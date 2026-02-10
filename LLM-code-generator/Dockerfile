FROM python:3.11-slim-bookworm

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code into /app
COPY backend/ ./backend/

# Copy frontend static files into /app/static
COPY frontend/ ./frontend/

COPY workflows/ /app/workflows

COPY agents/ /app/agents

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
