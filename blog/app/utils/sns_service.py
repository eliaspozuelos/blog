import boto3
from flask import current_app

def get_sns_client():
    return boto3.client('sns', region_name=current_app.config['SNS_REGION'])

def publish_to_sns(message, subject=None, topic_arn=None):
    sns_client = get_sns_client()
    topic_arn = topic_arn or current_app.config['SNS_DEFAULT_TOPIC_ARN']
    response = sns_client.publish(
        TopicArn=topic_arn,
        Message=message,
        Subject=subject
    )
    return response
