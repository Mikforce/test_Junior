from typing import List
import os
import uuid
import base64

from flask import Flask, jsonify, request, send_file
from sqlalchemy.types import LargeBinary
from sqlalchemy import create_engine, Column, Integer, String, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from flask_cors import CORS

import ffmpeg
app = Flask(__name__)
CORS(app)

engine = create_engine('postgresql://user:user@localhost/user')
Session = sessionmaker(bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    token = Column(String(50), unique=True)

    def __repr__(self):
        return f"<User(name='{self.name}', token='{self.token}')>"

class Record(Base):
    __tablename__ = 'records'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    audio_wav = Column(LargeBinary)
    audio_mp3 = Column(LargeBinary)
    uuid = Column(String(50), unique=True)

    UniqueConstraint(user_id, uuid)

    def __repr__(self):
        return f"<Record(user_id={self.user_id}, uuid='{self.uuid}')>"

def create_tables():
    Base.metadata.create_all(engine)

@app.route('/users/', methods=['POST'])
def create_user():
    session = Session()
    try:
        data = request.json
        name = data['name']
        token = str(uuid.uuid4())
        user = User(name=name, token=token)
        session.add(user)
        session.commit()

        return jsonify({
            'id': user.id,
            'access_token': user.token
        }), 201
    except KeyError:
        return jsonify({'error': 'Invalid input'}), 400
    except SQLAlchemyError as e:
        session.rollback()
        error = str(e.__dict__['orig'])
        return jsonify({'error': error}), 409
    finally:
        session.close()

@app.route('/records', methods=['POST'])
def add_record():
    session = Session()
    try:
        data = request.form
        user_id = int(data['user_id'])
        access_token = data['access_token']
        audio_wav = request.files['audio'].read()

        # Проверить токен доступа
        user = session.query(User).filter(User.id == user_id, User.token == access_token).first()
        if not user:
            return jsonify({'error': 'Unauthorized'}), 401

        # Конвертировать аудио в mp3
        audio_conv = ffmpeg(inputs={'pipe:0': '-f wav -ac 2 -ar 44100'}, outputs={'pipe:1': '-f mp3 -q:a 0 -map a'})
        audio_mp3 = audio_conv.run(audio_wav)[0]

        # Сохранить запись в базу данных
        uuid_str = str(uuid.uuid4())
        record = Record(user_id=user_id, audio_wav=audio_wav, audio_mp3=audio_mp3, uuid=uuid_str)
        session.add(record)
        session.commit()

        return jsonify({
            'url': f'http://{request.host}/record?id={uuid_str}&user={user_id}'
        }), 201
    except KeyError:
        return jsonify({'error': 'Invalid input'}), 400
    except SQLAlchemyError as e:
        session.rollback()
        error = str(e.__dict__['orig'])
        return jsonify({'error': error}), 409
    finally:
        session.close()

@app.route('/record')
def download_record():
    session = Session()
    try:
        uuid_str = request.args.get('id')
        user_id = int(request.args.get('user'))

        # Проверять
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
        if request.args.get('token') != user.token:
            return jsonify({'error': 'Unauthorized'}), 401

        # Получить запись из базы данных
        record = session.query(Record).filter(Record.user_id == user_id, Record.uuid == uuid_str).first()
        if not record:
            return jsonify({'error': 'Record not found'}), 404

        # Вернуть аудиофайл
        return send_file(
            data=record.audio_mp3,
            mimetype='audio/mpeg',
            attachment_filename=f'record_{uuid_str}.mp3',
            as_attachment=True
        )

    except ValueError:
        return jsonify({'error': 'Invalid user ID'}), 400
    except SQLAlchemyError as e:
        session.rollback()
        error = str(e.__dict__['orig'])
        return jsonify({'error': error}), 409
    finally:
        session.close()

if __name__ == '__main__':
    create_tables()
    app.run(host='0.0.0.0', port=5000)
