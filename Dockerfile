FROM python:3.10-alpine

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN mkdir /app
WORKDIR /app
COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

RUN mkdir /app/static && mkdir /app/media

COPY . /app

EXPOSE 8000

CMD ["gunicorn", "dj_api_diplom.wsgi:application", "-b", "0.0.0.0:8000"]