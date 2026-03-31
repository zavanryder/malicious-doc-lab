FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends tesseract-ocr && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV PYTHONPATH=/app

COPY demo-chatbot/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY demo-chatbot ./demo-chatbot
COPY shared_pipeline.py ./shared_pipeline.py

EXPOSE 8001

WORKDIR /app/demo-chatbot

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]
