FROM python:3.12-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

ENV ENV_FILE=/app/.env

EXPOSE 80

CMD ["python3", "app.py"]