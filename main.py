from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, EmailField
from wtforms.validators import DataRequired
from flask import Flask, redirect, render_template
from data import db_session
from forms.user import RegisterForm
from flask_login import LoginManager
from flask_login import login_user, login_required, logout_user
from data.users import User
import os
from PIL import Image, ImageOps
from flask import request

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
class LoginForm(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)

@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)

@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.get(User,user_id)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")

def process_photo(input_file, slot_id):
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    img = Image.open(input_file)
    # Делаем фото квадратным 600x600
    img = ImageOps.fit(img, (600, 600), Image.Resampling.LANCZOS)
    filename = f"photo_{slot_id}.png"
    img.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

@app.route('/upload', methods=['POST'])
def upload():
    slot_id = request.form.get('slot_id')
    file = request.files.get('photo')
    if file and slot_id:
        process_photo(file, slot_id)
    return redirect('/')

# И обнови свой старый маршрут index, чтобы он видел фотки:
@app.route("/")
def index():
    photos = {}
    for i in range(1, 7):
        if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], f"photo_{i}.png")):
            photos[i] = f"photo_{i}.png"
    return render_template('index.html', photos=photos)





if __name__ == '__main__':
    db_session.global_init("db/blogs.db")
    app.run(port=8080, host='127.0.0.1')