import os
from flask import Flask, redirect, render_template, request
from flask_wtf import FlaskForm
from wtforms import PasswordField, BooleanField, SubmitField, EmailField
from wtforms.validators import DataRequired
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from PIL import Image, ImageOps
from data import db_session
from data.users import User
from forms.user import RegisterForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

login_manager = LoginManager()
login_manager.init_app(app)

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])


def process_photo(input_file, slot_id):
    img = Image.open(input_file)
    img = ImageOps.fit(img, (800, 800), Image.Resampling.LANCZOS)
    filename = f"user{current_user.id}_photo_{slot_id}.png"
    img.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))


class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


@app.route("/")
def index():
    photos = {}
    captions = {}
    if current_user.is_authenticated:
        for i in range(1, 7):
            p_name = f"user{current_user.id}_photo_{i}.png"
            if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], p_name)):
                photos[i] = p_name

            t_name = f"user{current_user.id}_caption_{i}.txt"
            t_path = os.path.join(app.config['UPLOAD_FOLDER'], t_name)
            if os.path.exists(t_path):
                with open(t_path, "r", encoding="utf-8") as f:
                    captions[i] = f.read()
    return render_template('index.html', photos=photos, captions=captions)


@app.route('/upload', methods=['POST'])
@login_required
def upload():
    slot_id = request.form.get('slot_id')
    file = request.files.get('photo')
    if file and slot_id:
        process_photo(file, slot_id)
    return redirect('/')


@app.route('/save_caption', methods=['POST'])
@login_required
def save_caption():
    slot_id = request.form.get('slot_id')
    text = request.form.get('caption')
    if slot_id:
        filename = f"user{current_user.id}_caption_{slot_id}.txt"
        with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), "w", encoding="utf-8") as f:
            f.write(text)
    return redirect('/')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect("/")
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html', message="Неправильный логин или пароль", form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect("/")
    form = RegisterForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация', form=form,
                                   message="Такой пользователь уже есть")
        user = User(name=form.name.data, email=form.email.data)
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.get(User, user_id)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404 — Страница не найдена.</h1>", 404


if __name__ == '__main__':
    db_session.global_init("db/blogs.db")
    app.run(port=8080, host='127.0.0.1')