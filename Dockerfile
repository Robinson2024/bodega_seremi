FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --retries 10 -r requirements.txt
COPY ./sistema_bodega /app
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "sistema_bodega.wsgi:application"]
