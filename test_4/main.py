from sqlalchemy import create_engine
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import uuid
import subprocess
app = Flask(__name__)

DATABASE_URI = 'postgresql://admin:admin@localhost/admin'
engine = create_engine(DATABASE_URI)

# Настройки для загрузки файлов
UPLOAD_FOLDER = '/path/to/upload/folder'
ALLOWED_EXTENSIONS = {'wav'}


# Функция проверки разрешенного расширения файла
def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# REST метод создания пользователя
@app.route('/user', methods=['POST'])
def create_user():
    # Получаем имя пользователя из запроса
    username = request.json.get('username')

    # Генерируем уникальный идентификатор пользователя
    user_id = str(uuid.uuid4())

    # Генерируем UUID токен доступа для пользователя
    token = str(uuid.uuid4())

    # Записываем данные пользователя в БД
    # Реализация может быть разной, в зависимости от используемой ORM
    db.insert_user(user_id, username, token)

    # Возвращаем сгенерированный идентификатор пользователя и токен
    return jsonify({'user_id': user_id, 'token': token}), 201


# REST метод добавления аудиозаписи
@app.route('/record', methods=['POST'])
def upload_record():
    # Получаем остальные параметры из запроса
    user_id = request.form['user_id']
    token = request.form['token']

    # Проверяем корректность токена
    if not db.check_token(user_id, token):
        return jsonify({'error': 'Invalid token'}), 401

    # Проверяем, что файл был загружен
    if 'file' not in request.files:
        return jsonify({'error': 'No file included'}), 400

    file = request.files['file']

    # Проверяем расширение файла
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file extension'}), 400

    # Генерируем уникальный идентификатор для записи
    record_id = str(uuid.uuid4())

    # Сохраняем wav-файл на сервере
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    # Конвертируем в mp3 и сохраняем его на сервере
    mp3_filepath = os.path.join(UPLOAD_FOLDER, '{}.mp3'.format(record_id))
    subprocess.call(['ffmpeg', '-i', filepath, mp3_filepath])

    # Записываем данные файла в БД
    db.insert_record(record_id, user_id, mp3_filepath)

    # Генерируем URL для загрузки
    url = 'http://host:port/record?id={}&user={}'.format(record_id, user_id)

    # Возвращаем URL для скачивания записи
    return jsonify({'url': url}), 201


@app.route('/record', methods=['GET'])
def download_record():
    # Получаем параметры из запроса
    record_id = request.args.get('id')
    user_id = request.args.get('user')

    # Получаем данные записи из БД
    record = db.get_record(record_id)

    # Проверяем, что пользователь имеет доступ к записи
    if not record or record.user_id != user_id:
        return jsonify({'error': 'Record not found or unauthorized access'}), 401

    # Отправляем файл на скачивание
    return send_file(record.filepath, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)