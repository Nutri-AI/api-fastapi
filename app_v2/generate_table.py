import boto3

def generate_table(dynamodb):
    # dynamodb= boto3.resource('dynamodb', 
    #                             #endpoint_url= 'http://localhost:8000',
    #                             region_name= 'ap',
    #                             aws_access_key_id= 'x',
    #                             aws_secret_access_key= 'x')


    dynamodb.create_table(
        TableName= '1.0.0',
        KeySchema= [
            {'AttributeName': 'PK', 'KeyType': 'HASH'},    
            {'AttributeName': 'SK', 'KeyType': 'RANGE'}    
        ],
        AttributeDefinitions= [
            {'AttributeName': 'PK', 'AttributeType': 'S'},
            {'AttributeName': 'SK', 'AttributeType': 'S'}
        ],
        ProvisionedThroughput= {'ReadCapacityUnits': 10, 'WriteCapacityUnits': 10}
    )
    print('Successfully created table')