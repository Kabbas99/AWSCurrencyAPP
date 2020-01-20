#!/usr/bin/env python

import csv
import io
import boto3
import json
import botocore
from currency_converter import CurrencyConverter
import time

class QueueProcessor:
    sqs = sqs = boto3.client('sqs', region_name='us-east-1')
    s3 = boto3.client('s3', region_name='us-east-1')
    c = CurrencyConverter()
    seconds = time.time()
    receipt_handle = None
    key_name = None
    csv_string = None

    def __init__(self, queue_url, bucket_name):
        self.queue_url = queue_url
        self.bucket_name = bucket_name

    def receive_message(self):
        try:
            response = self.sqs.receive_message(
                QueueUrl=self.queue_url,
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
            self.receipt_handle = response["Messages"][0]["ReceiptHandle"]
        except KeyError:    
            raise
        else:
            print("Reading " + self.receipt_handle)
            body = response["Messages"][0]["Body"]
            json_body = json.loads(body)
            self.key_name = json_body["Records"][0]["s3"]["object"]["key"]
            print("Reading " + self.key_name)

    def get_file(self):
        file_data = self.s3.get_object(Bucket="inputbucketforqueue", Key=self.key_name)
        self.csv_string = file_data['Body'].read().decode('utf-8')
        reader = csv.DictReader(io.StringIO(self.csv_string))
        for row in reader:
            print(row)
        print(" ")

    def convert_currencies(self):
        reader = csv.DictReader(io.StringIO(self.csv_string))
        data = list(reader)
        for index, row in enumerate(data):
            if row["Currency"] != 'GBP':
                data[index]["Price"] = round(self.c.convert(float(row["Price"]), 'GBP'), 2)
        json_file = json.dumps(data, indent=4, sort_keys=True)
        print(json_file)
        file_key = "CSV" + str(self.seconds) + ".csv"
        print("New filename: " + file_key)
        self.s3.put_object(Body=json_file, Bucket="outputbuckerforec2", Key=file_key)        

    def delete_message(self):
        response = self.sqs.delete_message(
            QueueUrl=self.queue_url,
            ReceiptHandle=self.receipt_handle
        )
        print("Deleted " + self.receipt_handle)

    def delete_file(self):
        response = self.s3.delete_object(
            Bucket="inputbucketforqueue",
            Key=self.key_name
        )
        print("Deleted " + self.key_name)

    def start(self):
        while True:
            try:
                self.receive_message()
                self.delete_message()
                self.get_file()
                self.convert_currencies() 
                self.delete_file()
            except KeyError:
                print("No messages available. Trying again in 60 secs.")
                time.sleep(60)

my_queue = QueueProcessor("https://sqs.us-east-1.amazonaws.com/117670899390/SQSQueue", "inputbucketforqueue").start()
