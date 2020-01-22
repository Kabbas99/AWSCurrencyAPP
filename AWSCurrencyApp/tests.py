import pytest
import mock
from moto import mock_s3
import boto3
from currency_app import QueueProcessor


@mock_s3
def test_get_file():
    conn = boto3.resource('s3', region_name='us-east-1')
    conn.create_bucket(Bucket='bucket')
    conn.Bucket("bucket").put_object(Key="CSV", Body="100A" )

    queue_processor = QueueProcessor("https://sqs.us-east-1.amazonaws.com/117670899390/SQSQueue", "inputbucketforqueue")

    file_body = queue_processor.get_file("CSV")

    assert file_body == "100A"