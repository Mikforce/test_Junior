from flask import Flask, jsonify, request, send_file
import os
import io
import uuid
import subprocess
from models import User, Record, Base, engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
import re
from werkzeug.utils import secure_filename

app = Flask(__name__)

def sanitize_filename(filename):
    # Remove any non-alphanumeric characters from the filename
    filename = re.sub(r'[^\w\s-]', '', filename)
    # Replace whitespace characters with hyphens
    filename = re.sub(r'\s+', '-', filename)
    # Remove leading/trailing hyphens
    filename = filename.strip('-')
    # Make the filename lowercase
    filename = filename.lower()
    # Use Flask's built-in function to make the filename safe
    return secure_filename(filename)
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'wav', 'mp3'}
@app.route('/user', methods=['POST'])
def create_user():
    name = request.json['name']
    token = str(uuid.uuid4())
    user = User(name=name, token=token)
    session = Session()
    session.add(user)
    session.commit()
    session.close()
    return jsonify({'id': user.id, 'token': user.token})

@app.route('/record', methods=['POST'])
def add_record():
    user_id = request.json['user_id']
    token = request.json['token']
    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        wav_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        mp3_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{str(uuid.uuid4())}.mp3")
    subprocess.run(['ffmpeg', '-i', wav_path, '-f', 'mp3', '-ab', '192000', mp3_path])
    url = f"http://{request.host}/record?id={id}&user={user_id}"
    record = Record(user_id=user_id, url=url)
    session = Session()
    session.add(record)
    session.commit()
    session.close()
    return jsonify({'url': url})
@app.route('/record', methods=['GET'])
def get_record():
    user_id = request.args.get('user')
    record_id = request.args.get('id')
    session = Session()
    record = session.query(Record).filter(Record.user_id == user_id, Record.id == record_id).first()
    if not record:
        return jsonify({'error': 'Record not found.'}), 404
    path = record.url.split('/')[-1]
    return send_file(io.BytesIO(open(path, 'rb').read()), mimetype='audio/mp3')

if __name__ == '__main__':
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    app.config['UPLOAD_FOLDER'] = './uploads'
    app.run(debug=True)