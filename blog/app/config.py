import os
import boto3

boto3.setup_default_session(region_name='us-east-1')

class Config:
    # Configuración de SNS
    SNS_REGION = 'us-east-1'  # Región de SNS
    SNS_DEFAULT_TOPIC_ARN = 'arn:aws:sns:us-east-1:010526258375:blog-updates'  # ARN del tópico predeterminado
                            
    #SECRET_KEY = os.getenv('SECRET_KEY', 'your_secret_key')
    S3_BUCKET = 'blog-imagenes-users'
    S3_BUCKET_2 ='blog-imagenes-users-resized'
    S3_REGION = 'us-east-1'

    SECRET_KEY = 'produc5000'  # Clave secreta básica para desarrollo
    
    # Configuración de RDS
    RDS_DB_NAME = "blog_personal"
    RDS_HOSTNAME = 'db-blog.clk8is2ku4cp.us-east-1.rds.amazonaws.com'
    RDS_USERNAME = 'admin'
    RDS_PASSWORD = 'admin123**'

    DYNAMODB_TABLE_NAME = 'user_activity'  
    REGION_NAME = 'us-east-1' 
    
    SQS_QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/010526258375/cola_blog_updates"
    AWS_REGION = "us-east-1"
  # Configuración de SQLAlchemy
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{RDS_USERNAME}:{RDS_PASSWORD}@{RDS_HOSTNAME}/{RDS_DB_NAME}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False


    
    
def get_dynamodb_table():
    dynamodb = boto3.resource('dynamodb', region_name=Config.REGION_NAME)
    return dynamodb.Table(Config.DYNAMODB_TABLE_NAME)