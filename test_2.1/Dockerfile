FROM python:3.10-alpine

RUN mkdir /test_2.1
WORKDIR /test_2.1

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "app.py"]