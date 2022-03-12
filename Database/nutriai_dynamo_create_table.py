
import boto3
import logging
import time
from botocore.exceptions import ClientError
from aws_def_values_test import *



def get_dynamodb(access:dict):
    dynamodb = boto3.client(
        'dynamodb',
        region_name=access['region_ap'],
        aws_access_key_id=access['aws_access_key_id'],
        aws_secret_access_key=access['aws_secret_access_key']
    )
    print('get DynamoDB')
    return dynamodb


# Retrieve the list of existing tables
def tables_list(client):
    try:
        response = client.list_tables()
        print('Existing tables:')
        for bucket in response['TableNames']:
            print(f'  {bucket}')
    except ClientError as e:
        logging.error(e)


# create table for NutriAI project
def set_table(client, table_name:str):
    try:
        table = client.create_table(
            TableName = table_name,
            # HASH : PK, RANGE : SK
            KeySchema=[
                {
                    'AttributeName' : 'PK',
                    'KeyType' : 'HASH'
                },
                {
                    'AttributeName' : 'SK',
                    'KeyType' : 'RANGE'
                }
            ],
            # attr. def.
            AttributeDefinitions=[
                {
                    'AttributeName' : 'PK',
                    'AttributeType' : 'S'
                },
                {
                    'AttributeName' : 'SK',
                    'AttributeType' : 'S'
                },
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 10,
                'WriteCapacityUnits': 10
            }
        )
        time.sleep(3)
        print('set DynamoDB Table')
    except ClientError as e:
        logging.error(e)
        tables_list(client)
        return False
    return True




# main
if __name__=='__main__':
    dynamodb_clt = get_dynamodb(aws_access)
    set_table(dynamodb_clt, table_nutriai)
    tables_list(dynamodb_clt)
