# ☸️ Execra Kubernetes Deployment Guide

This guide provides instructions for deploying Execra to a Kubernetes cluster.

## 📋 Prerequisites

- A Kubernetes cluster (e.g., Minikube, GKE, EKS, AKS).
- `kubectl` CLI installed and configured.
- NGINX Ingress Controller installed in the cluster.
- Docker image `execra-api` built and pushed to a container registry.
- (Optional) `cert-manager` for automatic TLS certificate management.

## 🏗️ 1. Building the Docker Image

First, build the Docker image using the provided `Dockerfile` and push it to your registry:

```bash
# Build the image
docker build -t <your-registry>/execra-api:latest .

# Push the image
docker push <your-registry>/execra-api:latest
```

> [!NOTE]
> Ensure you update the image path in `k8s/deployment.yaml` to match your registry.

## 🔐 2. Configuring Secrets

Execra requires API keys for LLM providers. These are managed via Kubernetes Secrets.

1. Open `k8s/secret.yaml`.
2. Replace the placeholder values for `OPENAI_API_KEY` and `GEMINI_API_KEY` with your actual keys.
3. **Important:** Never commit the file with real secrets to version control.

## 🚀 3. Deploying to Kubernetes

Apply the manifests in the following order (or apply the entire directory):

```bash
# Apply the entire k8s directory
kubectl apply -f k8s/
```

This will create:
- The `execra` namespace.
- ConfigMap and Secrets.
- Redis deployment and service.
- Execra API deployment (2 replicas) and service.
- Ingress for external access.

## ✅ 4. Verifying the Deployment

Check the status of the resources:

```bash
# Check pods
kubectl -n execra get pods

# Check services
kubectl -n execra get svc

# Check ingress
kubectl -n execra get ingress

# Check logs
kubectl -n execra logs -l app=execra-api --tail=50
```

## 🌐 5. Configuring TLS

The provided `k8s/ingress.yaml` is configured for TLS. 

- **cert-manager:** If using `cert-manager`, add the appropriate annotations to the Ingress (e.g., `cert-manager.io/cluster-issuer: letsencrypt-prod`).
- **Manual:** Create a TLS secret manually:
  ```bash
  kubectl -n execra create secret tls execra-tls-cert --cert=path/to/tls.crt --key=path/to/tls.key
  ```

## 📈 6. Scaling

To scale the API deployment:

```bash
kubectl -n execra scale deployment execra-api --replicas=4
```

## 🔄 7. Updating the Image

To update the application image:

```bash
kubectl -n execra set image deployment/execra-api execra-api=<your-registry>/execra-api:v1.1.0
```

## 🗑️ 8. Teardown

To remove all resources:

```bash
kubectl delete -f k8s/
```
# Execra Deployment Guide

This guide explains how to set up and deploy Execra in different environments, including local development, Docker, and Kubernetes-based deployments.

For details about the internal modules and subsystem relationships, see [`architecture.md`](./architecture.md).

## Table of Contents

* [Prerequisites](#prerequisites)
* [Architecture Overview](#architecture-overview)
* [Local Development](#local-development)
* [Docker Compose Deployment](#docker-compose-deployment)
* [Docker Production Deployment](#docker-production-deployment)
* [Kubernetes Deployment](#kubernetes-deployment)
* [TLS Setup](#tls-setup)
* [Troubleshooting](#troubleshooting)
* [Production Recommendations](#production-recommendations)

## Prerequisites

Before running Execra, install the following tools on your system.

| Tool           | Version       |
| -------------- | ------------- |
| Python         | 3.10+         |
| Node.js        | 18+           |
| Docker         | Latest stable |
| Docker Compose | Latest stable |
| Redis          | 6+            |
| FFmpeg         | Latest        |
| Git            | Latest        |

You can verify the installations using:

```bash
python --version
node --version
docker --version
docker compose --version
redis-server --version
ffmpeg -version
git --version
```

## Architecture Overview

Execra uses multiple backend and frontend components that work together in real time:
* FastAPI backend services
* Frontend overlay and guidance panel
* Redis-based temporary storage
* OCR and runtime analysis engines
* YOLO-based object detection models

Some important project directories:

```text
core/        -> Backend logic and AI systems
frontend/    -> Overlay UI and frontend components
api/         -> REST and WebSocket APIs
models/      -> YOLO and custom AI model weights
tests/       -> Unit, integration, and e2e tests
```

For complete architecture details, refer to [`architecture.md`](./architecture.md).

## Local Development

### 1. Clone the Repository

```bash
git clone https://github.com/sahoo-tech/Execra.git
cd Execra
```

### 2. Create a Virtual Environment

#### Linux/macOS

```bash
python -m venv venv
source venv/bin/activate
```

#### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

Install development dependencies if needed:

```bash
pip install -r requirements-dev.txt
```

### 4. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

### 5. Configure Environment Variables

Create a local `.env` file:

#### Linux/macOS

```bash
cp .env.example .env
```

#### Windows

```bash
copy .env.example .env
```

Example `.env` configuration:

```env
OPENAI_API_KEY=your_api_key
REDIS_HOST=localhost
REDIS_PORT=6379
YOLO_MODEL_PATH=models/yolo/yolov8.pt
DEBUG=True
```

**Never commit `.env` files or API keys to GitHub.**

### 6. Start Redis

#### Linux

```bash
sudo service redis-server start
```

#### Using Docker

```bash
docker run -d -p 6379:6379 redis
```

Verify Redis is running:

```bash
redis-cli ping
```

Expected output:

```text
PONG
```

*If Redis is already installed locally, you may not need the Docker container.*

### 7. Download YOLO Model Weights

```bash
python scripts/download_models.py
```

The first download may take a few minutes depending on your internet connection.

The model files are usually stored inside:

```text
models/yolo/
```

### 8. Run the Backend Server

```bash
python main.py
```

The backend API should start at:

```text
http://localhost:8000
```

### 9. Run the Frontend Overlay

Open another terminal:

```bash
cd frontend
npm run dev
```

Frontend development server:

```text
http://localhost:3000
```

## Docker Compose Deployment

Docker Compose is useful for running multiple services together during development.

Start all services:

```bash
docker compose up --build
```

Run in detached mode:

```bash
docker compose up -d
```

Stop containers:

```bash
docker compose down
```

Check running containers:

```bash
docker ps
```

### Example Environment Variables

```env
REDIS_HOST=redis
REDIS_PORT=6379
DEBUG=False
```

### Example Volume Mounts

```yaml
volumes:
  - ./models:/app/models
  - ./logs:/app/logs
```

This helps persist downloaded models and application logs.

### Default Ports

| Service          | Port |
| ---------------- | ---- |
| Backend API      | 8000 |
| Frontend Overlay | 3000 |
| Redis            | 6379 |

## Docker Production Deployment

### Example Multi-Stage Dockerfile

```dockerfile
FROM python:3.11-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /app /app

EXPOSE 8000

CMD ["python", "main.py"]
```

*This is a simple example production setup and may be adjusted depending on deployment requirements.*

### Build the Docker Image

```bash
docker build -t execra:latest .
```

### Run the Production Container

```bash
docker run -d \
  --name execra \
  -p 8000:8000 \
  --env-file .env \
  execra:latest
```

### View Container Logs

```bash
docker logs execra
```

## Kubernetes Deployment

*Kubernetes manifests can be stored inside the `k8s/` directory.*

Apply manifests:

```bash
kubectl apply -f k8s/
```

Verify resources:

```bash
kubectl get pods
kubectl get services
```

### Example ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: execra-config
data:
  REDIS_HOST: redis
  REDIS_PORT: "6379"
```

Apply the ConfigMap:

```bash
kubectl apply -f k8s/configmap.yaml
```

### Example Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: execra-secret
type: Opaque
stringData:
  OPENAI_API_KEY: your_api_key
```

Apply the Secret:

```bash
kubectl apply -f k8s/secret.yaml
```

### Restart Deployment

```bash
kubectl rollout restart deployment execra
```

### View Pod Logs

```bash
kubectl logs <pod-name>
```

## TLS Setup

### Generate Self-Signed Certificates

```bash
openssl req -x509 -newkey rsa:4096 \
  -keyout key.pem \
  -out cert.pem \
  -days 365 \
  -nodes
```

Generated files:

```text
key.pem
cert.pem
```

### Run Uvicorn with TLS

```bash
uvicorn main:app \
  --host 0.0.0.0 \
  --port 443 \
  --ssl-keyfile=key.pem \
  --ssl-certfile=cert.pem
```

Secure endpoint:

```text
https://localhost
```

*Self-signed certificates should only be used for local development or testing.*

## Troubleshooting

### Redis Not Found

#### Error

```text
Connection refused to Redis
```

#### Fix

Start Redis manually:

```bash
sudo service redis-server start
```

Or run Redis using Docker:

```bash
docker run -d -p 6379:6379 redis
```

Verify the connection:

```bash
redis-cli ping
```

### YOLO Model Missing

#### Error

```text
FileNotFoundError: YOLO model not found
```

#### Fix

Download model weights:

```bash
python scripts/download_models.py
```

Check whether the model exists inside:

```text
models/yolo/
```

Verify the `.env` path:

```env
YOLO_MODEL_PATH=models/yolo/yolov8.pt
```

### Missing Environment Variables

#### Error

```text
Environment variable OPENAI_API_KEY not set
```

#### Fix

Create a `.env` file:

```bash
cp .env.example .env
```

Then update the required variables before starting the application.

### Screen Capture Permission Denied

#### Linux

Make sure screen recording permissions are enabled for your desktop session.

#### macOS

Enable permissions from:

```text
System Settings → Privacy & Security → Screen Recording
```

#### Windows

Run the terminal or IDE as Administrator.

### Docker Daemon Not Running

#### Error

```text
Cannot connect to the Docker daemon
```

#### Fix

Start Docker:

```bash
sudo systemctl start docker
```

### Docker Permission Denied

#### Error

```text
permission denied while trying to connect to the Docker daemon socket
```

#### Fix

Add your user to the Docker group:

```bash
sudo usermod -aG docker $USER
```

Log out and log back in after running the command.

### Port Already in Use

#### Error

```text
Address already in use
```

#### Fix

Find the process using the port:

```bash
lsof -i :8000
```

Kill the process:

```bash
kill -9 <PID>
```

### FFmpeg Not Installed

#### Error

```text
ffmpeg: command not found
```

#### Fix

#### Ubuntu/Debian

```bash
sudo apt install ffmpeg
```

#### macOS

```bash
brew install ffmpeg
```

#### Windows

Install FFmpeg manually and add it to the system PATH.

Verify installation:

```bash
ffmpeg -version
```

### Frontend Dependency Issues

#### Error

```text
npm: command not found
```

#### Fix

#### Ubuntu/Debian

```bash
sudo apt install nodejs npm
```

Verify installation:

```bash
node --version
npm --version
```

### Kubernetes CrashLoopBackOff

#### Error

```text
CrashLoopBackOff
```

#### Fix

Inspect pod logs and events:

```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

Common causes:
* Missing environment variables
* Invalid image name
* Redis connection failure
* Missing model files

## Production Recommendations

* Use trusted TLS certificates in production environments.
* Store secrets using Kubernetes Secrets or external secret managers.
* Avoid exposing Redis directly to the public internet.
* Mount persistent storage for logs and model files.
* Rotate API keys regularly.
* Keep dependencies updated for security fixes.
* Never commit `.env` files or secrets to version control.
