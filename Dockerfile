FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Set working directory
WORKDIR /app

# Install system dependencies needed for OpenCV, Tesseract, etc.
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user (UID 1000 as required by k8s deployment)
RUN groupadd -r execra && useradd -r -g execra -u 1000 execra

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=1000 -r requirements.txt

# Copy application source code
COPY . .

# Change ownership of the app directory to the non-root user
RUN chown -R execra:execra /app

# Switch to the non-root user
USER execra

# Expose the API port
EXPOSE 8000

# Command to run the FastAPI app
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
