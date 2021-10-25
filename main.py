#!/bin/python
import socket
import sys
import requests
import json
import datetime
import base64
import os
import boto3
from botocore.client import Config
from getpass import getpass

config = Config(connect_timeout=1, read_timeout=1, retries={'max_attempts': 0})
s3 = boto3.client('s3', config=config)

#i=""
#usernameio=1
#contractio=1
cSvPrintadd = ""

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
  print(f"You can create a configuration file in your home directory\n"
        f"This will make easy to run the script.\n"
        f"Create the file ionos.py in this same directory with content:\n\n"
        f"username=\"<replace with your username>\"\n"
        f"contract=\"<replace with your contract number>\"\n\n")

# If there is no file I am requesting User Inputs
if isinstance(usernameio,str):
  user_input_username = usernameio
else:
  user_input_username = input("Please insert username\n")
if isinstance(contractio,str):
  contract = contractio
else:
  user_input_contract = input("Please insert contract number\n")
  contract = user_input_contract

#user_input_period = input("Insert Period for billing, format YYYY-MM, press enter for current period\n")
#period = user_input_period
period=periodio
if isinstance(passwordio,str):
  user_input_password=passwordio
else:
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

### REPLACE USAGE WITH MORE GRANULARE UTILIZATION
## Build a List of product which have been used per DC
#def usage(authHead,contract,period):
#  url = "https://api.ionos.com/billing/"+ contract +"/usage?period="+ period
#  response = requests.get(url, headers=authHead)
#  usageRp = (response.json())
#  print(usageRp)
#  usageRp = usageRp['datacenters']
#  return usageRp

# Build a List of product which have been used per DC
def usage(authHead,contract,period):
  url = "https://api.ionos.com/billing/"+ contract +"/utilization?period="+ period
  response = requests.get(url, headers=authHead)
  usageRp = (response.json())
  usageRp = usageRp['datacenters']
  return usageRp

# Start Building the Catalog
catalogNotDeprecated=catalog(authAcc,contract)

# Make sure the period of the query is not null
if period is None:
  dateToday=datetime.datetime.now()
  year=str(dateToday.year)
  month=str(dateToday.month)
  period=str(year+"-"+month)
  print(period)

# Start the creation of a list of services used by the contract per DC
usageresp=usage(authAcc,contract,period)

# Debugging Print
#print(catalogNotDeprecated)
#print(usageresp)

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
#        print(f"\n\n----DC: {dcName}----\n"
#              f"----DC UUID: {dc}----\n"
#              f"Tag: {price['meterDesc']};\n"
#              f"Item: {price['meterId']};"
#              f"\nPrice per Unit: {price['unitCost']['quantity']} {price['unitCost']['unit']}\n"
#              f"Consumed Units: {quantitybUnit}\n"
#              f"Total Spending = {spending} {price['unitCost']['unit']}")
        grandTotal=(grandTotal+spending)
        if dcName == '':
            dcName="Control_Plane"
        cSvPrint=dcName,dc,price['meterDesc'],price['meterId'],price['unitCost']['quantity'],price['unitCost']['unit'],quantitybUnit,spending,price['unitCost']['unit']
        cSvPrint=str(cSvPrint)
        cSvPrintadd= cSvPrintadd +"\n"+ cSvPrint.strip("[()]")

##
# add S3 to the party
##
s3client = boto3.client('s3',
    aws_access_key_id=apiKeyi,
    aws_secret_access_key=apiSecretKeyi,
    endpoint_url='https://s3-de-central.profitbricks.com'
)
s3resource = boto3.resource('s3',
    aws_access_key_id=apiKeyi,
    aws_secret_access_key=apiSecretKeyi,
    endpoint_url='https://s3-de-central.profitbricks.com'
)
totalSizeByte = 0
buckets = s3client.list_buckets()
for bucket in buckets['Buckets']:
  s3sizeByte=0
  bucket42 = s3resource.Bucket(bucket['Name'])
  urlBucket = "https://"+ bucket['Name'] + ".s3-de-central.profitbricks.com"
  resUrlBucket = requests.get(urlBucket, allow_redirects=False)
  if resUrlBucket.is_redirect is True:
    nospliturl=(resUrlBucket.headers['Location'])
    nocol=nospliturl.split(":")
    realurl=nocol[1].split(".", 1)
    secondlevel=realurl[1]
    endpointurl="https://"+ secondlevel
    s3resource = boto3.resource('s3',
      aws_access_key_id=apiKeyi,
      aws_secret_access_key=apiSecretKeyi,
      endpoint_url="https://"+ secondlevel
    )
    bucket42 = s3resource.Bucket(bucket['Name'])
  else:
    s3resource = boto3.resource('s3',
      aws_access_key_id=apiKeyi,
      aws_secret_access_key=apiSecretKeyi,
      endpoint_url='https://s3-de-central.profitbricks.com'
    )
    bucket42 = s3resource.Bucket(bucket['Name'])
  for s3_file in bucket42.objects.all():
    s3sizeByte = s3sizeByte + s3_file.size
  totalSizeByte = (totalSizeByte + s3sizeByte)
  s3sizeByte = s3sizeByte / 1024 / 1024 / 1024
totalSizeByte=totalSizeByte/1024/1024/1024
productId = "S3SU1100"
for price in catalogNotDeprecated:
    if price['meterId'] == productId:
      unitCost=float(price['unitCost']['quantity'])
      consumedUnit=float(totalSizeByte)
      spending=(totalSizeByte*unitCost)

      cSvPrint="S3",s3DcUuid,price['meterDesc'],price['meterId'],price['unitCost']['quantity'],price['unitCost']['unit'],totalSizeByte,spending,price['unitCost']['unit']
      cSvPrint = str(cSvPrint)
      cSvPrintadd = cSvPrint.strip("[()]")+cSvPrintadd
print(cSvPrintadd)
print(f"\n\n--------\nGrand Total Compute & Network --> {grandTotal}\n--------")
