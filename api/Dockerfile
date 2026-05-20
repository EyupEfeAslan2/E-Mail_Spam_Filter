
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY data/model /app/data/model

COPY . .

COPY ui/app.js /app/app.js
COPY ui/style.css /app/style.css

CMD ["python", "start_app.py"]
