import boto3
import json

def get_temporary_credentials(user_arn):
    sts = boto3.client('sts', region_name='us-east-1')  # Asegúrate de incluir region_name aquí
    response = sts.assume_role(
        RoleArn=user_arn,
        RoleSessionName='UserSession',
        DurationSeconds=3600  # Credenciales válidas por 1 hora
    )
    return response['Credentials']

def create_lambda_client(credentials):
    lambda_client = boto3.client(
        'lambda',
        region_name='us-east-1',  # Asegúrate de usar la región correcta donde está desplegada tu función Lambda
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken']
    )
    return lambda_client
    
def invoke_lambda_function(lambda_client, function_name, payload):
    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType='RequestResponse',  # Puedes usar 'Event' para una invocación asíncrona
        Payload=json.dumps(payload)
    )
    return response
