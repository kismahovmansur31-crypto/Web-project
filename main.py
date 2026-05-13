import os
from flask import Flask, redirect, render_template, request
from PIL import Image, ImageOps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Автоматическое создание папки для фото при старте
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])


# Функция обработки фото через Pillow (кадрирование в квадрат 800x800)
def process_photo(input_file, slot_id):
    img = Image.open(input_file)
    img = ImageOps.fit(img, (800, 800), Image.Resampling.LANCZOS)
    filename = f"photo_{slot_id}.png"
    img.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))


# Главная страница: собирает все сохраненные фото и тексты
@app.route("/")
def index():
    photos = {}
    captions = {}
    for i in range(1, 7):
        photo_name = f"photo_{i}.png"
        if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], photo_name)):
            photos[i] = photo_name

        txt_path = os.path.join(app.config['UPLOAD_FOLDER'], f"caption_{i}.txt")
        if os.path.exists(txt_path):
            with open(txt_path, "r", encoding="utf-8") as f:
                captions[i] = f.read()
    return render_template('index.html', photos=photos, captions=captions)


# Маршрут для загрузки фото
@app.route('/upload', methods=['POST'])
def upload():
    slot_id = request.form.get('slot_id')
    file = request.files.get('photo')
    if file and slot_id:
        process_photo(file, slot_id)
    return redirect('/')


# Маршрут для сохранения текста подписи
@app.route('/save_caption', methods=['POST'])
def save_caption():
    slot_id = request.form.get('slot_id')
    text = request.form.get('caption')
    if slot_id:
        with open(os.path.join(app.config['UPLOAD_FOLDER'], f"caption_{slot_id}.txt"), "w", encoding="utf-8") as f:
            f.write(text)
    return redirect('/')


# Обработчик ошибки 404
@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404 — Страница не найдена. Вернитесь на главную.</h1>", 404


if __name__ == '__main__':
    app.run(port=8080, host='127.0.0.1')
