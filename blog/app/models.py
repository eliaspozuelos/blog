from . import db,bcrypt
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy.sql import text
from .config import get_dynamodb_table 
import boto3 
from botocore.exceptions import ClientError
import json
import pytz

from .utils.temp_credenciales import get_temporary_credentials, create_lambda_client,invoke_lambda_function



class User(UserMixin, db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)  # Cambiado de id a user_id
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(10), nullable=False, default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    posts = db.relationship('Post', backref='author', lazy=True)
    role_arn = db.Column(db.String(255), nullable=True)  # Campo para el ARN del rol IAM
    def get_id(self):
        """Sobrescribe el método para que use `user_id` en lugar de `id`."""
        return str(self.user_id)

    def set_password(self, password):
        """Cifra la contraseña del usuario."""
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """Verifica si la contraseña coincide con la almacenada."""
        return bcrypt.check_password_hash(self.password, password)  # Relación con las publicaciones
    
    ##funciones para subs
    def subscribe(self, blog_owner):
        """Suscribirse a un blog."""
        if not self.is_subscribed(blog_owner):
            subscription = Suscriptor(blog_owner_id=blog_owner.user_id, subscriber_user_id=self.user_id)
            db.session.add(subscription)

    def unsubscribe(self, blog_owner):
        """Cancelar la suscripción a un blog."""
        subscription = Suscriptor.query.filter_by(blog_owner_id=blog_owner.user_id, subscriber_user_id=self.user_id).first()
        if subscription:
            db.session.delete(subscription)

    def is_subscribed(self, blog_owner):
        """Verificar si está suscrito al blog de un usuario."""
        return Suscriptor.query.filter_by(blog_owner_id=blog_owner.user_id, subscriber_user_id=self.user_id).count() > 0

    def notify_subscribers(self, post_title, post_url):
        # Ajuste de la consulta usando text()
        lambda_client = boto3.client('lambda', region_name='us-east-1')
        query = text("""
            SELECT u.email
            FROM suscriptores s
            JOIN users u ON s.subscriber_user_id = u.user_id
            WHERE s.blog_owner_id = :author_id
        """) 
        # Ejecutar la consulta con parámetros
        result = db.session.execute(query, {'author_id': self.user_id})
        subscribers = result.fetchall()
        # Extraer los correos electrónicos de los suscriptores
        subscriber_emails = [subscriber.email for subscriber in subscribers]
        if subscriber_emails:
            # Configurar el cliente de Lambda
            #credentials = get_temporary_credentials(self.role_arn)
            # Crear el payload para la invocación de Lambda
             # Configurar el cliente de AWS Lambda usando las credenciales temporales
            credentials = get_temporary_credentials(self.role_arn)
            lambda_client = create_lambda_client(credentials)

            payload = {
                "author_name": self.username,  # Usa username en lugar de name
                "post_title": post_title,
                "post_url": post_url,
                "subscriber_emails": subscriber_emails
            }

            function_name = 'SendEmail'
              # Invocar la función Lambda
            response = invoke_lambda_function(lambda_client, function_name, payload)
    

            # Invocar la función Lambda
            #response = lambda_client.invoke(
            #    FunctionName='SendEmail',  # Cambia al nombre de tu función Lambda
            #    InvocationType='Event',  # Event para invocación asíncrona
            #    Payload=json.dumps(payload)
            #)
    # Imprimir la respuesta de la función Lambda
            response_payload = json.load(response['Payload'])
            print("Lambda Response:", response_payload)

            # Opcional: Manejar la respuesta si es necesario
           # print("Lambda invoked with response:", credentials)
    
    def like_post(self, post):
        if not self.has_liked_post(post):
            post.likes += 1    

    @staticmethod
    def log_activity(user_id, activity_type, details=None):

        activity_table = get_dynamodb_table() 
        guatemala_tz = pytz.timezone('America/Guatemala')
        timestamp= datetime.now(guatemala_tz).strftime('%d-%m-%YT%H:%M:%S')
        
        if isinstance(details, dict):
        # Extraer solo valores planos del diccionario
            cleaned_details = {key: str(value) if not isinstance(value, (str, int, float, list, dict)) else value
                                for key, value in details.items()}
        else:
            cleaned_details = details or {}
        item = {
            'user_id': str(user_id),
            'timestamp': timestamp,
            'activity_type': activity_type,
            'details': json.dumps(cleaned_details)
        }
        # Insertar en la tabla DynamoDB
        print(f"Actividad registrada: {item}")
        activity_table.put_item(Item=item)
        
    @staticmethod
    def get_user_details():
        return db.session.query(
            User.username,
            User.email,
            db.func.count(Post.user_id).label('posts_count'),
            db.func.count(db.distinct(Suscriptor.subscriber_user_id)).label('subscribers_count'),
            User.role  # Incluye el campo 'role'
        ).outerjoin(Post, Post.user_id == User.user_id)\
        .outerjoin(Suscriptor, Suscriptor.blog_owner_id == User.user_id)\
        .group_by(User.user_id, User.username, User.email).all()

class Post(db.Model):
    __tablename__ = 'posts'
    post_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(255))  # URL de la imagen en S3
    thumbnail_url = db.Column(db.String(255))  # URL de la miniatura en S3
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)  # Relación con 'users.user_id'
    likes = db.Column(db.Integer, default=0)  # Campo de likes

class Suscriptor(db.Model):
    __tablename__ = 'suscriptores'
    subscriber_id = db.Column(db.Integer, primary_key=True)
    blog_owner_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    subscriber_user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow)