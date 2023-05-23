# import psycopg2 as psycopg2
# from flask import Flask, request, jsonify, send_from_directory
# import uuid
# import os
#
# app = Flask(__name__)
# app.config['UPLOAD_FOLDER'] = 'uploads'
# # connect to postgres database
# db = psycopg2.connect(
#     host='localhost',
#     port=5432,
#     dbname='dbname',
#     user='user',
#     password='password'
# )
#
#
# @app.route('/create_user', methods=['POST'])
# def create_user():
#     # get user name from request
#     username = request.json['username']
#
#     # generate unique user id and access token
#     user_id = str(uuid.uuid4())
#     access_token = str(uuid.uuid4())
#
#     # insert user record into database
#     cur = db.cursor()
#
#     cur.execute(f"INSERT INTO users (id, username, access_token) VALUES ('{user_id}', '{username}', '{access_token}')")
#     db.commit()
#
#     return jsonify({'user_id': user_id, 'access_token': access_token}), 200
#
#
# @app.route('/add_audio', methods=['POST'])
# def add_audio():
#     # get user id, access token and audio file from request
#     user_id = request.form.get('user_id')
#     access_token = request.form.get('access_token')
#     audio_file = request.files['audio_file']
#
#     # verify user access token
#     cur = db.cursor()
#     cur.execute(f"SELECT access_token FROM users WHERE id = '{user_id}'")
#     user_access_token = cur.fetchone()[0]
#     if user_access_token != access_token:
#         return jsonify({'error': 'access denied'}), 401
#
#     # convert audio file to mp3 format
#     audio_id = str(uuid.uuid4())
#     audio_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{audio_id}.mp3")
#     audio_file.save(audio_path)
#
#     # insert audio record into database
#     cur.execute(f"INSERT INTO audios (id, user_id, filename) VALUES ('{audio_id}', '{user_id}', '{audio_id}.mp3')")
#     db.commit()
#
#     # return download url for the audio file
#     return jsonify({'url': f"http://host:port/record?id={audio_id}&user={user_id}"}), 200
#
#
# @app.route('/record')
# def download_record():
#     # get audio id and user id from request
#     audio_id = request.args.get('id')
#     user_id = request.args.get('user')
#
#     # verify user access to the audio file
#     cur = db.cursor()
#     cur.execute(f"SELECT filename FROM audios WHERE id = '{audio_id}' AND user_id = '{user_id}'")
#     filename = cur.fetchone()[0]
#     if filename is None:
#         return jsonify({'error': 'access denied'}), 401
#
#     # return audio file for download
#     return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


import psycopg2 as psycopg2
from flask import Flask, request, jsonify, send_from_directory
import uuid
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

class Database:
    def __init__(self):
        # connect to postgres database
        self.connection = psycopg2.connect(
            host='localhost',
            port=5432,
            dbname='dbname',
            user='user',
            password='password'
        )

        # create users table if it doesn't exist
        with self.connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id UUID PRIMARY KEY,
                    username TEXT NOT NULL,
                    access_token UUID NOT NULL
                )
            """)
            self.connection.commit()

        # create audios table if it doesn't exist
        with self.connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audios (
                    id UUID PRIMARY KEY,
                    user_id UUID NOT NULL REFERENCES users (id),
                    filename TEXT NOT NULL
                )
            """)
            self.connection.commit()

    def insert_user(self, username, access_token):
        # generate unique user id
        user_id = str(uuid.uuid4())

        # insert user record into database
        with self.connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO users (id, username, access_token)
                VALUES (%s, %s, %s)
            """, (user_id, username, access_token))
            self.connection.commit()

        return {'user_id': user_id, 'access_token': access_token}

    def insert_audio(self, user_id, access_token, audio_file):
        # verify user access token
        with self.connection.cursor() as cursor:
            cursor.execute("""
                SELECT access_token FROM users WHERE id = %s
            """, (user_id,))
            user_access_token = cursor.fetchone()[0]

            if user_access_token != access_token:
                return {'error': 'access denied'}, 401

        # convert audio file to mp3 format
        audio_id = str(uuid.uuid4())
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{audio_id}.mp3")
        audio_file.save(audio_path)

        # insert audio record into database
        with self.connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO audios (id, user_id, filename)
                VALUES (%s, %s, %s)
            """, (audio_id, user_id, f"{audio_id}.mp3"))
            self.connection.commit()

        # return download url for the audio file
        return {'url': f"http://host:port/record?id={audio_id}&user={user_id}"}

    def get_audio_filename(self, audio_id, user_id):
        # verify user access to the audio file
        with self.connection.cursor() as cursor:
            cursor.execute("""
                SELECT filename FROM audios WHERE id = %s AND user_id = %s
            """, (audio_id, user_id))
            filename = cursor.fetchone()[0]

            if filename is None:
                return {'error': 'access denied'}, 401

        return filename

db = Database()

@app.route('/create_user', methods=['POST'])
def create_user():
    # get user name from request
    username = request.json['username']
    access_token = str(uuid.uuid4())

    result = db.insert_user(username, access_token)
    return jsonify(result), 200

@app.route('/add_audio', methods=['POST'])
def add_audio():
    # get user id, access token and audio file from request
    user_id = request.form.get('user_id')
    access_token = request.form.get('access_token')
    audio_file = request.files['audio_file']

    result = db.insert_audio(user_id, access_token, audio_file)
    return jsonify(result), 200

@app.route('/record')
def download_record():
    # get audio id and user id from request
    audio_id = request.args.get('id')
    user_id = request.args.get('user')

    # get audio file name from database
    filename = db.get_audio_filename(audio_id, user_id)

    # return audio file for download
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)