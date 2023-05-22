from flask import Flask, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from pydub import AudioSegment
import os
import uuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://admin:admin@db/admin'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = "./uploads"
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    uuid = db.Column(db.String(36), nullable=False, unique=True)
    access_token = db.Column(db.String(36), nullable=False, unique=True)

class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), nullable=False, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    url = db.Column(db.String(200), nullable=False)

@app.route('/users', methods=['POST'])
def create_user():
    name = request.json.get('name')
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    new_user = User(name=name, uuid=str(uuid.uuid4()), access_token=str(uuid.uuid4()))
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'id': new_user.id, 'uuid': new_user.uuid, 'access_token': new_user.access_token})

@app.route('/records', methods=['POST'])
def add_record():
    user_uuid = request.form.get('user_uuid')
    access_token = request.form.get('access_token')
    file = request.files.get('file')
    if not user_uuid:
        return jsonify({'error': 'User UUID is required'}), 400
    if not access_token:
        return jsonify({'error': 'Access token is required'}), 400
    user = User.query.filter_by(uuid=user_uuid, access_token=access_token).first()
    if not user:
        return jsonify({'error': 'Invalid user credentials'}), 401
    if not file or not file.filename.endswith('.wav'):
        return jsonify({'error': 'WAV file is required'}), 400
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    mp3name = f"{uuid.uuid4()}.mp3"
    mp3path = os.path.join(app.config['UPLOAD_FOLDER'], mp3name)
    AudioSegment.from_wav(filepath).export(mp3path, format="mp3")
    record = Record(uuid=str(uuid.uuid4()), user_id=user.id, url=f"http://host:port/record?id={mp3name}&user={user.id}")
    db.session.add(record)
    db.session.commit()
    return jsonify({'id': record.id, 'uuid': record.uuid, 'url': record.url})

@app.route('/record', methods=['GET'])
def download_record():
    id = request.args.get('id')
    user_id = request.args.get('user')
    if not id:
        return jsonify({'error': 'Record ID is required'}), 400
    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400
    record = Record.query.filter_by(id=id, user_id=user_id).first()
    if not record:
        return jsonify({'error': 'Record does not exist'}), 404
    mp3path = os.path.join(app.config['UPLOAD_FOLDER'], id)
    if not os.path.exists(mp3path):
        return jsonify({'error': 'File does not exist'}), 404
    return send_file(mp3path)

app.use_x_sendfile = True
app.config['STATIC_FOLDER'] = "./uploads"


if __name__ == '__main__':
    app.run(debug=True)
