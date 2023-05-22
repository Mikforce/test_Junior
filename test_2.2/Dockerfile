FROM python:3.10-alpine

RUN mkdir /test_2
WORKDIR /test_1

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]