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
