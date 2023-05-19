from flask import Flask, request, jsonify, send_file
from sqlalchemy import create_engine, Column, Integer, String, DateTime
import os
import uuid
import subprocess

# Инициализация приложения
app = Flask(__name__)

# Конфигурация базы данных
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:password@db/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализация БД
db = SQLAlchemy(app)

# Модель User
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    token = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return '<User %r>' % self.name

# Модель Record
class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    wav_filename = db.Column(db.String(100), nullable=False, unique=True)
    mp3_filename = db.Column(db.String(100), nullable=False, unique=True)

    def __repr__(self):
        return '<Record %r>' % self.name

# Метод создания пользователя
@app.route('/user', methods=['POST'])
def create_user():
    data = request.get_json()
    name = data['name']
    token = str(uuid.uuid4())
    user = User(name=name, token=token)
    db.session.add(user)
    db.session.commit()
    return jsonify({'id': user.id, 'token': user.token})

# Метод добавления аудиозаписи
@app.route('/record', methods=['POST'])
def create_record():
    data = request.form
    user_id = data['user_id']
    token = data['token']
    file = request.files['file']
    if not validate_user_token(user_id, token):
        return jsonify({'error': 'Invalid token'}), 401
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    filename = secure_filename(file.filename)
    wav_filename = f'{uuid.uuid4()}.wav'
    mp3_filename = f'{uuid.uuid4()}.mp3'
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], wav_filename)
    file.save(file_path)
    subprocess.run(['ffmpeg', '-i', file_path, '-ar', '22050', '-ac', '1', os.path.join(app.config['UPLOAD_FOLDER'], mp3_filename)])
    record = Record(user_id=user_id, name=filename, wav_filename=wav_filename, mp3_filename=mp3_filename)
    db.session.add(record)
    db.session.commit()
    return jsonify({'url': f'http://{request.host}/record?id={record.mp3_filename}&user={record.user_id}'})

# Метод скачивания записи
@app.route('/record', methods=['GET'])
def download_record():
    id = request.args.get('id')
    user_id = request.args.get('user')
    record = Record.query.filter_by(mp3_filename=id, user_id=user_id).first()
    if not record:
        return jsonify({'error': 'Record not found'}), 404
    filename = os.path.join(app.config['UPLOAD_FOLDER'], record.mp3_filename)
    return send_file(filename, mimetype='audio/mpeg')

# Вспомогательный метод для проверки токена пользователя
def validate_user_token(user_id, token):
    user = User.query.filter_by(id=user_id, token=token).first()
    return True if user else False

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')