FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*

COPY Backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY Backend/app ./app
COPY Backend/ai ./ai
COPY Backend/seed_data.py ./seed_data.py
COPY Worker-Safety/best.pt Worker-Safety/yolov8n.pt ./Worker-Safety/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
