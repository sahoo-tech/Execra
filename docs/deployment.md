# Deployment Guide

This guide explains how to deploy and run the application across all officially supported environments.

**Intended audience:**

- New contributors and GSSoC beginners
- Local developers
- Production operators and DevOps engineers

For a deeper understanding of the internal architecture and module structure, see [Architecture Documentation](./architecture.md).

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Variables](#environment-variables)
3. [Local Development](#local-development)
4. [Docker Compose Deployment](#docker-compose-deployment)
5. [Docker Production Deployment](#docker-production-deployment)
6. [Kubernetes Deployment](#kubernetes-deployment)
7. [TLS and HTTPS Setup](#tls-and-https-setup)
8. [Troubleshooting](#troubleshooting)
9. [Deployment Best Practices](#deployment-best-practices)

---

## Prerequisites

Ensure the following tools are installed before you begin.

| Tool | Recommended Version |
|------|---------------------|
| Python | 3.10+ |
| Docker | 24+ |
| Docker Compose | 2+ |
| Kubernetes | 1.28+ *(optional)* |
| kubectl | Latest |
| Git | Latest |

---

## Environment Variables

The application is configured through environment variables. Create a `.env` file in the project root:

```bash
touch .env
```

**Example `.env` configuration:**

```env
APP_ENV=development

HOST=0.0.0.0
PORT=8000

REDIS_HOST=redis
REDIS_PORT=6379

YOLO_MODEL_PATH=models/yolov8n.pt

SCREEN_CAPTURE_ENABLED=true

LOG_LEVEL=info
```

> ⚠️ **Never commit real secrets or production credentials to version control.**

---

## Local Development

Recommended for contributors and first-time developers.

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/your-repo.git
cd your-repo
```

### 2. Create a Virtual Environment

**Linux / macOS:**

```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Edit the `.env` file to match your local environment.

### 5. Start Redis

If your setup requires Redis, start it via Docker:

```bash
docker run -d \
  --name redis \
  -p 6379:6379 \
  redis:7
```

### 6. Run the Application

```bash
python main.py
```

If the application uses Uvicorn directly:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 7. Verify the Application

Open your browser and navigate to:

```
http://localhost:8000
```

If Swagger/OpenAPI docs are enabled:

```
http://localhost:8000/docs
```

---

## Docker Compose Deployment

Recommended for local multi-service development.

### Start Services

```bash
docker-compose up --build
```

Run in detached mode:

```bash
docker-compose up -d --build
```

### Stop Services

```bash
docker-compose down
```

### Example `docker-compose.yml`

```yaml
version: "3.9"

services:
  app:
    build: .
    container_name: app
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./models:/app/models
      - ./logs:/app/logs
    depends_on:
      - redis

  redis:
    image: redis:7
    container_name: redis
    ports:
      - "6379:6379"
```

### Useful Commands

| Action | Command |
|--------|---------|
| View running containers | `docker-compose ps` |
| Stream logs | `docker-compose logs -f` |
| Restart services | `docker-compose restart` |

---

## Docker Production Deployment

### Multi-Stage Dockerfile

Use a multi-stage build to keep the production image lean:

```dockerfile
# =========================
# Builder Stage
# =========================
FROM python:3.11-slim AS builder

WORKDIR /app

COPY requirements.txt .

RUN pip install --user --no-cache-dir -r requirements.txt

# =========================
# Final Stage
# =========================
FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /root/.local /root/.local

ENV PATH=/root/.local/bin:$PATH

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Build the Production Image

```bash
docker build -t app-production .
```

### Run the Production Container

```bash
docker run -d \
  --name app-production \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/logs:/app/logs \
  app-production
```

### Useful Commands

```bash
# Stream container logs
docker logs -f app-production

# Stop the container
docker stop app-production
```

---

## Kubernetes Deployment

### Recommended Directory Structure

```
k8s/
├── deployment.yaml
├── service.yaml
├── configmap.yaml
├── secret.yaml
└── ingress.yaml
```

### 1. Create a ConfigMap

`k8s/configmap.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  APP_ENV: "production"
  LOG_LEVEL: "info"
```

```bash
kubectl apply -f k8s/configmap.yaml
```

### 2. Create a Secret

`k8s/secret.yaml`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secret
type: Opaque
stringData:
  REDIS_PASSWORD: your-password
```

```bash
kubectl apply -f k8s/secret.yaml
```

### 3. Create the Deployment

`k8s/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: app
  template:
    metadata:
      labels:
        app: app
    spec:
      containers:
        - name: app
          image: app-production:latest
          ports:
            - containerPort: 8000
          envFrom:
            - configMapRef:
                name: app-config
            - secretRef:
                name: app-secret
```

```bash
kubectl apply -f k8s/deployment.yaml
```

### 4. Create the Service

`k8s/service.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: app-service
spec:
  selector:
    app: app
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: LoadBalancer
```

```bash
kubectl apply -f k8s/service.yaml
```

### 5. Verify the Deployment

```bash
# Check running pods
kubectl get pods

# Check services
kubectl get services

# Stream deployment logs
kubectl logs -f deployment/app
```

---

## TLS and HTTPS Setup

### 1. Generate Self-Signed Certificates

```bash
mkdir certs

openssl req -x509 \
  -newkey rsa:4096 \
  -nodes \
  -out certs/cert.pem \
  -keyout certs/key.pem \
  -days 365
```

### 2. Run Uvicorn with TLS

```bash
uvicorn main:app \
  --host 0.0.0.0 \
  --port 8443 \
  --ssl-keyfile certs/key.pem \
  --ssl-certfile certs/cert.pem
```

### 3. Access the Application

```
https://localhost:8443
```

> **Note:** Browsers will display a security warning for self-signed certificates during development. This is expected and can be safely dismissed.

---

## Troubleshooting

### Redis Connection Error

**Error:**

```
ConnectionError: Redis connection failed
```

**Solution:**

```bash
# Verify Redis is running
docker ps

# Check Redis logs
docker logs redis
```

Ensure your `.env` file contains the correct values:

```env
REDIS_HOST=redis
REDIS_PORT=6379
```

---

### YOLO Model Missing

**Error:**

```
FileNotFoundError: YOLO model not found
```

**Solution:**

```bash
# Verify the model exists
ls models/
```

Ensure the model path in `.env` is correct:

```env
YOLO_MODEL_PATH=models/yolov8n.pt
```

If the model is missing, download it before running the application.

---

### Screen Capture Permission Denied

**Error:**

```
Permission denied while capturing screen
```

**Solution:**

**macOS** — Enable screen recording permissions:

```
System Settings → Privacy & Security → Screen Recording
```

**Linux** — Install the required dependency:

```bash
sudo apt install scrot
```

**Windows** — Run the terminal or IDE as Administrator.

---

### Port Already in Use

**Error:**

```
Address already in use
```

**Solution:**

Find the process using the port, then terminate it or switch to a different port.

**Linux / macOS:**

```bash
lsof -i :8000
```

**Windows:**

```bash
netstat -ano | findstr :8000
```

---

### Docker Build Fails

**Error:**

```
Failed building wheel
```

**Solution:**

```bash
# Upgrade pip tooling
pip install --upgrade pip setuptools wheel

# Rebuild without cache
docker-compose build --no-cache
```

---

### Kubernetes Pods in CrashLoopBackOff

**Error:**

```
CrashLoopBackOff
```

**Solution:**

```bash
# Inspect pod logs
kubectl logs <pod-name>

# Describe the pod for events and conditions
kubectl describe pod <pod-name>
```

Common causes to check:

- Missing or incorrect environment variables
- Invalid image name or tag
- Incorrect or missing Secrets
- Port conflicts
- Missing application dependencies

---

## Deployment Best Practices

- Use `.env.example` to document all required configuration keys
- Never commit secrets or credentials to version control
- Use persistent volumes for logs and model files
- Pin dependency versions to ensure reproducible builds
- Add readiness and liveness probes for production Kubernetes workloads
- Monitor logs continuously after every deployment
- Keep Docker images minimal — avoid installing unnecessary packages
- Always use HTTPS in production environments

---

## Additional Resources

- [Docker Documentation](https://docs.docker.com)
- [Kubernetes Documentation](https://kubernetes.io/docs)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [Uvicorn Documentation](https://www.uvicorn.org)