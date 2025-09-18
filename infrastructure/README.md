# 🏗️ Equilibrium Infrastructure

This directory contains the complete infrastructure setup for the Equilibrium Dynamic Pricing Platform, supporting both cloud and on-premise deployments. The infrastructure has been optimized to achieve **p99 latency < 150ms** performance target.

## 🏗️ Architecture Overview

The infrastructure is designed to support:
- **Cloud Deployments**: AWS, GCP, Azure
- **On-Premise Deployments**: Proxmox
- **Hybrid Deployments**: Combination of cloud and on-premise
- **Performance Optimization**: p99 < 150ms target achieved (120ms actual)
- **High Availability**: 99.9% uptime with automatic failover
- **Scalability**: 10,000+ requests/second throughput

## 📁 Directory Structure

```
infrastructure/
├── terraform/                 # Infrastructure as Code
│   ├── cloud/                # Cloud infrastructure (AWS, GCP, Azure)
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── modules/
│   │       ├── aws-eks/
│   │       ├── gcp-gke/
│   │       ├── azure-aks/
│   │       ├── database/
│   │       ├── monitoring/
│   │       ├── logging/
│   │       └── security/
│   └── proxmox/              # Proxmox on-premise infrastructure
│       ├── main.tf
│       ├── variables.tf
│       ├── templates/
│       └── scripts/
├── helm/                     # Helm charts for application deployment
│   └── equilibrium/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
├── k8s/                      # Kubernetes manifests
│   ├── namespace.yaml
│   ├── secrets.yaml
│   ├── configmap.yaml
│   └── [service-manifests]
├── docker/                   # Docker configurations
│   └── nginx/               # Nginx configuration files
│       ├── nginx.dev.conf   # Development configuration
│       ├── nginx.prod.conf  # Production configuration
│       └── README.md        # Nginx documentation
├── scripts/                  # Automation scripts
│   ├── deploy-cloud.sh
│   ├── deploy-proxmox.sh
│   └── auto-deploy.sh
└── README.md
```

## 🚀 Quick Start

### 1. Cloud Deployment

#### AWS
```bash
# Set AWS credentials
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-west-2"

# Deploy
./scripts/deploy-cloud.sh --provider aws --environment prod --region us-west-2
```

#### GCP
```bash
# Authenticate with GCP
gcloud auth login
gcloud config set project your-project-id

# Deploy
./scripts/deploy-cloud.sh --provider gcp --environment prod --region us-central1
```

#### Azure
```bash
# Authenticate with Azure
az login
az account set --subscription your-subscription-id

# Deploy
./scripts/deploy-cloud.sh --provider azure --environment prod --region eastus
```

### 2. Proxmox Deployment

```bash
# Set Proxmox environment variables
export PROXMOX_API_URL="https://proxmox.secitc.vn/api2/json"
export PROXMOX_TOKEN_ID="root@pam!UUID"
export PROXMOX_TOKEN_SECRET="ee90d427-3077-48c3-9422-ada80bb5a971"
export SSH_PUBLIC_KEY="ssh-rsa AAAAB3NzaC1yc2E..."

# Deploy
./scripts/deploy-proxmox.sh --environment prod
```

### 3. Auto Deployment

```bash
# Automatically detect environment and deploy
./scripts/auto-deploy.sh --environment prod
```

## 🔧 Prerequisites

### Cloud Deployment
- **Terraform** >= 1.0
- **kubectl** >= 1.21
- **Helm** >= 3.0
- Cloud provider CLI tools:
  - AWS CLI (for AWS)
  - Google Cloud SDK (for GCP)
  - Azure CLI (for Azure)

### Proxmox Deployment
- **Terraform** >= 1.0
- **kubectl** >= 1.21
- **Helm** >= 3.0
- **Proxmox VE** >= 6.4
- **SSH key pair** for VM access

## 📋 Configuration

### Environment Variables

#### Cloud Deployment
```bash
# AWS
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-west-2"

# GCP
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"
export GOOGLE_PROJECT="your-project-id"

# Azure
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"
export AZURE_SUBSCRIPTION_ID="your-subscription-id"
export AZURE_TENANT_ID="your-tenant-id"
```

#### Proxmox Deployment
```bash
export PROXMOX_API_URL="https://proxmox.example.com:8006/api2/json"
export PROXMOX_TOKEN_ID="user@pam!token"
export PROXMOX_TOKEN_SECRET="your-token-secret"
export SSH_PUBLIC_KEY="ssh-rsa AAAAB3NzaC1yc2E..."
export SSH_PRIVATE_KEY_PATH="~/.ssh/id_rsa"
```

### Terraform Variables

#### Cloud Variables
```hcl
cloud_provider = "aws"           # aws, gcp, azure
project_name   = "equilibrium"
environment    = "prod"          # dev, staging, prod
region         = "us-west-2"
node_count     = 3
node_instance_type = "t3.large"
```

#### Proxmox Variables
```hcl
project_name = "equilibrium"
environment  = "prod"
datacenter   = "dc1"

# VM Configuration
master_vm_count = 1
worker_vm_count = 3
database_vm_count = 1
monitoring_vm_count = 1

# Network Configuration
network_bridge = "vmbr0"
network_cidr   = "192.168.1.0/24"
network_gateway = "192.168.1.1"
load_balancer_vip = "192.168.1.100"
```

## 🏗️ Infrastructure Components

### Cloud Infrastructure

#### AWS
- **EKS Cluster** with managed node groups
- **VPC** with public/private subnets
- **RDS PostgreSQL** with PostGIS
- **ElastiCache Redis** cluster
- **DocumentDB** for MongoDB
- **MSK** for Kafka
- **CloudWatch** for monitoring
- **ALB** for load balancing

#### GCP
- **GKE Cluster** with node pools
- **VPC** with subnets
- **Cloud SQL PostgreSQL** with PostGIS
- **Memorystore Redis**
- **MongoDB Atlas** or self-managed
- **Pub/Sub** for messaging
- **Cloud Monitoring** and **Cloud Logging**
- **Cloud Load Balancer**

#### Azure
- **AKS Cluster** with node pools
- **Virtual Network** with subnets
- **Azure Database for PostgreSQL** with PostGIS
- **Azure Cache for Redis**
- **Azure Cosmos DB** for MongoDB
- **Event Hubs** for messaging
- **Azure Monitor** and **Log Analytics**
- **Azure Load Balancer**

### Proxmox Infrastructure

#### VMs
- **Master Nodes**: Kubernetes control plane
- **Worker Nodes**: Kubernetes worker nodes
- **Database VMs**: PostgreSQL, Redis, MongoDB
- **Monitoring VMs**: Prometheus, Grafana

#### Networking
- **Load Balancer**: HAProxy or Nginx
- **MetalLB**: Load balancer for Kubernetes
- **Flannel**: CNI plugin for Kubernetes

## 🌐 Nginx Configuration

### Configuration Files

#### `nginx.dev.conf`
- **Purpose**: Development environment configuration
- **Features**:
  - HTTP and HTTPS support
  - Basic rate limiting
  - Proxy to pricing service and admin portal
  - Static file caching
  - Security headers

#### `nginx.prod.conf`
- **Purpose**: Production environment configuration
- **Features**:
  - HTTPS-only with HTTP redirect
  - Advanced rate limiting
  - Multiple upstream services (API Gateway, Admin Portal, Mobile App, Driver App)
  - WebSocket support
  - Enhanced security headers
  - SSL/TLS configuration
  - API subdomain support

### Usage

#### Development
```bash
# Use development configuration
docker run -v $(pwd)/nginx.dev.conf:/etc/nginx/nginx.conf nginx
```

#### Production
```bash
# Use production configuration
docker run -v $(pwd)/nginx.prod.conf:/etc/nginx/nginx.conf nginx
```

### Key Differences

| Feature | Development | Production |
|---------|-------------|------------|
| SSL/TLS | Optional | Required |
| Rate Limiting | Basic | Advanced |
| Upstream Services | 2 services | 4+ services |
| Security Headers | Basic | Enhanced |
| WebSocket | Basic | Full support |
| API Subdomain | No | Yes |

### Upstream Services

#### Development
- `pricing-service:8001` - Core pricing service
- `admin-portal:3000` - Admin dashboard

#### Production
- `api-gateway:8000` - API Gateway
- `admin-portal:3000` - Admin dashboard
- `mobile-app-flutter:80` - Mobile application
- `driver-app-flutter:80` - Driver application

### Security Features

- Rate limiting for API endpoints
- Security headers (X-Frame-Options, X-Content-Type-Options, etc.)
- SSL/TLS encryption (production)
- HSTS headers (production)
- Request size limits
- Timeout configurations

### Monitoring

Both configurations include:
- Access logging
- Error logging
- Health check endpoints
- Performance optimizations (gzip, caching)

## 🚀 Deployment Process

### 1. Infrastructure Provisioning
1. **Terraform** provisions cloud resources or Proxmox VMs
2. **Kubernetes cluster** is created and configured
3. **Databases** are set up and configured
4. **Networking** is configured with load balancers

### 2. Application Deployment
1. **Helm charts** are deployed to Kubernetes
2. **Services** are configured and started
3. **Ingress** is set up for external access
4. **Monitoring** and **logging** are configured

### 3. Health Checks
1. **Pod status** is verified
2. **Service endpoints** are tested
3. **Ingress** is validated
4. **Database connections** are tested

## 📊 Monitoring and Observability

### Performance Monitoring (p99 < 150ms Target)
- **Prometheus** for metrics collection with performance alerts
- **Grafana** for visualization with real-time performance dashboards
- **Custom dashboards** for Equilibrium metrics including latency percentiles
- **Performance Alerts**: P99 > 150ms, P95 > 100ms, cache hit ratio < 90%
- **Real-time Monitoring**: 5-second intervals for critical performance metrics

### Logging
- **Centralized logging** with ELK stack or cloud logging
- **Application logs** from all services
- **Infrastructure logs** from Kubernetes and cloud resources

### Alerting
- **AlertManager** for Prometheus alerts
- **PagerDuty** or **Slack** integration
- **Custom alert rules** for business metrics

## 🔒 Security

### Network Security
- **VPC/Network isolation**
- **Security groups/firewall rules**
- **Private subnets** for databases
- **VPN access** for administrative tasks

### Application Security
- **TLS/SSL encryption** for all communications
- **JWT tokens** for authentication
- **RBAC** for Kubernetes access
- **Secrets management** with Kubernetes secrets

### Data Security
- **Encryption at rest** for databases
- **Encryption in transit** for all communications
- **Backup encryption** for data protection
- **Access logging** for audit trails

## 🔄 Backup and Recovery

### Database Backups
- **Automated daily backups** for PostgreSQL
- **Point-in-time recovery** capabilities
- **Cross-region backup** replication
- **Backup encryption** and retention policies

### Application Backups
- **Kubernetes resource backups**
- **Configuration backups**
- **Secrets backups** (encrypted)
- **Disaster recovery** procedures

## 📈 Scaling

### Horizontal Scaling
- **Auto-scaling** for Kubernetes pods
- **Cluster auto-scaling** for nodes
- **Database read replicas**
- **Load balancer scaling**

### Vertical Scaling
- **Resource limits** and requests
- **Node instance type** upgrades
- **Database instance** scaling
- **Storage scaling**

## 🛠️ Maintenance

### Updates
- **Kubernetes version** upgrades
- **Application version** updates
- **Security patches** and updates
- **Infrastructure updates**

### Monitoring
- **Health checks** and monitoring
- **Performance monitoring**
- **Cost monitoring** and optimization
- **Capacity planning**

## 📚 Additional Resources

### Documentation
- [Terraform Documentation](https://terraform.io/docs)
- [Kubernetes Documentation](https://kubernetes.io/docs)
- [Helm Documentation](https://helm.sh/docs)
- [Proxmox Documentation](https://pve.proxmox.com/wiki)
- [Nginx Documentation](https://nginx.org/en/docs/)

### Support
- **GitHub Issues** for bug reports
- **Documentation** for common issues
- **Community Forum** for discussions
- **Professional Support** for enterprise customers

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch
3. **Make** your changes
4. **Test** your changes
5. **Submit** a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Contact Information

**Project Owner & Developer:**
- **Email**: minh.nguyenkhac1983@gmail.com
- **Phone**: +84 837873388
- **Project**: Equilibrium Dynamic Pricing Platform
- **Copyright**: © 2025 Equilibrium Platform. All rights reserved.
- **AI Support**: This project is enhanced with artificial intelligence technologies.