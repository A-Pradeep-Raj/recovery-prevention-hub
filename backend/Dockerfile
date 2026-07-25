FROM python:3.11-slim

WORKDIR /app

# NOTE: build context for this Dockerfile is the repo root (not backend/), so
# that demo_data/ (needed for user seeding) can be copied in.
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app/ ./app/
COPY demo_data/ ./demo_data/

ENV PORT=8080
EXPOSE 8080

CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
