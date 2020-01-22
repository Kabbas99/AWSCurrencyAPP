#!/usr/bin/env python

import csv
import io
import boto3
import json
import botocore
from currency_converter import CurrencyConverter
import time


class QueueProcessor:
    sqs = sqs = boto3.client("sqs", region_name="us-east-1")
    s3 = boto3.client("s3", region_name="us-east-1")
    c = CurrencyConverter()
    seconds = time.time()

    def __init__(self, queue_url, bucket_name):
        self.queue_url = queue_url
        self.bucket_name = bucket_name

    # Polls the SQS queue and gets information from the message such as the receipt handle and the body, to then get the name of the file
    def receive_message(self):
        receipt_handle = None
        key_name = None
        try:
            response = self.sqs.receive_message(
                QueueUrl=self.queue_url,
                AttributeNames=["SentTimestamp"],
                MaxNumberOfMessages=1,
                MessageAttributeNames=["All"],
                VisibilityTimeout=0,
                WaitTimeSeconds=20,
            )
            receipt_handle = response["Messages"][0]["ReceiptHandle"]
        except KeyError:
            raise
        else:
            print("Reading " + receipt_handle)
            body = response["Messages"][0]["Body"]
            json_body = json.loads(body)
            key_name = json_body["Records"][0]["s3"]["object"]["key"]
            print("Reading " + key_name)
            return receipt_handle, key_name

    # Uses the key from receive_message() to access the inside of the .csv file
    def get_file(self, key_name):
        file_data = self.s3.get_object(Bucket="inputbucketforqueue", Key=key_name)
        csv_string = file_data["Body"].read().decode("utf-8")
        reader = csv.DictReader(io.StringIO(csv_string))
        for row in reader:
            print(row)
        print(" ")
        return csv_string

    # Searches through the file to identify which rows are no GBP, and then converts the price of that row into GBP
    def convert_currencies(self, csv_string):
        reader = csv.DictReader(io.StringIO(csv_string))
        data = list(reader)
        for index, row in enumerate(data):
            if row["Currency"] != "GBP":
                data[index]["Price"] = round(
                    self.c.convert(float(row["Price"]), "GBP"), 2
                )
        json_file = json.dumps(data, indent=4, sort_keys=True)
        print(json_file)
        file_key = "CSV" + str(self.seconds) + ".csv"
        print("New filename: " + file_key)
        self.s3.put_object(Body=json_file, Bucket="outputbuckerforec2", Key=file_key)

    # Using the receipt _handle from receive_message() to delete the message from the SQS queue
    def delete_message(self, receipt_handle):
        response = self.sqs.delete_message(
            QueueUrl=self.queue_url, ReceiptHandle=receipt_handle
        )
        print("Deleted " + receipt_handle)

    # Using the key from receive_message() this method deletes the .csv file from the s3 bucket
    def delete_file(self, key_name):
        response = self.s3.delete_object(Bucket="inputbucketforqueue", Key=key_name)
        print("Deleted " + key_name)

    # This is the main method where the previous methods are called in a certain order, also within a while loop, ensuring the SQS queue is checked every 60 seconds to confirm there is a message in there
    def start(self):
        while True:
            try:
                handler, key = self.receive_message()
                self.delete_message(handler)
                csv = self.get_file(key)
                self.convert_currencies(csv)
                self.delete_file(key)
            except KeyError:
                print("No messages available. Trying again in 60 secs.")
                time.sleep(60)
