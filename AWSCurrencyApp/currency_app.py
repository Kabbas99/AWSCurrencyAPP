#!/usr/bin/env python

import csv
import io
import boto3
import json
import botocore
from currency_converter import CurrencyConverter
import time

c = CurrencyConverter()
seconds = time.time()
sqs = boto3.client('sqs', region_name='us-east-1')
s3 = boto3.client('s3', region_name='us-east-1')

queue_url = "https://sqs.us-east-1.amazonaws.com/117670899390/SQSQueue"

receipt_handle = None
key_name = None
csv_string = None

def receive_message():
    try:
        response = sqs.receive_message(
            QueueUrl=queue_url,
            AttributeNames=[
                'SentTimestamp'
            ],
            MaxNumberOfMessages=1,
            MessageAttributeNames=[
                'All'
            ],
            VisibilityTimeout=0,
            WaitTimeSeconds=20
        )
        global receipt_handle
        receipt_handle = response["Messages"][0]["ReceiptHandle"]
    except KeyError:    
        raise
    else:
        print(receipt_handle)
        body = response["Messages"][0]["Body"]
        json_body = json.loads(body)
        global key_name
        key_name = json_body["Records"][0]["s3"]["object"]["key"]
        print(key_name)

def get_file():
    file_data = s3.get_object(Bucket="inputbucketforqueue", Key=key_name)
    global csv_string
    csv_string = file_data['Body'].read().decode('utf-8')
    reader = csv.DictReader(io.StringIO(csv_string))
    for row in reader:
        print(row)
    print(" ")

def convert_currencies():
    reader = csv.DictReader(io.StringIO(csv_string))
    data = list(reader)
    for index, row in enumerate(data):
        if row["Currency"] != 'GBP':
            data[index]["Price"] = round(c.convert(float(row["Price"]), 'GBP'), 2)
    print(data)
    json_file = json.dumps(data, indent=4, sort_keys=True)
    print(json_file)
    file_key = "CSV" + str(seconds) + ".csv"
    print(file_key)
    s3.put_object(Body=json_file, Bucket="outputbuckerforec2", Key=file_key)        

def delete_message():
    response = sqs.delete_message(
        QueueUrl=queue_url,
        ReceiptHandle=receipt_handle
    )
    print("Deleted " + receipt_handle)

def delete_file():
    response = s3.delete_object(
        Bucket="inputbucketforqueue",
        Key=key_name
    )
    print("Deleted " + key_name)

while True:
    try:
        receive_message()
        delete_message()
        get_file()
        convert_currencies() 
        delete_file()
    except KeyError:
        print("No messages available. Trying again in 60 secs.")
        time.sleep(60)
