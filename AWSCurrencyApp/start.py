#!/usr/bin/env python

from currency_app import QueueProcessor

def start():
     my_queue = QueueProcessor(
     "https://sqs.us-east-1.amazonaws.com/117670899390/SQSQueue", "inputbucketforqueue"
 ).start()

start()