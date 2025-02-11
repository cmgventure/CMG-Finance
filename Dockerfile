FROM python:3.11

WORKDIR /src

COPY ./requirements.txt /src/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /src/requirements.txt

COPY . /src

CMD uvicorn app.main:app --reload --port 8080 --host 0.0.0.0