import boto3
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from . import db, bcrypt, login_manager 
from .models import User, Post  
from .utils.sns_service import publish_to_sns

from werkzeug.utils import secure_filename
import pytz
from datetime import datetime


main = Blueprint('main', __name__)

@login_manager.user_loader
def load_user(user_id):
    from .models import User
    return User.query.get(int(user_id))

@main.route('/')
def index():
    """Página de inicio"""
    return render_template('base.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Validar campos manualmente
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('main.register'))
        
        # Comprobar si el usuario ya existe
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already taken. Please choose a different one.', 'danger')
            return redirect(url_for('main.register'))
        
        # Crear un nuevo usuario y guardar en la base de datos
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        role_arn = "arn:aws:iam::010526258375:role/user_blog"  # Cambia este ARN según tu configuración
        user = User(username=username, email=email, password=hashed_password, role_arn=role_arn)
        db.session.add(user)
        db.session.commit()

        
        
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('main.login'))

    return render_template('auth/register.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # Busca el usuario en la base de datos
        user = User.query.filter_by(username=username).first()
        # Verifica la contraseña
        if user and user.check_password(password):
            login_user(user)
            
            User.log_activity(user_id=user.user_id, activity_type='login')
            
            # Comprueba si el usuario es administrador y redirige adecuadamente
            if user.role == 'admin':
                flash('Login successful! Welcome Admin.', 'success')
                return redirect(url_for('main.index'))  # Redirige al panel de administración
            else:
                flash('Login successful!', 'success')
                return redirect(url_for('main.index'))  # Redirige a la página principal para usuarios no admin
        else:
            flash('Login failed. Check username and/or password.', 'danger')

    return render_template('auth/login.html')

@main.route('/logout')
@login_required
def logout():
    """Cierre de sesión"""
    User.log_activity(user_id=current_user.user_id, activity_type='logout')  # Usa current_user
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.login'))

@main.route('/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    print("Accedió a la página de creación de publicaciones")  # Verificar si se accede a la ruta correctamente
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        image = request.files.get('image')

        print("Título:", title)  # Imprimir título
        print("Contenido:", content)  # Imprimir contenido
        print("Imagen:", image)  # Verificar si se está recibiendo el archivo de imagen
        
        if not title or not content:
            flash('Title and content are required.', 'danger')
            return redirect(url_for('main.create_post'))
          
        # Obtener la hora actual en la zona horaria de Guatemala
        guatemala_tz = pytz.timezone('America/Guatemala')
        timestamp = datetime.now(guatemala_tz)  # Ahora datetime está definido

        # Subir la imagen a S3 si se proporciona
        image_url = None
        if image:
            print("Iniciando la subida de imagen a S3")  # Mensaje de inicio de subida
            s3 = boto3.client('s3')
            filename = secure_filename(image.filename)
            image_path = f"{filename}"
            #thumbnail_path = f"thumbnails/{filename}"
            resized_path = f"{filename}" # Ruta para la imagen redimensionada
            
            try:
                s3.upload_fileobj(
                    image,
                    current_app.config['S3_BUCKET'],
                    image_path
                  # ExtraArgs={'ACL': 'public-read'}
                )
                image_url = f"https://{current_app.config['S3_BUCKET']}.s3.{current_app.config['S3_REGION']}.amazonaws.com/{filename}"
                print("URL de la imagen:", image_url)  # Imprimir URL generada de la imagen
           
                # Construir la URL de la imagen redimensionada
                thumbnail_url = f"https://{current_app.config['S3_BUCKET_2']}.s3.{current_app.config['S3_REGION']}.amazonaws.com/resized-{resized_path}"
                print("URL de la imagen:", thumbnail_url)
                # Opcional: Esperar a que la imagen redimensionada esté lista
                waiter = boto3.client('s3').get_waiter('object_exists')
                waiter.wait(
                    Bucket=current_app.config['S3_BUCKET'],
                    Key=resized_path,
                    WaiterConfig={'Delay': 2, 'MaxAttempts': 10}
                )

            except Exception as e:
                flash(f"An error occurred while uploading the image: {e}", 'danger')
                return redirect(url_for('main.create_post'))

        # Crear la publicación y guardar en la base de datos
        post = Post(title=title, content=content, image_url=image_url, thumbnail_url=thumbnail_url,  created_at=timestamp, author=current_user)
        db.session.add(post)
        db.session.commit()
         # Notificar a los suscriptores
        post_url = url_for('main.user_blog', username=current_user.username, _external=True)


        current_user.notify_subscribers(title, post_url)  # Si usaste la función en el modelo
        # o
        # NotificationService.notify_subscribers(current_user, title, post_url)  # Si usaste el servicio

        flash('Your post has been created and notifications have been sent!', 'success')
        return redirect(url_for('main.index'))

    return render_template('auth/create_post.html')

@main.route('/edit/<int:post_id>', methods=['POST'])
def edit_post(post_id):
    data = request.get_json()
    post = Post.query.get_or_404(post_id)
    post.title = data['title']
    post.content = data['content']
    db.session.commit()
    return jsonify({'success': True})

@main.route('/delete/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    return jsonify({'message': 'Post eliminado correctamente'}), 200

@main.route('/blog', methods=['GET'])
@login_required
def list_posts():
    # Usar current_user.user_id para filtrar las publicaciones
    user_posts = Post.query.filter_by(user_id=current_user.user_id).all()
    return render_template('auth/list_posts.html', posts=user_posts)

@main.route('/blog/<username>', methods=['GET'])
def user_blog(username):
    user = User.query.filter_by(username=username).first_or_404()
    user_posts = Post.query.filter_by(user_id=user.user_id).all()
  
    #Registrar la actividad si el usuario actual está autenticado
    if current_user.is_authenticated:
        try:
            user.log_activity(
                user_id=current_user.user_id,  # ID del usuario actual
                activity_type='blog_view',    # Tipo de actividad
                details={'blog_owner': username}  # Información adicional
            )
        except Exception as e:
            # Manejar errores para que no interrumpan la funcionalidad principal
            print(f"Error registrando actividad: {e}")

    return render_template('auth/user_blog.html', user=user, posts=user_posts)


@main.route('/search', methods=['GET', 'POST'])
@login_required
def search_users():
    if request.method == 'POST':
        search_query = request.form.get('search', '').strip()
        users = User.query.filter(User.username.ilike(f'%{search_query}%'), User.role != 'admin').all()
        return render_template('search_results.html', users=users, search_query=search_query)
    return render_template('search.html')


#para subs

@main.route('/subscribe/<username>', methods=['POST'])
@login_required
def subscribe(username):
    blog_owner = User.query.filter_by(username=username).first_or_404()
    if blog_owner == current_user:
        flash('No puedes suscribirte a tu propio blog.', 'danger')
        return redirect(url_for('main.user_blog', username=username))
    current_user.subscribe(blog_owner)
    db.session.commit()
    flash(f'Te has suscrito al blog de {blog_owner.username}.', 'success')
    return redirect(url_for('main.user_blog', username=username))

@main.route('/unsubscribe/<username>', methods=['POST'])
@login_required
def unsubscribe(username):
    blog_owner = User.query.filter_by(username=username).first_or_404()
    if blog_owner == current_user:
        flash('No puedes cancelar la suscripción a tu propio blog.', 'danger')
        return redirect(url_for('main.user_blog', username=username))
    current_user.unsubscribe(blog_owner)
    db.session.commit()
    flash(f'Has cancelado la suscripción al blog de {blog_owner.username}.', 'success')
    return redirect(url_for('main.user_blog', username=username))

@main.route('/like/<int:post_id>', methods=['POST'])
@login_required
def toggle_like(post_id):
    post = Post.query.get_or_404(post_id)
    if 'unlike' in request.form:
        post.likes = max(0, post.likes - 1)  # Reducir likes sin permitir valores negativos
        flash(f'Quitaste tu like del post: {post.title}', 'warning')
    else:
        post.likes += 1  # Incrementar likes
        flash(f'Le diste like al post: {post.title}', 'success')
    db.session.commit()
    return redirect(url_for('main.user_blog', username=post.author.username))

@main.route('/view-adm')
@login_required
def view_adm():
    if current_user.role != 'admin':  # Asumimos que existe esta propiedad o método en el modelo de usuario
        flash('No tienes permiso para acceder a esta página.', 'danger')
        return redirect(url_for('main.index'))

    users = User.get_user_details()  # Utiliza el método estático
    print(users)
     # Esta función debe implementarse para manejar sesiones activas

    return render_template('auth/view_adm.html', users=users)

# Ruta para manejar el formulario de notificaciones
@main.route('/send_notification', methods=['GET', 'POST'])
def send_notification():
    if request.method == 'POST':
        try:
            # Obtén los datos del formulario
            topic_arn = request.form.get('topic_arn')
            subject = request.form.get('subject', 'Notificación del Administrador')
            message = request.form.get('message', 'Mensaje vacío')

            # Llama a la función para publicar el mensaje
            publish_to_sns(message, subject, topic_arn)

            # Usa flash para mostrar un mensaje de éxito
            flash("La notificación fue enviada exitosamente.", "success")
            return redirect(url_for('main.send_notification'))
        except Exception as e:
            # Usa flash para mostrar un mensaje de error
            flash(f"Error al enviar la notificación: {str(e)}", "danger")
            return redirect(url_for('main.send_notification'))

    # Si es GET, renderiza el formulario
    return render_template('auth/send_notification.html')

