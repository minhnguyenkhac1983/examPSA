# Kubernetes Deployment Guide

## Overview
This guide provides comprehensive instructions for deploying the Equilibrium Dynamic Pricing Platform on Kubernetes, including setup, configuration, and operational procedures.

## Prerequisites

### Required Tools
- **kubectl**: Kubernetes command-line tool
- **Helm**: Kubernetes package manager
- **Docker**: Container runtime
- **kubectx**: Kubernetes context switcher (optional)

### Cluster Requirements
- **Kubernetes Version**: 1.21 or higher
- **Node Count**: Minimum 3 worker nodes
- **CPU**: 8 cores per node minimum
- **Memory**: 16GB RAM per node minimum
- **Storage**: 100GB per node minimum
- **Network**: CNI plugin (Calico, Flannel, or similar)

## Cluster Setup

### 1. Create Namespace
```bash
# Create equilibrium namespace
kubectl create namespace equilibrium

# Set default namespace
kubectl config set-context --current --namespace=equilibrium
```

### 2. Configure RBAC
```yaml
# rbac.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: equilibrium-sa
  namespace: equilibrium
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: equilibrium-role
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps", "secrets"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: equilibrium-binding
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: equilibrium-role
subjects:
- kind: ServiceAccount
  name: equilibrium-sa
  namespace: equilibrium
```

### 3. Apply RBAC Configuration
```bash
kubectl apply -f rbac.yaml
```

## Database Deployment

### 1. PostgreSQL with PostGIS
```yaml
# postgres-deployment.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: equilibrium
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgis/postgis:13-3.1
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_DB
          value: "equilibrium"
        - name: POSTGRES_USER
          value: "equilibrium_user"
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secrets
              key: password
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - equilibrium_user
            - -d
            - equilibrium
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - pg_isready
            - -U
            - equilibrium_user
            - -d
            - equilibrium
          initialDelaySeconds: 5
          periodSeconds: 5
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 20Gi
---
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
  namespace: equilibrium
spec:
  selector:
    app: postgres
  ports:
  - protocol: TCP
    port: 5432
    targetPort: 5432
  type: ClusterIP
```

### 2. Redis Cluster
```yaml
# redis-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: equilibrium
spec:
  replicas: 3
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        command:
        - redis-server
        - --requirepass
        - $(REDIS_PASSWORD)
        - --cluster-enabled
        - "yes"
        - --cluster-config-file
        - /data/nodes.conf
        - --cluster-node-timeout
        - "5000"
        - --appendonly
        - "yes"
        env:
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: redis-secrets
              key: password
        volumeMounts:
        - name: redis-storage
          mountPath: /data
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          exec:
            command:
            - redis-cli
            - ping
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - redis-cli
            - ping
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: redis-storage
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: redis-service
  namespace: equilibrium
spec:
  selector:
    app: redis
  ports:
  - protocol: TCP
    port: 6379
    targetPort: 6379
  type: ClusterIP
```

### 3. MongoDB
```yaml
# mongodb-deployment.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mongodb
  namespace: equilibrium
spec:
  serviceName: mongodb
  replicas: 1
  selector:
    matchLabels:
      app: mongodb
  template:
    metadata:
      labels:
        app: mongodb
    spec:
      containers:
      - name: mongodb
        image: mongo:5.0
        ports:
        - containerPort: 27017
        env:
        - name: MONGO_INITDB_ROOT_USERNAME
          value: "equilibrium_user"
        - name: MONGO_INITDB_ROOT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: mongodb-secrets
              key: password
        - name: MONGO_INITDB_DATABASE
          value: "equilibrium_analytics"
        volumeMounts:
        - name: mongodb-storage
          mountPath: /data/db
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          exec:
            command:
            - mongosh
            - --eval
            - "db.adminCommand('ping')"
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          exec:
            command:
            - mongosh
            - --eval
            - "db.adminCommand('ping')"
          initialDelaySeconds: 5
          periodSeconds: 5
  volumeClaimTemplates:
  - metadata:
      name: mongodb-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
---
apiVersion: v1
kind: Service
metadata:
  name: mongodb-service
  namespace: equilibrium
spec:
  selector:
    app: mongodb
  ports:
  - protocol: TCP
    port: 27017
    targetPort: 27017
  type: ClusterIP
```

## Application Deployment

### 1. API Gateway
```yaml
# api-gateway-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
  namespace: equilibrium
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api-gateway
  template:
    metadata:
      labels:
        app: api-gateway
    spec:
      containers:
      - name: api-gateway
        image: equilibrium/api-gateway:latest
        ports:
        - containerPort: 8000
        env:
        - name: API_GATEWAY_PORT
          value: "8000"
        - name: CORS_ORIGINS
          value: "https://yourdomain.com,https://admin.yourdomain.com"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: api-gateway-service
  namespace: equilibrium
spec:
  selector:
    app: api-gateway
  ports:
  - protocol: TCP
    port: 8000
    targetPort: 8000
  type: LoadBalancer
```

### 2. Pricing Service
```yaml
# pricing-service-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pricing-service
  namespace: equilibrium
spec:
  replicas: 5
  selector:
    matchLabels:
      app: pricing-service
  template:
    metadata:
      labels:
        app: pricing-service
    spec:
      containers:
      - name: pricing-service
        image: equilibrium/pricing-service:latest
        ports:
        - containerPort: 8001
        env:
        - name: PRICING_SERVICE_PORT
          value: "8001"
        - name: REDIS_HOST
          value: "redis-service"
        - name: POSTGRES_HOST
          value: "postgres-service"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: pricing-service
  namespace: equilibrium
spec:
  selector:
    app: pricing-service
  ports:
  - protocol: TCP
    port: 8001
    targetPort: 8001
  type: ClusterIP
```

## Monitoring Setup

### 1. Prometheus
```yaml
# prometheus-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prometheus
  namespace: equilibrium
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prometheus
  template:
    metadata:
      labels:
        app: prometheus
    spec:
      containers:
      - name: prometheus
        image: prom/prometheus:latest
        ports:
        - containerPort: 9090
        volumeMounts:
        - name: prometheus-config
          mountPath: /etc/prometheus/prometheus.yml
          subPath: prometheus.yml
        - name: prometheus-storage
          mountPath: /prometheus
        command:
        - '--config.file=/etc/prometheus/prometheus.yml'
        - '--storage.tsdb.path=/prometheus'
        - '--web.console.libraries=/etc/prometheus/console_libraries'
        - '--web.console.templates=/etc/prometheus/consoles'
        - '--storage.tsdb.retention.time=200h'
        - '--web.enable-lifecycle'
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /-/healthy
            port: 9090
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /-/ready
            port: 9090
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: prometheus-config
        configMap:
          name: prometheus-config
      - name: prometheus-storage
        persistentVolumeClaim:
          claimName: prometheus-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: prometheus
  namespace: equilibrium
spec:
  selector:
    app: prometheus
  ports:
  - protocol: TCP
    port: 9090
    targetPort: 9090
  type: ClusterIP
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: prometheus-pvc
  namespace: equilibrium
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
```

### 2. Grafana
```yaml
# grafana-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: grafana
  namespace: equilibrium
spec:
  replicas: 1
  selector:
    matchLabels:
      app: grafana
  template:
    metadata:
      labels:
        app: grafana
    spec:
      containers:
      - name: grafana
        image: grafana/grafana:latest
        ports:
        - containerPort: 3000
        env:
        - name: GF_SECURITY_ADMIN_PASSWORD
          valueFrom:
            secretKeyRef:
              name: grafana-secrets
              key: admin-password
        - name: GF_INSTALL_PLUGINS
          value: "grafana-piechart-panel"
        volumeMounts:
        - name: grafana-storage
          mountPath: /var/lib/grafana
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /api/health
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/health
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: grafana-storage
        persistentVolumeClaim:
          claimName: grafana-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: grafana
  namespace: equilibrium
spec:
  selector:
    app: grafana
  ports:
  - protocol: TCP
    port: 3000
    targetPort: 3000
  type: ClusterIP
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: grafana-pvc
  namespace: equilibrium
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
```

## Secrets Management

### 1. Create Secrets
```bash
# PostgreSQL secrets
kubectl create secret generic postgres-secrets \
  --from-literal=password=secure_password_2025 \
  --namespace=equilibrium

# Redis secrets
kubectl create secret generic redis-secrets \
  --from-literal=password=secure_redis_password_2025 \
  --namespace=equilibrium

# MongoDB secrets
kubectl create secret generic mongodb-secrets \
  --from-literal=password=secure_mongodb_password_2025 \
  --namespace=equilibrium

# Auth secrets
kubectl create secret generic auth-secrets \
  --from-literal=jwt-secret=equilibrium-jwt-secret-key-production-2025-very-secure \
  --namespace=equilibrium

# Grafana secrets
kubectl create secret generic grafana-secrets \
  --from-literal=admin-password=secure_grafana_password_2025 \
  --namespace=equilibrium
```

### 2. ConfigMaps
```yaml
# prometheus-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: equilibrium
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
      evaluation_interval: 15s

    rule_files:
      # - "first_rules.yml"
      # - "second_rules.yml"

    scrape_configs:
      - job_name: 'prometheus'
        static_configs:
          - targets: ['localhost:9090']

      - job_name: 'api-gateway'
        static_configs:
          - targets: ['api-gateway-service:8000']
        metrics_path: '/metrics'
        scrape_interval: 5s

      - job_name: 'pricing-service'
        static_configs:
          - targets: ['pricing-service:8001']
        metrics_path: '/metrics'
        scrape_interval: 5s
```

## Deployment Scripts

### 1. Deploy All Services
```bash
#!/bin/bash
# deploy-all.sh

echo "🚀 Starting Equilibrium Kubernetes Deployment..."

# Create namespace
kubectl create namespace equilibrium --dry-run=client -o yaml | kubectl apply -f -

# Apply secrets
kubectl apply -f infrastructure/k8s/secrets.yaml

# Apply configmaps
kubectl apply -f infrastructure/k8s/configmap.yaml

# Deploy databases
kubectl apply -f infrastructure/k8s/postgres.yaml
kubectl apply -f infrastructure/k8s/redis.yaml
kubectl apply -f infrastructure/k8s/mongodb.yaml

# Wait for databases
kubectl wait --for=condition=ready pod -l app=postgres -n equilibrium --timeout=300s
kubectl wait --for=condition=ready pod -l app=redis -n equilibrium --timeout=300s
kubectl wait --for=condition=ready pod -l app=mongodb -n equilibrium --timeout=300s

# Deploy backend services
kubectl apply -f infrastructure/k8s/api-gateway.yaml
kubectl apply -f infrastructure/k8s/pricing-service.yaml
kubectl apply -f infrastructure/k8s/analytics-service.yaml

# Wait for backend services
kubectl wait --for=condition=ready pod -l app=api-gateway -n equilibrium --timeout=300s
kubectl wait --for=condition=ready pod -l app=pricing-service -n equilibrium --timeout=300s

# Deploy monitoring
kubectl apply -f infrastructure/k8s/prometheus.yaml
kubectl apply -f infrastructure/k8s/grafana.yaml

echo "✅ Deployment completed successfully!"
```

### 2. Health Check Script
```bash
#!/bin/bash
# health-check.sh

echo "🔍 Checking Equilibrium system health..."

# Check pods
kubectl get pods -n equilibrium

# Check services
kubectl get services -n equilibrium

# Check deployments
kubectl get deployments -n equilibrium

# Check logs
echo "📋 Recent logs from API Gateway:"
kubectl logs -l app=api-gateway -n equilibrium --tail=10

echo "📋 Recent logs from Pricing Service:"
kubectl logs -l app=pricing-service -n equilibrium --tail=10

# Check resource usage
echo "📊 Resource usage:"
kubectl top pods -n equilibrium
kubectl top nodes
```

## Scaling and Auto-scaling

### 1. Horizontal Pod Autoscaler
```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: pricing-service-hpa
  namespace: equilibrium
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: pricing-service
  minReplicas: 3
  maxReplicas: 20
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

### 2. Vertical Pod Autoscaler
```yaml
# vpa.yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: pricing-service-vpa
  namespace: equilibrium
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: pricing-service
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: pricing-service
      minAllowed:
        cpu: 250m
        memory: 256Mi
      maxAllowed:
        cpu: 1000m
        memory: 1Gi
```

## Troubleshooting

### 1. Common Issues

#### Pod Not Starting
```bash
# Check pod status
kubectl describe pod <pod-name> -n equilibrium

# Check logs
kubectl logs <pod-name> -n equilibrium

# Check events
kubectl get events -n equilibrium --sort-by='.lastTimestamp'
```

#### Service Not Accessible
```bash
# Check service endpoints
kubectl get endpoints -n equilibrium

# Test service connectivity
kubectl run test-pod --image=busybox -it --rm -- nslookup <service-name>

# Check service configuration
kubectl describe service <service-name> -n equilibrium
```

#### Database Connection Issues
```bash
# Check database pods
kubectl get pods -l app=postgres -n equilibrium

# Check database logs
kubectl logs -l app=postgres -n equilibrium

# Test database connectivity
kubectl exec -it <postgres-pod> -n equilibrium -- psql -U equilibrium_user -d equilibrium
```

### 2. Performance Issues

#### High CPU Usage
```bash
# Check resource usage
kubectl top pods -n equilibrium

# Check node resources
kubectl top nodes

# Scale up if needed
kubectl scale deployment pricing-service --replicas=10 -n equilibrium
```

#### High Memory Usage
```bash
# Check memory usage
kubectl top pods -n equilibrium --sort-by=memory

# Check memory limits
kubectl describe pod <pod-name> -n equilibrium | grep -A 5 "Limits:"

# Adjust memory limits if needed
kubectl patch deployment pricing-service -n equilibrium -p '{"spec":{"template":{"spec":{"containers":[{"name":"pricing-service","resources":{"limits":{"memory":"2Gi"}}}]}}}}'
```

## Backup and Recovery

### 1. Database Backup
```bash
#!/bin/bash
# backup-databases.sh

# PostgreSQL backup
kubectl exec -it $(kubectl get pods -l app=postgres -n equilibrium -o jsonpath='{.items[0].metadata.name}') -n equilibrium -- pg_dump -U equilibrium_user equilibrium > postgres-backup-$(date +%Y%m%d).sql

# MongoDB backup
kubectl exec -it $(kubectl get pods -l app=mongodb -n equilibrium -o jsonpath='{.items[0].metadata.name}') -n equilibrium -- mongodump --username equilibrium_user --password secure_mongodb_password_2025 --db equilibrium_analytics --out /tmp/backup
kubectl cp equilibrium/$(kubectl get pods -l app=mongodb -n equilibrium -o jsonpath='{.items[0].metadata.name}'):/tmp/backup ./mongodb-backup-$(date +%Y%m%d)
```

### 2. Configuration Backup
```bash
#!/bin/bash
# backup-configs.sh

# Backup all configurations
kubectl get all -n equilibrium -o yaml > equilibrium-backup-$(date +%Y%m%d).yaml

# Backup secrets (base64 encoded)
kubectl get secrets -n equilibrium -o yaml > equilibrium-secrets-backup-$(date +%Y%m%d).yaml

# Backup configmaps
kubectl get configmaps -n equilibrium -o yaml > equilibrium-configmaps-backup-$(date +%Y%m%d).yaml
```

This comprehensive Kubernetes deployment guide provides all the necessary steps to deploy, monitor, and maintain the Equilibrium Dynamic Pricing Platform in a production Kubernetes environment.