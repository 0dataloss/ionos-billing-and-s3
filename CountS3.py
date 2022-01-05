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

# Read Env Variables
if os.getenv('IONOS_APIKEY'):
  if os.getenv('IONOS_APIKEYSECRET'):
    apiKeyi = os.getenv('IONOS_APIKEY')
    apiSecretKeyi = os.getenv('IONOS_APIKEYSECRET')
else:
  if os.path.exists("ionos.py"):
    # File Exist so  Import .ionos.cfg
    sys.path.append("ionos")
    import ionos as i
    apiKeyi=i.apikey
    apiSecretKeyi=i.apisecretkey
  else:
    print(f"You can create a configuration file in your home directory\n"
    f"This will make easy to run the script.\n"
    f"Create the file ionos.py in this same directory with content:\n\n")

# check if Key and secret Key have values
try:
    apiKeyi
except:
    print("API Key missing, please export it in your env with 'export IONOS_APIKEY=<apikey>'"\n
    "Or set up the file ionos.py")
try:
    apiSecretKeyi
except:
    print("API Key missing, please export it in your env with 'export IONOS_APIKEYSECRET=<apiSecretKeyi>'"\n
    "Or set up the file ionos.py")

##
# Create S3 Objects
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
