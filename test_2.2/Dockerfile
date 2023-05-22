FROM python:3.9-slim-buster

RUN apt-get update && apt-get install -y libpq-dev gcc

COPY requirements.txt /app/requirements.txt

WORKDIR /test_2.2

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]

