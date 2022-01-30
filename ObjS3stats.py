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
containerIo = os.getenv('IONOS_CONTAINER')
# Prices per GB tiers Less or equal 50, between 50 and 500, and over 500 TB
s3le50TB=0.015
s3le500TB=0.014
s3gt500TB=0.013

# Pre-Calculate Prices
tb50Price=50000*s3le50TB
tb450Price=450000*s3le500TB

# Check Env Var do exist
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
def stats(apiKeyi,apiSecretKeyi,runOption):
# Vars Init
  prometheusStats = ""
  totalSizeGB = 0
  totalPrice=0
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
  buckets = s3client.list_buckets()
  if runOption == "TOTAL":
    print(f"# Bucket Details\n#--------------------")
  elif runOption == "CSV":
    print(f"Bucket_Name,Size_in_GB,Number_Of_Files,Price at 30 Days")
  for bucket in buckets['Buckets']:
    s3sizeByte=0
    bucketSize=0
    bucket42 = s3resource.Bucket(bucket['Name'])
    urlBucket = "https://"+ bucket['Name'] + ".s3-de-central.profitbricks.com"
    resUrlBucket = requests.get(urlBucket, allow_redirects=False)
# At today the redirect is broken so this is necessary to avoid loops
# and to do not break away from https I am parsing the response and rebuild the Endpoint
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

# Count the files (may take a while)  
    c0 = 0
    for s3_file in bucket42.objects.all():
       s3sizeByte = s3sizeByte + s3_file.size
       c0 = c0 + 1

# Calculate the tiers and the money    
    bucketSize = s3sizeByte / 1024 / 1024 / 1024
    if bucketSize <= 50000 :
      bucketPrice = bucketSize * s3le50TB
    elif bucketSize <= 500000 :
      over50TB = bucketSize - 50000
      bucketPrice=over50TB*s3le500TB
      bucketPrice=bucketPrice+tb50Price
    elif bucketSize >= 500000 :
      over500TB = bucketSize - 500000
      bucketPrice=over500TB*s3gt500TB
      bucketPrice=bucketPrice+tb50Price+tb450Price

    if runOption == "TOTAL":
      print(f"Size of {bucket42.name}: {bucketSize} GB\nFiles contained in {bucket42.name}:{c0}\nForecasted Price in 30 Days {bucket42.name}:{bucketPrice}\n#--------------------")
    elif runOption == "CSV":
      print(f"{bucket42.name},{bucketSize},{c0},{bucketPrice}")
    elif runOption == "PROMETHEUS":
      s3PrometheusSize="Size{BucketName="+ bucket42.name + "}" + str(bucketSize)
      s3PrometheusFiles="Files{BucketName="+ bucket42.name + "}" + str(c0)
      s3PrometheusPrice="Price{BucketName="+ bucket42.name + "}" + str(bucketPrice)
      prometheusStats = prometheusStats +"\n"+  str(s3PrometheusFiles) +"\n"+ str(s3PrometheusSize)+"\n"+ str(s3PrometheusPrice)
    totalSizeGB = (totalSizeGB + bucketSize)
    totalPrice = (totalPrice + bucketPrice)
  
  if runOption == "TOTAL":
    totalSizeGB=str(totalSizeGB)
    totalPrice=str(totalPrice)
    print(f"Total Size: {totalSizeGB} GB\nTotal Price Forecast at 30 Days: {totalPrice}")
  elif runOption == "PROMETHEUS":
    return prometheusStats

# It is just temporary till I sort out the 3 endpoints
if containerIo == "YES":
  runOption="PROMETHEUS"
try:
  runOption
  if runOption == "PROMETHEUS":
    @app.route('/metrics')
    def test():
      return(stats(apiKeyi,apiSecretKeyi,runOption))

    if __name__ == '__main__':
      if containerIo == "YES":
        app.run(host="0.0.0.0")
      else:
        app.run()
  elif runOption == "CSV":
    stats(apiKeyi,apiSecretKeyi,runOption)
  elif runOption == "TOTAL":
    stats(apiKeyi,apiSecretKeyi,runOption)
  else:
    print(f"ERROR!!\nPlease set IONOS_RUNTYPE as env variable with value CSV or TOTAL or PROMETHEUS")
    sys.exit(1)
except:
    print(f"IONOS_RUNTYPE env variable not set!\nPlease set IONOS_RUNTYPE as env variable with value CSV or TOTAL or PROMETHEUS")