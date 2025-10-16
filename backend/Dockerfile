FROM python:3.12-slim

WORKDIR /app

# Install backend dependencies first to leverage Docker layer caching.
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend package into /app/backend so "backend.*" imports resolve
# consistently in both development and production containers.
COPY . /app/backend

# Ensure Python can import the backend package from /app.
ENV PYTHONPATH="/app"

EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
