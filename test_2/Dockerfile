FROM python:3.10-alpine

RUN mkdir /test_2
WORKDIR /test_2

COPY requirements.txt .

RUN pip install --upgrade pip -r requirements.txt

COPY . .

CMD ["python", "main.py"]

