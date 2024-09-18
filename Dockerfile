FROM python:3.12-slim

WORKDIR /app

COPY . /app

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y tesseract-ocr libtesseract-dev tesseract-ocr-rus &&\
    apt-get clean 

RUN apt install -y libgl1

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

ENV ENV_FILE=/app/.env

EXPOSE 80

CMD ["python3", "app.py"]