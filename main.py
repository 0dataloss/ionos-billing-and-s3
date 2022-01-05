#!/bin/python3
import socket
import sys
import requests
import json
import datetime
import base64
import os
from flask import Flask
from botocore.client import Config
from getpass import getpass


app = Flask(__name__)

@app.route('/')
def stats():
  cSvPrintadd = ""
  prometheusPagePrintadd = ""

  # Read Env Variables
  if os.getenv('IONOS_USERNAME'):
    if os.getenv('IONOS_PASSWORD'):
      yAndM = datetime.datetime.now().strftime('%Y-%m')
      usernameio = os.getenv('IONOS_USERNAME')
      passwordio = os.getenv('IONOS_PASSWORD')
      contractio = os.getenv('IONOS_CONTRACT')
      apiKeyi = os.getenv('IONOS_APIKEY')
      periodio = os.getenv('IONOS_PERIOD')
      apiSecretKeyi = os.getenv('IONOS_APIKEYSECRET')
  else:
    if os.path.exists("ionos.py"):
      # File Exist so  Import .ionos.cfg
      sys.path.append("ionos")
      import ionos as i
      usernameio=i.username
      contractio=i.contract
      apiKeyi=i.apikey
      apiSecretKeyi=i.apisecretkey
      periodio=i.period
      passwordio=i.password
    else:
      print("You can create a configuration file in your home directory\n"
      "This will make easy to run the script.\n"
      "Create the file ionos.py in this same directory with content:\n\n"
      "username=\"<replace with your username>\"\n"
      "contract=\"<replace with your contract number>\"\n\n")

  # If there is no file or no variables I am requesting User Inputs
  try:
      usernameio
      user_input_username = usernameio
  except:
    user_input_username = input("Please insert username\n")
  try:
      isinstance
      contract = contractio
  except:
    user_input_contract = input("Please insert contract number\n")
    contract = user_input_contract
  try:
      periodio
      period = periodio
  except:
      periodio = yAndM
  try:
      isinstance
      user_input_password=passwordio
  except:
    user_input_password=getpass()

  # End User Input

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
          cSvPrint=dcName,dc,price['meterDesc'],price['meterId'],price['unitCost']['quantity'],price['unitCost']['unit'],quantitybUnit,spending,price['unitCost']['unit']
          cSvPrint=str(cSvPrint)
          cSvPrintadd= cSvPrintadd +"\n"+ cSvPrint.strip("[()]")
          descriptionSanit=price['meterDesc'].strip(")").strip("(")
          prometheusPagePrint=dcName.replace(" ","_") + "{" + "DCName="+ dcName + ",DCUUID=" + dc + ",Description=" + descriptionSanit.replace(" ","_").replace("+","").replace("(","").replace(")","")+ ",MeterID=" + price['meterId'] +",Quantity=" + str(quantitybUnit) + ",Price=" +str(spending)+"}"
          prometheusPagePrintadd=prometheusPagePrintadd +"\n"+ prometheusPagePrint

  # If CSV requested print CSV
  ###print(cSvPrintadd)
  # If GranTotal requested print GranTotal
  ###print("\n\n--------\nGrand Total Compute & Network --> "+ str(grandTotal) +"\n--------")
  # If Prometheus requested print prometheusPage
  return prometheusPagePrintadd



if __name__ == '__main__':
    app.run()
