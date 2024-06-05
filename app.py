from flask import Flask, render_template, redirect, url_for, request, flash
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
import os
from mongodb import init_app, find_user_by_id, find_user_by_username, insert_user, insert_film, find_films_by_user_id, find_film_by_id, delete_film

app = Flask(__name__)
app.config['MONGO_URI'] = os.getenv('MONGO_URI', 'mongodb://localhost:27017/film_db')
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

mongo = init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    user = find_user_by_id(user_id)
    if user:
        return User(user)
    return None

class User(UserMixin):
    def __init__(self, user):
        self.id = str(user['_id'])
        self.username = user['username']

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = find_user_by_username(username)
        if user:
            flash('Username already exists. Please choose a different username.', 'danger')
            return redirect(url_for('register'))
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        insert_user(username, hashed_password)
        flash('You have successfully registered!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = find_user_by_username(username)
        if user and bcrypt.check_password_hash(user['password'], password):
            user_obj = User(user)
            login_user(user_obj)
            return redirect(url_for('index'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    films = find_films_by_user_id(current_user.get_id())
    return render_template('index.html', films=films)

@app.route('/add_film', methods=['GET', 'POST'])
@login_required
def add_film():
    if request.method == 'POST':
        title = request.form['title']
        opinion = request.form['opinion']
        image = request.files['image']
        if image:
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            insert_film(title, opinion, filename, current_user.get_id())
            flash('Film added successfully!', 'success')
            return redirect(url_for('index'))
    return render_template('add_film.html')

@app.route('/delete_film/<film_id>', methods=['POST'])
@login_required
def delete_film_route(film_id):
    film = find_film_by_id(film_id)
    if film and film['user_id'] == current_user.get_id():
        delete_film(film_id)
        if 'image' in film:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], film['image']))
        flash('Film deleted successfully!', 'success')
    else:
        flash('You do not have permission to delete this film.', 'danger')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5012, debug=True)
