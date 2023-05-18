from flask import Flask, request, jsonify
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
import requests

app = Flask(__name__)

# Подключение к базе данных
engine = create_engine('postgresql://admin:admin@localhost/admin')
Session = sessionmaker(bind=engine)
Base = declarative_base()
session = Session()


# Модель вопроса для хранения в базе данных
class Question(Base):
    __tablename__ = 'questions'
    id = Column(Integer, primary_key=True)
    question_text = Column(String)
    answer_text = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
Base.metadata.create_all(engine)

@app.route('/questions', methods=['GET', 'POST'])
def create_questions():

    questions = []

    while len(questions) < 1:

        response = requests.get("https://jservice.io/api/random?count=1")

        json_data = response.json()

        question_text = json_data[0]['question']

        answer_text = json_data[0]['answer']

        # Проверяем, есть ли такой вопрос уже в базе данных
        existing_question = session.query(Question).filter_by(question_text=question_text).first()

        if existing_question:
            continue  # Пропускаем сохранение и запрашиваем новый вопрос

        question = Question(question_text=question_text, answer_text=answer_text)
        session.add(question)
        session.commit()
        questions.append(question)


    if questions:
        latest_question = questions[-1]
        response = {
            'id': latest_question.id,
            'question': latest_question.question_text,
            'answer': latest_question.answer_text
            }
        return jsonify(response)
    else:
        return jsonify({'message': 'No questions found.'})


if __name__ == '__main__':
    app.run(debug=True)