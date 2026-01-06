# Kubernetes Deployment Examples

This directory contains Kubernetes manifests for deploying Sonotheia API integrations in a production environment.

## Overview

The deployment includes:
- **Deployment**: Scalable processor pods with health checks
- **ConfigMap**: Centralized configuration management
- **Secret**: Secure API key storage
- **Service**: Metrics exposure for monitoring
- **PersistentVolumeClaim**: Shared storage for audio files
- **CronJob**: Periodic health checks

## Prerequisites

- Kubernetes cluster (v1.20+)
- kubectl configured to access your cluster
- Docker image built from `examples/python/Dockerfile`

## Quick Start

### 1. Build and Push Docker Image

```bash
cd examples/python
docker build -t sonotheia-python:latest .

# Tag and push to your registry
docker tag sonotheia-python:latest your-registry/sonotheia-python:latest
docker push your-registry/sonotheia-python:latest
```

### 2. Update Configuration

Edit `deployment.yaml` and update:
- Replace `YOUR_API_KEY_HERE` in the Secret with your actual API key
- Update the image reference if using a custom registry
- Adjust resource limits based on your workload

### 3. Deploy to Kubernetes

```bash
kubectl apply -f deployment.yaml
```

### 4. Verify Deployment

```bash
# Check pod status
kubectl get pods -l app=sonotheia-processor

# View logs
kubectl logs -f deployment/sonotheia-processor

# Check health
kubectl exec -it deployment/sonotheia-processor -- python health_check.py
```

## Components

### Deployment

The deployment creates processor pods with:
- **Replicas**: 2 (adjust based on load)
- **Resource Limits**: 512Mi RAM, 500m CPU
- **Health Checks**: Liveness and readiness probes
- **Environment**: Configuration from ConfigMap and Secret

```bash
# Scale deployment
kubectl scale deployment sonotheia-processor --replicas=5

# Update deployment
kubectl set image deployment/sonotheia-processor processor=sonotheia-python:v2
```

### Health Checks

The deployment includes both liveness and readiness probes:

- **Liveness Probe**: Ensures the container is running (restarts if fails)
  - Initial delay: 30s
  - Period: 60s
  - Timeout: 10s

- **Readiness Probe**: Ensures the service is ready to accept traffic
  - Initial delay: 10s
  - Period: 30s
  - Timeout: 10s

### Monitoring

The service exposes metrics on port 9090 for Prometheus scraping:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: sonotheia-processor
spec:
  selector:
    matchLabels:
      app: sonotheia-processor
  endpoints:
  - port: metrics
    interval: 30s
```

### Storage

The deployment uses a PersistentVolumeClaim for shared audio file storage:

```bash
# Check PVC status
kubectl get pvc audio-pvc

# Inspect volume
kubectl describe pv $(kubectl get pvc audio-pvc -o jsonpath='{.spec.volumeName}')
```

## Configuration

### Environment Variables

Configure via ConfigMap (`sonotheia-config`):

| Variable | Default | Description |
|----------|---------|-------------|
| `SONOTHEIA_API_URL` | `https://api.sonotheia.com` | API base URL (API host for Sonotheia.ai) |
| `SONOTHEIA_DEEPFAKE_PATH` | `/v1/voice/deepfake` | Deepfake endpoint |
| `SONOTHEIA_MFA_PATH` | `/v1/mfa/voice/verify` | MFA endpoint |
| `SONOTHEIA_SAR_PATH` | `/v1/reports/sar` | SAR endpoint |

> Tip: copy the repo-root `.env.example` to `.env` and export it to keep cURL and client examples aligned.

### Secrets

API key is stored in Secret (`sonotheia-api-secret`):

```bash
# Update API key
kubectl create secret generic sonotheia-api-secret \
  --from-literal=api-key=YOUR_NEW_KEY \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart pods to pick up new secret
kubectl rollout restart deployment/sonotheia-processor
```

## Operational Considerations

### Security

1. **Use dedicated namespace**:
   ```bash
   kubectl create namespace sonotheia
   kubectl config set-context --current --namespace=sonotheia
   ```

2. **Apply network policies**:
   ```yaml
   apiVersion: networking.k8s.io/v1
   kind: NetworkPolicy
   metadata:
     name: sonotheia-processor-netpol
   spec:
     podSelector:
       matchLabels:
         app: sonotheia-processor
     egress:
     - to:
       - podSelector: {}
       ports:
       - protocol: TCP
         port: 443  # HTTPS only
   ```

3. **Use RBAC**:
   ```bash
   kubectl create serviceaccount sonotheia-processor
   kubectl create role sonotheia-processor-role --verb=get,list --resource=configmaps,secrets
   kubectl create rolebinding sonotheia-processor-binding \
     --role=sonotheia-processor-role \
     --serviceaccount=default:sonotheia-processor
   ```

### High Availability

1. **Pod Disruption Budget**:
   ```yaml
   apiVersion: policy/v1
   kind: PodDisruptionBudget
   metadata:
     name: sonotheia-processor-pdb
   spec:
     minAvailable: 1
     selector:
       matchLabels:
         app: sonotheia-processor
   ```

2. **Anti-affinity rules**:
   ```yaml
   affinity:
     podAntiAffinity:
       preferredDuringSchedulingIgnoredDuringExecution:
       - weight: 100
         podAffinityTerm:
           labelSelector:
             matchLabels:
               app: sonotheia-processor
           topologyKey: kubernetes.io/hostname
   ```

### Monitoring and Alerting

1. **Prometheus metrics**: Already exposed on port 9090
2. **Grafana dashboard**: Create custom dashboard for Sonotheia metrics
3. **Alerting rules**:
   ```yaml
   - alert: SonotheiaHighErrorRate
     expr: rate(sonotheia_api_errors_total[5m]) > 0.1
     for: 5m
     labels:
       severity: warning
     annotations:
       summary: "High error rate in Sonotheia API calls"
   ```

### Autoscaling

Enable horizontal pod autoscaling based on CPU/memory:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: sonotheia-processor-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: sonotheia-processor
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## Troubleshooting

### Pods Not Starting

```bash
# Check pod events
kubectl describe pod -l app=sonotheia-processor

# View logs
kubectl logs -l app=sonotheia-processor --tail=100

# Check resource constraints
kubectl top pods
```

### Health Check Failures

```bash
# Manual health check
kubectl exec -it deployment/sonotheia-processor -- python health_check.py -v

# Check API connectivity
kubectl exec -it deployment/sonotheia-processor -- curl -v https://api.sonotheia.com/health
```

### Performance Issues

```bash
# Check resource usage
kubectl top pods -l app=sonotheia-processor

# Scale up
kubectl scale deployment sonotheia-processor --replicas=5

# Check API latency
kubectl logs -l app=sonotheia-processor | grep latency_ms
```

## Clean Up

```bash
# Delete all resources
kubectl delete -f deployment.yaml

# Or delete individual components
kubectl delete deployment sonotheia-processor
kubectl delete service sonotheia-processor-metrics
kubectl delete configmap sonotheia-config
kubectl delete secret sonotheia-api-secret
kubectl delete pvc audio-pvc
```

## Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Prometheus Operator](https://github.com/prometheus-operator/prometheus-operator)
- [Kubernetes Best Practices](https://kubernetes.io/docs/concepts/configuration/overview/)

## 📌 Essential Reading (Fast Path)

- [Getting Started](../../docs/GETTING_STARTED.md) — 5-minute setup
- [Documentation Index](../../docs/INDEX.md) — find anything quickly
- [Examples Overview](../README.md) — one-command runs for every track
- [Design & Content Audit](../../docs/DESIGN_AUDIT.md) — current quality posture
