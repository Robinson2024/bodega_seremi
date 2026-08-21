FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --retries 10 -r requirements.txt

COPY ./sistema_bodega /app
COPY ./entrypoint.sh /app/entrypoint.sh
RUN sed -i 's/\r$//' /app/entrypoint.sh \
    && chmod +x /app/entrypoint.sh \
    && mkdir -p /app/db /app/staticfiles

EXPOSE 5000

ENTRYPOINT ["/app/entrypoint.sh"]
