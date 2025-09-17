FROM python:3.9

WORKDIR /app

RUN apt-get update && apt-get install -y ffmpeg

COPY backend/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
