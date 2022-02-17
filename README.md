# IONOS Billing and S3 Tracker

Create your Billing and S3 stats with these 2 python scripts
- Billing.py
- ObjS3stats.py

Stats can be generated in CSV format, PROMETHEUS (including a basic http metric page), or simply a string with the totals

## Table of Contents

- [Description](#description)
- [Installation](#installation)
- [Test your setup](#test-your-setup)
- [Prometheus Tags](#prometheus-tags)

## Description

Billing.py is a Python3 program which can be run on any linux environment.
It is designed primarily to export metrics for Prometheus but CSV format and a 1 line string with the total are also options for the output.
Will track all your resources as the billing system of IONOS does, tagging every signle price wit a variety of information which are going to 
help you design really granular graphs with Grafana.

As IONOS Billing api does not track S3 in real time, I have put together ObjS3stats.py which is still written in Python3 and will track the number
of files per container and the total amount of GB used at the time you are running the script.
ObjS3stats.py is also able to track the containers across multiple regions using the response headers from the Object Storage server response to
track the location of a Object Storage container dynamically.

## Installation

No special install procedure is required, just download the scripts and execute them.
Both script have been tested with with Python 3.8
ObjS3stats.py has been tested up to 2500 files for single container.

## Configuration

To use the scrips is necessary to pass information like username/password and contract number.
To do that securely we recommend to create a protected file named 'ionos.py' in the same directory as teh script with the content as follow:
```
runtype="CSV"    # Acceptable paramenters: TOTAL, CSV, PROMETHEUS
# Billing Config
username="Your@user.name"
contract="Contract Number"
password="Your Password"
period="2022-02" # This can be left blank for 'Latest'

# Object Storage Config
apiKeyi="Object Storage API KEY"
apiSecretKeyi="Object Storage Secret Key"
```

A second method is to export your IONOS credential for the admin user, as environment variables:
For Billing.py
```
export IONOS_USERNAME="username" && export IONOS_PASSWORD="password" && export IONOS_CONTRACT=contract_number && export IONOS_PERIOD="YYYY-MM" && export IONOS_RUNTYPE=[TOTAL, CSV, PROMETHEUS]
```
For ObjS3stats.py
```
export IONOS_APIKEY=<api key> && export IONOS_APIKEYSECRET=<api secret> && export IONOS_RUNTYPE=[TOTAL, CSV, PROMETHEUS]
```
or

If none of the two options above have been set-up:
- ObjS3stats.py will fail with error (exit code 1)
- Billing.py will request user input

## Test your setup
Is it possible to run the script stand-alone against the IONOS API to verify if the username and password used
are working as expected in terms of accessing resources

Billing.py
```
$ export IONOS_USERNAME="username" && export IONOS_PASSWORD="password" && export IONOS_CONTRACT=contract_number && export IONOS_PERIOD="YYYY-MM" && export IONOS_RUNTYPE=TOTAL ; Billing.py

--------
Grand Total Compute & Network :74.82126276412268
--------

$ export IONOS_USERNAME="username" && export IONOS_PASSWORD="password" && export IONOS_CONTRACT=contract_number && export IONOS_PERIOD="YYYY-MM" && export IONOS_RUNTYPE=CSV ; Billing.py

[...]
Cloud_Control_Plane,662befd5-3063-4b38-be3d-21f4e9a981d3,TRAFFIC,67a1baf2-e9b2-4515-916f-4f3ca694e7d2,1GB traffic inbound,TI1000,0,GBP,0.0005506686866283417,0.0,GBP
Cloud_Control_Plane,662befd5-3063-4b38-be3d-21f4e9a981d3,TRAFFIC,0d653255-c450-406a-974f-e1a50809f401,1GB traffic outbound,TO1000,0,GBP,1.6265548765659332e-05,0.0,GBP
Cloud_Control_Plane,662befd5-3063-4b38-be3d-21f4e9a981d3,TRAFFIC,0d653255-c450-406a-974f-e1a50809f401,1GB traffic inbound,TI1000,0,GBP,0.003911620005965233,0.0,GBP
[...]

$ export IONOS_USERNAME="username" && export IONOS_PASSWORD="password" && export IONOS_CONTRACT=contract_number && export IONOS_PERIOD="YYYY-MM" && export IONOS_RUNTYPE=PROMETHEUS ; Billing.py
 * Serving Flask app 'Billing' (lazy loading)
 * Environment: production
   WARNING: This is a development server. Do not use it in a production deployment.
   Use a production WSGI server instead.
 * Debug mode: off
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
```
Then point your browser to http://127.0.0.1:5000/metrics
[...]
Price{DCName="Cloud_Control_Plane",DCUUID="662befd5-3063-4b38-be3d-21f4e9a981d3",Type="TRAFFIC",ResourceUUID="67a1baf2-e9b2-4515-916f-4f3ca694e7d2",Description="1GB_traffic_inbound",MeterID="TI1000",Quantity="0.0005506686866283417"}0.0 Price{DCName="Cloud_Control_Plane",DCUUID="662befd5-3063-4b38-be3d-21f4e9a981d3",Type="TRAFFIC",ResourceUUID="0d653255-c450-406a-974f-e1a50809f401",Description="1GB_traffic_outbound",MeterID="TO1000",Quantity="1.6265548765659332e-05"}0.0 Price{DCName="Cloud_Control_Plane",DCUUID="662befd5-3063-4b38-be3d-21f4e9a981d3",Type="TRAFFIC",ResourceUUID="0d653255-c450-406a-974f-e1a50809f401",Description="1GB_traffic_inbound",MeterID="TI1000",Quantity="0.003911620005965233"}0.0
[...]

ObjS3stats.py
```
$ export IONOS_APIKEY=<api key> && export IONOS_APIKEYSECRET=<api secret> && export IONOS_RUNTYPE=TOTAL ; ObjS3stats.py

# Bucket Details
#--------------------
Size of corposo: 12.86932373046875 GB
Files contained in corposo:2686
#--------------------
Size of corposoes: 4.53253173828125 GB
Files contained in corposoes:946
#--------------------
Total Size:17.40185546875 GB

$ export IONOS_APIKEY=<api key> && export IONOS_APIKEYSECRET=<api secret> && export IONOS_RUNTYPE=CSV ; ObjS3stats.py

[...]
Bucket_Name,Size_in_GB,Number_Of_Files
corposo,12.86932373046875,2686
corposoes,4.53253173828125,946
[...]

$ export IONOS_APIKEY=<api key> && export IONOS_APIKEYSECRET=<api secret> && export IONOS_RUNTYPE=PROMETHEUS ; ObjS3stats.py
 * Serving Flask app 'Billing' (lazy loading)
 * Environment: production
   WARNING: This is a development server. Do not use it in a production deployment.
   Use a production WSGI server instead.
 * Debug mode: off
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
```
Then point your browser to http://127.0.0.1:5000/metrics
[...]
Files{BucketName=corposo}2686
Size{BucketName=corposo}12.86932373046875
Files{BucketName=corposoes}946
Size{BucketName=corposoes}4.53253173828125
[...]


## Prometheus Tags
For Billing.py each price metric has always the following tags:
DCName="VDC Name",DCUUID="VDC UUID",Type="Resource Type",ResourceUUID="Resource UUID",Description="Description of the resource",MeterID="Resource ID",Quantity="Quantity used for this resource"

If Type=SERVER there is an additional field with name ServerName="Name of the compute resource"

For ObjS3stats.py each metric reports as tag the bucket name and there are 2 types of metrics:
- Size
Reports the used GB for a Bucket
- Files
Reports the number of files in a Bucket