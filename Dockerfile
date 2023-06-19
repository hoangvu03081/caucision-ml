FROM python:3.10.11

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY ./caucisionml /app/caucisionml

CMD ["uvicorn", "caucisionml.main:app", "--host", "0.0.0.0", "--port", "8000"]