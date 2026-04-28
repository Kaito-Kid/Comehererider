FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p logs app/static/uploads

EXPOSE 5000

ENV FLASK_APP=wsgi.py
ENV PYTHONUNBUFFERED=1

CMD flask db upgrade && gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
