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

ionos_access_key_id = ""
ionos_secret_access_key = ""
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
    print(f"No credentials found...\n"
    f"Before running the program export as environment variables IONOS_APIKEY=<your api key> and\n"
    f"IONOS_APIKEYSECRET=<your api secret key\n"
    f"Or, create the file ionos.py in this same directory with content:\n\n"
    f"apikey=<your api key>"
    f"apisecretkey=<your api secret key>")
    sys.exit(1)

##
# Create S3 Objects
##
s3client = boto3.client('s3',
    ionos_access_key_id=apiKeyi,
    ionos_secret_access_key=apiSecretKeyi,
    endpoint_url='https://s3-de-central.profitbricks.com'
)
s3resource = boto3.resource('s3',
    ionos_access_key_id=apiKeyi,
    ionos_secret_access_key=apiSecretKeyi,
    endpoint_url='https://s3-de-central.profitbricks.com'
)
totalSizeByte = 0
buckets = s3client.list_buckets()
print(f"# Bucket Details\n#--------------------")
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
      ionos_access_key_id=apiKeyi,
      ionos_secret_access_key=apiSecretKeyi,
      endpoint_url="https://"+ secondlevel
    )
    bucket42 = s3resource.Bucket(bucket['Name'])
  else:
    s3resource = boto3.resource('s3',
      ionos_access_key_id=apiKeyi,
      ionos_secret_access_key=apiSecretKeyi,
      endpoint_url='https://s3-de-central.profitbricks.com'
    )
    bucket42 = s3resource.Bucket(bucket['Name'])
  c0 = 0
  for s3_file in bucket42.objects.all():
     s3sizeByte = s3sizeByte + s3_file.size
     c0 = c0 + 1
  bucketSize = s3sizeByte / 1024 / 1024 / 1024
  print(f"Size of {bucket42.name}: {bucketSize} GB\nFiles contained in {bucket42.name}:{c0}\n#--------------------")

  totalSizeByte = (totalSizeByte + s3sizeByte)
  s3sizeByte = s3sizeByte / 1024 / 1024 / 1024
totalSizeByte=totalSizeByte/1024/1024/1024
print(f"Total Size:{totalSizeByte} GB")
