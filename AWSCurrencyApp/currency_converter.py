#!/usr/bin/env python

import csv
import io
import boto3
import json
import botocore
#import currency_converter

sqs = boto3.client('sqs', region_name='us-east-1')
s3 = boto3.client('s3', region_name='us-east-1')

queue_url = "https://sqs.us-east-1.amazonaws.com/117670899390/SQSQueue"

key_name = None

def receive_message():
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
    body = response["Messages"][0]["Body"]
    json_body = json.loads(body)
    global key_name
    key_name = json_body["Records"][0]["s3"]["object"]["key"]
    print(key_name)

receive_message()

def get_file():
    file_data = s3.get_object(Bucket="inputbucketforqueue", Key=key_name)
    csv_string = file_data['Body'].read().decode('utf-8')
    reader = csv.DictReader(io.StringIO(csv_string))
    for row in reader:
        print(row)

get_file()

#def convert_currencies():
