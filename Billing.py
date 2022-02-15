#!/bin/python3
import sys
import requests
import datetime
import base64
import os
from flask import Flask
from getpass import getpass

usernameio = os.getenv('IONOS_USERNAME')
try:
  usernameio.isascii
except:
  print("Missing Username -> IONOS_USERNAME\n")
  sys.exit(1)
passwordio = os.getenv('IONOS_PASSWORD')
try:
  passwordio.isascii
except:
  print("Missing Password -> IONOS_PASSWORD\n")
  sys.exit(1)
contractio = os.getenv('IONOS_CONTRACT')
try:
  contractio.isascii
except:
  print("Missing Contract Number -> IONOS_CONTRACT\n")
  sys.exit(1)
runOption = os.getenv('IONOS_RUNTYPE')
containerIo = os.getenv('IONOS_CONTAINER')
runOption = os.getenv('IONOS_RUNTYPE')
yAndM = datetime.datetime.now().strftime('%Y-%m')
app = Flask(__name__)

def stats(usernameio,passwordio,contractio,runOption):
  user_input_username = usernameio
  user_input_password=passwordio
  contract = str(contractio)
  cSvPrintadd = ""
  prometheusPagePrintadd="# This script is interrogating IONOS Billing API\n# Each metric is a Price tagged with all the most relevant information"
  yAndM = datetime.datetime.now().strftime('%Y-%m')
  # Period is always the current Billing Month
  period = str(yAndM)

  # Prepare base46 username:password Headers
  user_input_usernameandpassword=str(user_input_username+":"+user_input_password)
  message_bytes = user_input_usernameandpassword.encode('ascii')
  base64_bytes = base64.b64encode(message_bytes)
  token = base64_bytes.decode('ascii')
  contract=contract
  authAcc={"Authorization": "Basic "+token+""}


  # Buld a catalog for all the products with ID, the price per unit, and the unit
  def catalog(authHead,contract):
    url = "https://api.ionos.com/billing/"+ contract +"/products"
    response = requests.get(url, headers=authHead)
    catalogRp = (response.json())
    # only return the products with deprected = False
    catalogRpOnlyFalse = []
    catalogProducts = catalogRp['products']
    # Build a new list of Dict from previous Dict for only services Not Deprecated
    for item in catalogProducts:
      if item['deprecated'] is False:
        catalogRpOnlyFalse.append(item)
    return catalogRpOnlyFalse

  # Build a List of product which have been used per DC
  def usage(authHead,contract,period):
    url = "https://api.ionos.com/billing/"+ contract +"/utilization/"+ period +"?"
    response = requests.get(url, headers=authHead)
    usageRp = (response.json())
    usageRp = usageRp['datacenters']
    return usageRp

  # Start Building the Catalog
  catalogNotDeprecated=catalog(authAcc,contract)

  # Start the creation of a list of services used by the contract per DC
  usageresp=usage(authAcc,contract,period)

  # Looping through the Catalog to exrapolate the product, the cost and do the maths
  i=0
  grandTotal = 0
  s3DcUuid=0
  while i < len(usageresp):
    vdc=usageresp[i]
    i = i + 1
    dc=vdc['id']
    dcName=vdc['name']
    if dcName == "S3":
        s3DcUuid=dc
    for a in vdc['meters']:
      meterIdb=a['meterId']
      typeObj=str(a['type'])
      resourceUUID=str(a['resourceId'])
      if resourceUUID == "None":
          resourceUUID=str(a['id'])
      serverName=a['name']
      quantityb=a['quantity']
      quantitybUnit=a['quantity']['quantity']
      for price in catalogNotDeprecated:
        if price['meterId'] == meterIdb:
          unitCost=float(price['unitCost']['quantity'])
          consumedUnit=float(quantitybUnit)
          spending=(consumedUnit*unitCost)
          grandTotal=(grandTotal+spending)
          if dcName == '':
              dcName="Control_Plane"
          x=len(serverName)
          if x != 0:
            cSvPrint=dcName,dc,typeObj,resourceUUID,price['meterDesc'],price['meterId'],price['unitCost']['quantity'],price['unitCost']['unit'],quantitybUnit,spending,price['unitCost']['unit'],serverName
          else:
            cSvPrint=dcName,dc,typeObj,resourceUUID,price['meterDesc'],price['meterId'],price['unitCost']['quantity'],price['unitCost']['unit'],quantitybUnit,spending,price['unitCost']['unit']
          cSvPrint=str(cSvPrint)
          cSvPrintadd= cSvPrintadd +"\n"+ cSvPrint.strip("[()]").replace("'","").replace(", ",",")
          descriptionSanit=price['meterDesc'].strip(")").strip("(")
          if x != 0:
            prometheusPagePrint="Price{DCName=\""+ dcName.replace(" ","_") + "\",DCUUID=\"" + dc + "\",Type=\"" + typeObj + "\",ResourceUUID=\"" + resourceUUID + "\",ServerName=\"" + serverName + "\",Description=\"" + descriptionSanit.replace(" ","_").replace("+","").replace("(","").replace(")","") + "\",MeterID=\"" + price['meterId'] + "\",Quantity=\"" + str(quantitybUnit) + "\"}" + str(spending)
          else:
            prometheusPagePrint="Price{DCName=\""+ dcName.replace(" ","_") + "\",DCUUID=\"" + dc + "\",Type=\"" + typeObj + "\",ResourceUUID=\"" + resourceUUID + "\",Description=\"" + descriptionSanit.replace(" ","_").replace("+","").replace("(","").replace(")","") + "\",MeterID=\"" + price['meterId'] + "\",Quantity=\"" + str(quantitybUnit) + "\"}" + str(spending)

          prometheusPagePrintadd=prometheusPagePrintadd +"\n"+ prometheusPagePrint

  if runOption == "CSV":
    # If CSV requested print CSV
    print(f"{cSvPrintadd}")

  elif runOption == "TOTAL":
    # If GranTotal requested print GranTotal
    print(f"\n\n--------\nGrand Total Compute & Network :"+ str(grandTotal) +"\n--------")

  elif runOption == "PROMETHEUS":
    # If Prometheus is what is needed then start server and return results
    return prometheusPagePrintadd

# It is just temporary till I sort out the 3 endpoints
if containerIo == "YES":
  runOption="PROMETHEUS"
try:
  runOption
  if runOption == "PROMETHEUS":
    @app.route('/metrics')
    def test():
      return(stats(usernameio,passwordio,contractio,runOption))

    if __name__ == '__main__':
      if containerIo == "YES":
        app.run(host="0.0.0.0")
      else:
        app.run()
  elif runOption == "CSV":
    stats(usernameio,passwordio,contractio,runOption)
  elif runOption == "TOTAL":
    stats(usernameio,passwordio,contractio,runOption)
  else:
    print(f"ERROR!!\nPlease set IONOS_RUNTYPE as env variable with value CSV or TOTAL or PROMETHEUS")
    sys.exit(1)
except:
    print(runOption)
    print(f"IONOS_RUNTYPE env variable not set!\nPlease set IONOS_RUNTYPE as env variable with value CSV or TOTAL or PROMETHEUS")
    sys.exit(1)