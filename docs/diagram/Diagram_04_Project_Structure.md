# Diagram 04: Project Structure

## Overview
This diagram visualizes the complete project structure of the Equilibrium Dynamic Pricing Platform, showing the organization of directories, files, and their relationships.

## Project Structure Visualization

```mermaid
graph TD
    ROOT[equilibrium/] --> BACKEND[backend/]
    ROOT --> FRONTEND[frontend/]
    ROOT --> INFRA[infrastructure/]
    ROOT --> DATA[data/]
    ROOT --> SCRIPTS[scripts/]
    ROOT --> DOCS[docs/]
    ROOT --> TESTS[tests/]
    ROOT --> CONFIG[Configuration Files]
    
    %% Backend Services
    BACKEND --> API_GW[api-gateway/]
    BACKEND --> PRICING[pricing-service/]
    BACKEND --> ANALYTICS[analytics-service/]
    BACKEND --> GEOSPATIAL[geospatial-service/]
    BACKEND --> STREAM[stream-processor/]
    BACKEND --> WEBSOCKET[websocket-service/]
    BACKEND --> AUTH[auth-service/]
    BACKEND --> ML[ml-pricing-service/]
    BACKEND --> NOTIF[notification-service/]
    BACKEND --> ADV_ANALYTICS[advanced-analytics-service/]
    BACKEND --> I18N[i18n-service/]
    
    %% Frontend Applications
    FRONTEND --> ADMIN[admin-portal/]
    FRONTEND --> MOBILE[mobile-app/]
    FRONTEND --> DRIVER[driver-app/]
    
    %% Mobile App Structure
    MOBILE --> MOBILE_RN[mobile-app/react-app/]
    MOBILE --> MOBILE_FLUTTER[mobile-app/flutter-app/]
    
    %% Driver App Structure
    DRIVER --> DRIVER_RN[driver-app/react-app/]
    DRIVER --> DRIVER_FLUTTER[driver-app/flutter-app/]
    
    %% Infrastructure
    INFRA --> DOCKER[docker/]
    INFRA --> K8S[k8s/]
    INFRA --> MONITORING[monitoring/]
    INFRA --> NGINX[nginx/]
    INFRA --> TERRAFORM[terraform/]
    INFRA --> HELM[helm/]
    
    %% Data
    DATA --> POSTGRES[postgres/]
    DATA --> MONGODB[mongodb/]
    DATA --> REDIS[redis/]
    
    %% Scripts
    SCRIPTS --> SETUP[setup/]
    SCRIPTS --> DEPLOY[deploy/]
    SCRIPTS --> BACKUP[backup/]
    SCRIPTS --> DEMO[demo/]
    SCRIPTS --> TEST[test/]
    SCRIPTS --> MONITORING_SCRIPTS[monitoring/]
    
    %% Documentation
    DOCS --> API_DOCS[api/]
    DOCS --> ARCH_DOCS[architecture/]
    DOCS --> DEPLOY_DOCS[deployment/]
    DOCS --> DIAGRAMS[diagrams/]
    
    %% Tests
    TESTS --> UNIT[unit/]
    TESTS --> INTEGRATION[integration/]
    TESTS --> E2E[e2e/]
    
    %% Configuration Files
    CONFIG --> DOCKER_COMPOSE[docker-compose.yml]
    CONFIG --> DOCKER_PROD[docker-compose.prod.yml]
    CONFIG --> ENV[env.example]
    CONFIG --> ENV_PROD[env.prod.example]
    CONFIG --> MAKEFILE[Makefile]
    CONFIG --> REQUIREMENTS[requirements.txt]
    
    %% Styling
    classDef backendService fill:#e8f5e8
    classDef frontendApp fill:#e3f2fd
    classDef infrastructure fill:#fff3e0
    classDef data fill:#f3e5f5
    classDef scripts fill:#fce4ec
    classDef docs fill:#f1f8e9
    classDef tests fill:#e0f2f1
    classDef config fill:#fff8e1
    
    class API_GW,PRICING,ANALYTICS,GEOSPATIAL,STREAM,WEBSOCKET,AUTH,ML,NOTIF,ADV_ANALYTICS,I18N backendService
    class ADMIN,MOBILE,DRIVER,MOBILE_RN,MOBILE_FLUTTER,DRIVER_RN,DRIVER_FLUTTER frontendApp
    class DOCKER,K8S,MONITORING,NGINX,TERRAFORM,HELM infrastructure
    class POSTGRES,MONGODB,REDIS data
    class SETUP,DEPLOY,BACKUP,DEMO,TEST,MONITORING_SCRIPTS scripts
    class API_DOCS,ARCH_DOCS,DEPLOY_DOCS,DIAGRAMS docs
    class UNIT,INTEGRATION,E2E tests
    class DOCKER_COMPOSE,DOCKER_PROD,ENV,ENV_PROD,MAKEFILE,REQUIREMENTS config
```

## Detailed Directory Structure

### Backend Services Structure

```mermaid
graph TD
    subgraph "Backend Services"
        subgraph "API Gateway"
            AG_APP[app.py]
            AG_REQ[requirements.txt]
            AG_DOCKER[Dockerfile]
        end
        
        subgraph "Pricing Service"
            PS_APP[app.py]
            PS_PROD[app_prod.py]
            PS_SIMPLE[simple_app.py]
            PS_REQ[requirements.txt]
            PS_DOCKER[Dockerfile]
            PS_DOCKER_PROD[Dockerfile.prod]
        end
        
        subgraph "Analytics Service"
            AS_APP[analytics_app.py]
            AS_REQ[requirements.txt]
            AS_DOCKER[Dockerfile]
        end
        
        subgraph "Geospatial Service"
            GS_APP[app.py]
            GS_REQ[requirements.txt]
            GS_DOCKER[Dockerfile]
        end
        
        subgraph "Stream Processor"
            SP_APP[app.py]
            SP_REQ[requirements.txt]
            SP_DOCKER[Dockerfile]
        end
        
        subgraph "WebSocket Service"
            WS_APP[websocket_app.py]
            WS_REQ[requirements.txt]
            WS_DOCKER[Dockerfile]
        end
        
        subgraph "Auth Service"
            AUTH_APP[auth_app.py]
            AUTH_REQ[requirements.txt]
            AUTH_DOCKER[Dockerfile]
        end
        
        subgraph "ML Pricing Service"
            ML_APP[ml_pricing_app.py]
            ML_REQ[requirements.txt]
            ML_DOCKER[Dockerfile]
        end
        
        subgraph "Notification Service"
            NS_APP[notification_app.py]
            NS_REQ[requirements.txt]
            NS_DOCKER[Dockerfile]
        end
        
        subgraph "Advanced Analytics"
            AAS_APP[advanced_analytics_app.py]
            AAS_REQ[requirements.txt]
            AAS_DOCKER[Dockerfile]
        end
        
        subgraph "i18n Service"
            I18N_APP[i18n_app.py]
            I18N_REQ[requirements.txt]
            I18N_DOCKER[Dockerfile]
        end
    end
```

### Frontend Applications Structure

```mermaid
graph TD
    subgraph "Frontend Applications"
        subgraph "Admin Portal"
            AP_PACKAGE[package.json]
            AP_PACKAGE_LOCK[package-lock.json]
            AP_DOCKER[Dockerfile]
            AP_DOCKER_PROD[Dockerfile.prod]
            AP_PUBLIC[public/]
            AP_SRC[src/]
            AP_NODE[node_modules/]
        end
        
        subgraph "Mobile App"
            subgraph "React Native"
                MA_RN_APP[App.js]
                MA_RN_PACKAGE[package.json]
                MA_RN_METRO[metro.config.js]
                MA_RN_README[README.md]
            end
            
            subgraph "Flutter"
                MA_FLUTTER_MAIN[main.dart]
                MA_FLUTTER_PUBSPEC[pubspec.yaml]
                MA_FLUTTER_ANALYSIS[analysis_options.yaml]
                MA_FLUTTER_README[README.md]
            end
        end
        
        subgraph "Driver App"
            subgraph "React Native"
                DA_RN_APP[App.js]
                DA_RN_PACKAGE[package.json]
                DA_RN_METRO[metro.config.js]
                DA_RN_README[README.md]
            end
            
            subgraph "Flutter"
                DA_FLUTTER_MAIN[main.dart]
                DA_FLUTTER_PUBSPEC[pubspec.yaml]
                DA_FLUTTER_ANALYSIS[analysis_options.yaml]
                DA_FLUTTER_README[README.md]
            end
        end
    end
```

### Infrastructure Structure

```mermaid
graph TD
    subgraph "Infrastructure"
        subgraph "Docker"
            DOCKER_GATEWAY[Dockerfile.gateway]
            DOCKER_NGINX[nginx/]
        end
        
        subgraph "Kubernetes"
            K8S_NAMESPACE[namespace.yaml]
            K8S_CONFIGMAP[configmap.yaml]
            K8S_SECRETS[secrets.yaml]
            K8S_API_GW[api-gateway.yaml]
            K8S_PRICING[pricing-service.yaml]
            K8S_ANALYTICS[analytics-service.yaml]
            K8S_GEOSPATIAL[geospatial-service.yaml]
            K8S_STREAM[stream-processor.yaml]
            K8S_WEBSOCKET[websocket-service.yaml]
            K8S_AUTH[auth-service.yaml]
            K8S_ML[ml-pricing-service.yaml]
            K8S_NOTIF[notification-service.yaml]
            K8S_ADV_ANALYTICS[advanced-analytics-service.yaml]
            K8S_I18N[i18n-service.yaml]
            K8S_ADMIN[admin-portal.yaml]
            K8S_MOBILE[mobile-app.yaml]
            K8S_DRIVER[driver-app.yaml]
            K8S_POSTGRES[postgres.yaml]
            K8S_MONGODB[mongodb.yaml]
            K8S_REDIS[redis.yaml]
            K8S_KAFKA[kafka.yaml]
            K8S_ZOOKEEPER[zookeeper.yaml]
            K8S_PROMETHEUS[prometheus.yaml]
            K8S_GRAFANA[grafana.yaml]
        end
        
        subgraph "Monitoring"
            MONITOR_PROMETHEUS[prometheus.yml]
            MONITOR_GRAFANA[grafana.yml]
        end
        
        subgraph "Nginx"
            NGINX_PROD[nginx.prod.conf]
        end
        
        subgraph "Terraform"
            TF_MAIN[main.tf]
            TF_VARIABLES[variables.tf]
            TF_OUTPUTS[outputs.tf]
            TF_PROVIDER[provider.tf]
            TF_NETWORK[network.tf]
            TF_SECURITY[security.tf]
            TF_COMPUTE[compute.tf]
            TF_DATABASE[database.tf]
            TF_STORAGE[storage.tf]
            TF_MONITORING[monitoring.tf]
            TF_SCRIPTS[scripts/]
        end
        
        subgraph "Helm"
            HELM_CHARTS[equilibrium/]
        end
    end
```

### Data Structure

```mermaid
graph TD
    subgraph "Data Layer"
        subgraph "PostgreSQL"
            PG_INIT[init.sql]
        end
        
        subgraph "MongoDB"
            MONGO_INIT[init.js]
        end
        
        subgraph "Redis"
            REDIS_CONF[redis.conf]
        end
    end
```

### Scripts Structure

```mermaid
graph TD
    subgraph "Scripts"
        subgraph "Setup"
            SETUP_DB[setup_database.py]
            SETUP_ENV[setup_environment.py]
        end
        
        subgraph "Deploy"
            DEPLOY_MAIN[deploy.sh]
        end
        
        subgraph "Backup"
            BACKUP_MAIN[backup.sh]
        end
        
        subgraph "Demo"
            DEMO_SCENARIO1[scenario1_morning_rush.py]
            DEMO_SCENARIO2[scenario2_concert_spike.py]
            DEMO_SCENARIO3[scenario3_transactional_integrity.py]
            DEMO_RUN_ALL[run_all_scenarios.py]
        end
        
        subgraph "Test"
            TEST_SIMPLE[simple_test.py]
            TEST_LOAD[load_test.py]
            TEST_INTEGRATION[integration_test.py]
            TEST_E2E[e2e_test.py]
        end
        
        subgraph "Monitoring"
            MONITOR_SETUP[setup_monitoring.sh]
        end
    end
```

### Documentation Structure

```mermaid
graph TD
    subgraph "Documentation"
        subgraph "API Documentation"
            API_README[README.md]
            API_AUTH[auth-api.md]
            API_PRICING[pricing-api.md]
            API_ANALYTICS[analytics-api.md]
        end
        
        subgraph "Architecture"
            ARCH_SYSTEM[system-design.md]
            ARCH_MICROSERVICES[microservices-design.md]
            ARCH_DATA_FLOW[data-flow.md]
        end
        
        subgraph "Deployment"
            DEPLOY_K8S[kubernetes-deployment.md]
            DEPLOY_PRODUCTION[PRODUCTION_DEPLOYMENT.md]
            DEPLOY_MONITORING[monitoring/]
        end
        
        subgraph "Diagrams"
            DIAGRAM_USER[Diagram_01_User_Journey.md]
            DIAGRAM_SYSTEM[Diagram_02_System_Architecture.md]
            DIAGRAM_SEQUENCE[Diagram_03_Service_Sequence.md]
            DIAGRAM_STRUCTURE[Diagram_04_Project_Structure.md]
            DIAGRAM_TECH[Diagram_05_Technology_Stack.md]
        end
    end
```

## File Organization Principles

### 1. **Separation of Concerns**
- Backend services are isolated in their own directories
- Frontend applications are separated by platform and purpose
- Infrastructure configurations are centralized
- Documentation is organized by topic

### 2. **Consistency**
- Each service follows the same structure pattern
- Docker files are consistently named
- Configuration files follow naming conventions
- Documentation follows markdown standards

### 3. **Scalability**
- Microservices can be developed independently
- New services can be added following existing patterns
- Infrastructure can be scaled horizontally
- Documentation can be extended easily

### 4. **Maintainability**
- Clear directory structure
- Consistent file naming
- Comprehensive documentation
- Modular design

## Key Configuration Files

| File | Purpose | Location |
|------|---------|----------|
| `docker-compose.yml` | Development environment | Root |
| `docker-compose.prod.yml` | Production environment | Root |
| `env.example` | Environment variables template | Root |
| `env.prod.example` | Production environment template | Root |
| `Makefile` | Build and deployment commands | Root |
| `requirements.txt` | Python dependencies | Root |

## Service Dependencies

### Backend Services
- Each service has its own `requirements.txt`
- Each service has its own `Dockerfile`
- Services communicate via HTTP APIs and Kafka
- Shared configuration via environment variables

### Frontend Applications
- Each app has its own `package.json`
- Each app has its own `Dockerfile`
- Apps communicate with backend via REST APIs
- Shared UI components and utilities

### Infrastructure
- Kubernetes manifests for each service
- Terraform for cloud infrastructure
- Helm charts for package management
- Monitoring configurations

---

*This project structure provides a scalable, maintainable, and well-organized codebase for the Equilibrium Dynamic Pricing Platform.*
