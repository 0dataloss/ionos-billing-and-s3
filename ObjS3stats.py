#!/bin/python3
import sys
import requests
import os
import boto3
from flask import Flask
from botocore.client import Config

config = Config(connect_timeout=1, read_timeout=1, retries={'max_attempts': 0})
s3 = boto3.client('s3', config=config)
runOption = os.getenv('IONOS_RUNTYPE')
apiKeyi = os.getenv('IONOS_APIKEY')
apiSecretKeyi = os.getenv('IONOS_APIKEYSECRET')

try:
  runOption
except:
  print(f"Please make sure IONOS_RUNTYPE is an Environment Variable")
  sys.exit(1)
try:
  apiKeyi
except:
  print(f"Please make sure IONOS_APIKEY is an Environment Variable")
  sys.exit(1)
try:
  apiSecretKeyi
except:
  print(f"Please make sure IONOS_APIKEYSECRET is an Environment Variable")
  sys.exit(1)

app = Flask(__name__)

def stats():
  aws_access_key_id = ""
  aws_secret_access_key = ""
  prometheusStats = ""

  # Read Env Variables
  apiKeyi = os.getenv('IONOS_APIKEY')
  apiSecretKeyi = os.getenv('IONOS_APIKEYSECRET')
  runOption = os.getenv('IONOS_RUNTYPE')
  
  try:
    runOption
  except:
    runOption="TOTAL"
  
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
  if runOption == "TOTAL":
    print(f"# Bucket Details\n#--------------------")
  elif runOption == "CSV":
    print(f"Bucket_Name,Size_in_GB,Number_Of_Files")
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
  
    c0 = 0
    for s3_file in bucket42.objects.all():
       s3sizeByte = s3sizeByte + s3_file.size
       c0 = c0 + 1
  
    bucketSize = s3sizeByte / 1024 / 1024 / 1024
    if runOption == "TOTAL":
      print(f"Size of {bucket42.name}: {bucketSize} GB\nFiles contained in {bucket42.name}:{c0}\n#--------------------")
    elif runOption == "CSV":
      print(f"{bucket42.name},{bucketSize},{c0}")
    elif runOption == "PROMETHEUS":
      s3PrometheusSize="Size{BucketName="+ bucket42.name + "}" + str(bucketSize)
      s3PrometheusFiles="Files{BucketName="+ bucket42.name + "}" + str(c0)
      prometheusStats = prometheusStats +"\n"+  str(s3PrometheusFiles) +"\n"+ str(s3PrometheusSize)
    totalSizeByte = (totalSizeByte + s3sizeByte)
    s3sizeByte = s3sizeByte / 1024 / 1024 / 1024
  
  if runOption == "TOTAL":
    totalSizeByte=totalSizeByte/1024/1024/1024
    print(f"Total Size:{totalSizeByte} GB")
  elif runOption == "PROMETHEUS":
    return prometheusStats

try:
  runOption
  if runOption == "PROMETHEUS":
    @app.route('/metrics')
    def test():
      return(stats())

    if __name__ == '__main__':
      app.run()
  elif runOption == "CSV":
    stats()
  elif runOption == "TOTAL":
    stats()
  else:
    print(f"ERROR!!\nPlease set IONOS_RUNTYPE as env variable with value CSV or TOTAL or PROMETHEUS")
except:
    print(f"IONOS_RUNTYPE env variable not set!\nPlease set IONOS_RUNTYPE as env variable with value CSV or TOTAL or PROMETHEUS")