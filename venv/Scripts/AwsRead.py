import boto3
import json
from boto3.dynamodb.conditions import Key



class AwsRead:
    table = ""


    def __init__(self, table):
        self.table = table


    def getUserTables(self):
        dynamodb_client = boto3.resource('dynamodb', region_name='us-west-2')
        table = dynamodb_client.Table(self.table)
        response = table.scan()
        return response['Items']

    def getUser_oneDriveRecords(self):
        dynamodb_client = boto3.resource('dynamodb', region_name='us-west-2')
        table = dynamodb_client.Table(self.table)
        response = table.scan()
        time = response['Items'][0]
        canData = response['Items'][1]
        GPSData = response['Items'][2]
        gyroData = response['Items'][3]
        return time,canData,GPSData,gyroData