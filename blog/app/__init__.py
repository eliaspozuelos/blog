from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from .config import Config

# Inicialización de extensiones
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'main.login'  # Redirección si no está autenticado
login_manager.login_message_category = 'info'  # Categoría de mensaje de flash

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializar extensiones con la aplicación
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    # Registrar el blueprint de rutas
    from .routes import main
    app.register_blueprint(main)

    return app

