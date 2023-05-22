from flask import Flask, request, Response
import psycopg2
import uuid
import os
import requests
from pydub import AudioSegment
import soundfile as sf


app = Flask(__name__)

DATABASE_URL = os.environ['DATABASE_URL']


def create_user(name):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    user_id = str(uuid.uuid4())
    token = str(uuid.uuid4())

    query = f"INSERT INTO users (id, name, token) VALUES ('{user_id}', '{name}', '{token}')"

    cur.execute(query)
    conn.commit()

    cur.close()
    conn.close()

    return user_id, token


def add_audio(user_id, token, audio_file):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    query = f"SELECT * FROM users WHERE id='{user_id}' AND token='{token}'"
    cur.execute(query)

    if cur.fetchone() is None:
        return Response(status=401)

    audio_id = str(uuid.uuid4())

    audio_wav = AudioSegment.from_file(audio_file, format="wav")
    audio_mp3 = audio_wav.export(f"/app/{audio_id}.mp3", format="mp3")

    data, samplerate = sf.read(f"/app/{audio_id}.mp3")
    duration = len(data) / samplerate

    query = f"INSERT INTO audios (id, user_id, filename, duration) VALUES ('{audio_id}', '{user_id}', '{audio_id}.mp3', {duration})"

    cur.execute(query)
    conn.commit()

    cur.close()
    conn.close()

    return audio_id

    @app.route('/user', methods=['POST'])
    def create_user_handler():
        name = request.json.get('name')

    if not name:
        return Response(status=400)

    user_id, token = create_user(name)

    response_data = {
        'user_id': user_id,
        'token': token
    }

    return response_data

    @app.route('/record', methods=['POST'])
    def add_audio_handler():
        user_id = request.form.get('user_id')

    token = request.form.get('token')
    audio_file = request.files.get('audio')

    if not all([user_id, token, audio_file]):
        return Response(status=400)

    audio_id = add_audio(user_id, token, audio_file)

    response_data = {
        'url': f'http://host:port/record?id={audio_id}&user={user_id}'
    }

    return response_data

@app.route('/record', methods=['GET'])
def get_audio_handler():
    audio_id = request.args.get('id')

    user_id = request.args.get('user')

    if not all([audio_id, user_id]):
        return Response(status=400)

    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    query = f"SELECT * FROM audios WHERE id='{audio_id}' AND user_id='{user_id}'"

    cur.execute(query)

    result = cur.fetchone()

    cur.close()
    conn.close()

    if result is None:
        return Response(status=404)

    filename = result[2]

    response = requests.get(f'http://host:port/{filename}')

    return response.content

if __name__ == '__main__':
        app.run(host='0.0.0.0', port=5000)

