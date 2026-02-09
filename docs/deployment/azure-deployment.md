# Azure Deployment Guide

Complete guide for deploying Zen AI Pentest on Microsoft Azure with production-ready configurations.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Azure VM Setup](#azure-vm-setup)
4. [Azure Database for PostgreSQL](#azure-database-for-postgresql)
5. [AKS Deployment](#aks-deployment)
6. [Blob Storage](#blob-storage)
7. [Networking](#networking)
8. [Monitoring](#monitoring)
9. [Security](#security)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                       Azure Architecture                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐        │
│  │   DNS Zone   │────▶│   CDN        │────▶│  App Gateway │        │
│  └──────────────┘     └──────────────┘     └──────┬───────┘        │
│                                                   │                  │
│                           ┌───────────────────────┼───────────┐     │
│                           │                       │           │     │
│                           ▼                       ▼           ▼     │
│                    ┌────────────┐          ┌──────────┐  ┌──────┐  │
│                    │  AKS Pod   │          │  AKS Pod │  │ AKS  │  │
│                    │  (API)     │          │  (Worker)│  │ Pod  │  │
│                    └─────┬──────┘          └────┬─────┘  │(Web) │  │
│                          │                      │        └──────┘  │
│                          └──────────────────────┘                  │
│                                     │                               │
│                                     ▼                               │
│                    ┌────────────────────────────────────┐          │
│                    │  Azure Database for PostgreSQL     │          │
│                    │    (Flexible Server)               │          │
│                    └────────────────────────────────────┘          │
│                                     │                               │
│                                     ▼                               │
│                    ┌────────────────────────────────────┐          │
│                    │     Azure Cache for Redis          │          │
│                    │    (Enterprise)                    │          │
│                    └────────────────────────────────────┘          │
│                                                                     │
│                    ┌────────────────────────────────────┐          │
│                    │     Azure Blob Storage             │          │
│                    │    (Hot Tier)                      │          │
│                    └────────────────────────────────────┘          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### Azure CLI Installation

```bash
# Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Login
az login

# Set default subscription (optional)
az account set --subscription "Your Subscription Name"
```

### Required Azure Services

| Service | Purpose | Estimated Cost |
|---------|---------|----------------|
| Virtual Machines | Compute | $50-200/month |
| Database for PostgreSQL | Database | $30-100/month |
| AKS | Kubernetes | $75/month + nodes |
| Blob Storage | Storage | $5-20/month |
| Application Gateway | Load balancer | $25-100/month |
| Monitor | Monitoring | $10-30/month |

---

## Azure VM Setup

### 1. Create Resource Group and Networking

```bash
# Variables
RESOURCE_GROUP="zen-pentest-rg"
LOCATION="westeurope"
VNET_NAME="zen-pentest-vnet"
NSG_NAME="zen-pentest-nsg"

# Create resource group
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION \
  --tags "Environment=Production" "Project=ZenPentest"

# Create Virtual Network
az network vnet create \
  --resource-group $RESOURCE_GROUP \
  --name $VNET_NAME \
  --address-prefix 10.0.0.0/16 \
  --subnet-name frontend \
  --subnet-prefix 10.0.1.0/24

# Create additional subnets
az network vnet subnet create \
  --resource-group $RESOURCE_GROUP \
  --vnet-name $VNET_NAME \
  --name backend \
  --address-prefix 10.0.2.0/24

az network vnet subnet create \
  --resource-group $RESOURCE_GROUP \
  --vnet-name $VNET_NAME \
  --name database \
  --address-prefix 10.0.3.0/24

# Create Network Security Group
az network nsg create \
  --resource-group $RESOURCE_GROUP \
  --name $NSG_NAME \
  --location $LOCATION

# Add NSG rules
az network nsg rule create \
  --resource-group $RESOURCE_GROUP \
  --nsg-name $NSG_NAME \
  --name AllowSSH \
  --priority 1000 \
  --source-address-prefixes '*' \
  --destination-port-ranges 22 \
  --access Allow \
  --protocol Tcp

az network nsg rule create \
  --resource-group $RESOURCE_GROUP \
  --nsg-name $NSG_NAME \
  --name AllowHTTP \
  --priority 1010 \
  --source-address-prefixes '*' \
  --destination-port-ranges 80 8000 3000 \
  --access Allow \
  --protocol Tcp

az network nsg rule create \
  --resource-group $RESOURCE_GROUP \
  --nsg-name $NSG_NAME \
  --name AllowHTTPS \
  --priority 1020 \
  --source-address-prefixes '*' \
  --destination-port-ranges 443 \
  --access Allow \
  --protocol Tcp
```

### 2. Create Virtual Machine

```bash
# Generate SSH key
ssh-keygen -t rsa -b 4096 -f ~/.ssh/zen-pentest-azure -N ""

# Create VM
VM_NAME="zen-pentest-vm"
az vm create \
  --resource-group $RESOURCE_GROUP \
  --name $VM_NAME \
  --location $LOCATION \
  --size Standard_D4s_v3 \
  --image Ubuntu2204 \
  --admin-username azureuser \
  --ssh-key-values ~/.ssh/zen-pentest-azure.pub \
  --vnet-name $VNET_NAME \
  --subnet frontend \
  --nsg $NSG_NAME \
  --public-ip-address-allocation static \
  --os-disk-size-gb 64 \
  --os-disk-caching ReadWrite \
  --storage-sku Premium_LRS \
  --tags "Environment=Production" "Component=API"

# Get VM public IP
VM_IP=$(az vm show \
  --resource-group $RESOURCE_GROUP \
  --name $VM_NAME \
  --show-details \
  --query publicIps \
  --output tsv)

echo "VM Public IP: $VM_IP"
```

### 3. Configure VM for Zen AI Pentest

```bash
# SSH into VM
ssh -i ~/.ssh/zen-pentest-azure azureuser@$VM_IP

# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker azureuser

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone repository
cd /opt
sudo git clone https://github.com/SHAdd0WTAka/zen-ai-pentest.git
sudo chown -R azureuser:azureuser zen-ai-pentest
cd zen-ai-pentest

# Create environment file
cp .env.example .env

# Configure for Azure
sed -i 's|DATABASE_URL=.*|DATABASE_URL=postgresql://postgres:'$DB_PASSWORD'@'$DB_HOST':5432/zen_pentest|' .env
sed -i 's|JWT_SECRET_KEY=.*|JWT_SECRET_KEY='$(openssl rand -hex 32)'|' .env

# Start application
docker-compose up -d
```

---

## Azure Database for PostgreSQL

### 1. Create Flexible Server

```bash
# Variables
DB_SERVER_NAME="zen-pentest-postgres-$(date +%s)"
DB_ADMIN_USER="postgres"
DB_PASSWORD=$(openssl rand -base64 32)
DB_NAME="zen_pentest"

# Create PostgreSQL Flexible Server
az postgres flexible-server create \
  --resource-group $RESOURCE_GROUP \
  --name $DB_SERVER_NAME \
  --location $LOCATION \
  --admin-user $DB_ADMIN_USER \
  --admin-password "$DB_PASSWORD" \
  --sku-name Standard_D2s_v3 \
  --tier GeneralPurpose \
  --storage-size 128 \
  --version 15 \
  --vnet $VNET_NAME \
  --subnet database \
  --private-dns-zone flexibleserver \
  --backup-retention 7 \
  --geo-redundant-backup Disabled \
  --high-availability Disabled \
  --tags "Environment=Production"

# Get database FQDN
DB_HOST=$(az postgres flexible-server show \
  --resource-group $RESOURCE_GROUP \
  --name $DB_SERVER_NAME \
  --query fullyQualifiedDomainName \
  --output tsv)

echo "Database Host: $DB_HOST"
echo "Database Password: $DB_PASSWORD (SAVE THIS SECURELY)"
```

### 2. Configure Database Firewall

```bash
# Allow access from VM subnet
VM_NIC=$(az vm show \
  --resource-group $RESOURCE_GROUP \
  --name $VM_NAME \
  --query 'networkProfile.networkInterfaces[0].id' \
  --output tsv)

VM_PRIVATE_IP=$(az network nic show \
  --ids $VM_NIC \
  --query 'ipConfigurations[0].privateIPAddress' \
  --output tsv)

# Add firewall rule for VM
az postgres flexible-server firewall-rule create \
  --resource-group $RESOURCE_GROUP \
  --name $DB_SERVER_NAME \
  --rule-name AllowVM \
  --start-ip-address 10.0.1.0 \
  --end-ip-address 10.0.1.255
```

### 3. Create Database and User

```bash
# Install PostgreSQL client locally
sudo apt-get install -y postgresql-client

# Connect and create database
PGPASSWORD="$DB_PASSWORD" psql \
  -h $DB_HOST \
  -U $DB_ADMIN_USER \
  -d postgres \
  -c "CREATE DATABASE $DB_NAME;"

# Create application user
APP_DB_PASSWORD=$(openssl rand -base64 32)
PGPASSWORD="$DB_PASSWORD" psql \
  -h $DB_HOST \
  -U $DB_ADMIN_USER \
  -d $DB_NAME \
  -c "CREATE USER zen_app WITH PASSWORD '$APP_DB_PASSWORD';"

PGPASSWORD="$DB_PASSWORD" psql \
  -h $DB_HOST \
  -U $DB_ADMIN_USER \
  -d $DB_NAME \
  -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO zen_app;"

echo "App Database Password: $APP_DB_PASSWORD"
```

---

## AKS Deployment

### 1. Create AKS Cluster

```bash
AKS_NAME="zen-pentest-aks"
AKS_NODE_COUNT=2

# Create AKS cluster
az aks create \
  --resource-group $RESOURCE_GROUP \
  --name $AKS_NAME \
  --location $LOCATION \
  --kubernetes-version 1.29.0 \
  --node-count $AKS_NODE_COUNT \
  --node-vm-size Standard_D4s_v3 \
  --enable-cluster-autoscaler \
  --min-count 1 \
  --max-count 5 \
  --enable-addons monitoring \
  --generate-ssh-keys \
  --network-plugin azure \
  --vnet-subnet-id "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Network/virtualNetworks/$VNET_NAME/subnets/backend" \
  --service-cidr 10.1.0.0/16 \
  --dns-service-ip 10.1.0.10 \
  --docker-bridge-address 172.17.0.1/16 \
  --enable-managed-identity \
  --tags "Environment=Production"

# Get credentials
az aks get-credentials \
  --resource-group $RESOURCE_GROUP \
  --name $AKS_NAME \
  --overwrite-existing

# Verify connection
kubectl get nodes
```

### 2. Deploy to AKS

```yaml
# zen-pentest-aks.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: zen-pentest
---
apiVersion: v1
kind: Secret
metadata:
  name: zen-pentest-secrets
  namespace: zen-pentest
type: Opaque
stringData:
  database-url: "postgresql://postgres:DB_PASSWORD@DB_HOST:5432/zen_pentest"
  jwt-secret: "JWT_SECRET"
  redis-url: "redis://redis:6379/0"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: zen-pentest-api
  namespace: zen-pentest
spec:
  replicas: 3
  selector:
    matchLabels:
      app: zen-pentest-api
  template:
    metadata:
      labels:
        app: zen-pentest-api
    spec:
      containers:
      - name: api
        image: yourregistry/zen-ai-pentest:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: zen-pentest-secrets
              key: database-url
        - name: JWT_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: zen-pentest-secrets
              key: jwt-secret
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
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
  name: zen-pentest-service
  namespace: zen-pentest
spec:
  selector:
    app: zen-pentest-api
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: zen-pentest-ingress
  namespace: zen-pentest
  annotations:
    kubernetes.io/ingress.class: azure/application-gateway
    appgw.ingress.kubernetes.io/cookie-based-affinity: "true"
    appgw.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  rules:
  - host: zen-pentest.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: zen-pentest-service
            port:
              number: 80
```

```bash
# Deploy to AKS
kubectl apply -f zen-pentest-aks.yaml

# Check status
kubectl get pods -n zen-pentest
kubectl get svc -n zen-pentest
kubectl get ingress -n zen-pentest
```

### 3. Configure Application Gateway

```bash
# Create Application Gateway
APPGW_NAME="zen-pentest-appgw"
APPGW_PUBLIC_IP="zen-pentest-appgw-ip"

# Create public IP
az network public-ip create \
  --resource-group $RESOURCE_GROUP \
  --name $APPGW_PUBLIC_IP \
  --allocation-method Static \
  --sku Standard

# Create Application Gateway
az network application-gateway create \
  --resource-group $RESOURCE_GROUP \
  --name $APPGW_NAME \
  --location $LOCATION \
  --sku WAF_v2 \
  --capacity 2 \
  --vnet-name $VNET_NAME \
  --subnet backend \
  --public-ip-address $APPGW_PUBLIC_IP \
  --frontend-port 80 \
  --http-settings-port 80 \
  --http-settings-protocol Http \
  --priority 100

# Enable WAF
az network application-gateway waf-config set \
  --resource-group $RESOURCE_GROUP \
  --gateway-name $APPGW_NAME \
  --enabled true \
  --firewall-mode Prevention \
  --rule-set-type OWASP \
  --rule-set-version 3.2
```

---

## Blob Storage

### 1. Create Storage Account

```bash
STORAGE_ACCOUNT="zenpenteststorage$(date +%s)"

# Create storage account
az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS \
  --kind StorageV2 \
  --access-tier Hot \
  --https-only true \
  --min-tls-version TLS1_2 \
  --allow-blob-public-access false \
  --tags "Environment=Production"

# Enable blob versioning
az storage account blob-service-properties update \
  --resource-group $RESOURCE_GROUP \
  --account-name $STORAGE_ACCOUNT \
  --enable-versioning true

# Get connection string
STORAGE_CONNECTION_STRING=$(az storage account show-connection-string \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --query connectionString \
  --output tsv)

echo "Storage Account: $STORAGE_ACCOUNT"
```

### 2. Create Containers

```bash
# Create containers for different purposes
az storage container create \
  --name reports \
  --account-name $STORAGE_ACCOUNT \
  --public-access off

az storage container create \
  --name logs \
  --account-name $STORAGE_ACCOUNT \
  --public-access off

az storage container create \
  --name backups \
  --account-name $STORAGE_ACCOUNT \
  --public-access off
```

### 3. Lifecycle Management

```bash
# Create lifecycle policy
cat > lifecycle-policy.json << 'EOF'
{
  "rules": [
    {
      "name": "reports-lifecycle",
      "enabled": true,
      "type": "Lifecycle",
      "definition": {
        "filters": {
          "blobTypes": ["blockBlob"],
          "prefixMatch": ["reports/"]
        },
        "actions": {
          "baseBlob": {
            "tierToCool": { "daysAfterModificationGreaterThan": 30 },
            "delete": { "daysAfterModificationGreaterThan": 90 }
          }
        }
      }
    },
    {
      "name": "logs-lifecycle",
      "enabled": true,
      "type": "Lifecycle",
      "definition": {
        "filters": {
          "blobTypes": ["blockBlob"],
          "prefixMatch": ["logs/"]
        },
        "actions": {
          "baseBlob": {
            "delete": { "daysAfterModificationGreaterThan": 30 }
          }
        }
      }
    }
  ]
}
EOF

az storage account management-policy create \
  --resource-group $RESOURCE_GROUP \
  --account-name $STORAGE_ACCOUNT \
  --policy @lifecycle-policy.json
```

---

## Networking

### 1. Virtual Network Peering (if needed)

```bash
# Create peering between VNets
az network vnet peering create \
  --name zen-pentest-peering \
  --resource-group $RESOURCE_GROUP \
  --vnet-name $VNET_NAME \
  --remote-vnet "/subscriptions/OTHER_SUB/resourceGroups/OTHER_RG/providers/Microsoft.Network/virtualNetworks/OTHER_VNET" \
  --allow-vnet-access
```

### 2. Private Endpoints

```bash
# Create private endpoint for database
az network private-endpoint create \
  --resource-group $RESOURCE_GROUP \
  --name zen-pentest-db-pe \
  --vnet-name $VNET_NAME \
  --subnet database \
  --private-connection-resource-id "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.DBforPostgreSQL/flexibleServers/$DB_SERVER_NAME" \
  --group-id postgresqlServer \
  --connection-name zen-pentest-db-connection
```

### 3. Azure Front Door (Optional)

```bash
# Create Front Door for global load balancing
FRONT_DOOR_NAME="zen-pentest-fd"

az afd profile create \
  --resource-group $RESOURCE_GROUP \
  --profile-name $FRONT_DOOR_NAME \
  --sku Premium_AzureFrontDoor

# Create endpoint
az afd endpoint create \
  --resource-group $RESOURCE_GROUP \
  --profile-name $FRONT_DOOR_NAME \
  --endpoint-name zen-pentest \
  --enabled-state Enabled
```

---

## Monitoring

### 1. Azure Monitor Setup

```bash
# Create Log Analytics workspace
WORKSPACE_NAME="zen-pentest-logs"

az monitor log-analytics workspace create \
  --resource-group $RESOURCE_GROUP \
  --name $WORKSPACE_NAME \
  --location $LOCATION \
  --sku PerGB2018 \
  --retention-time 30

# Get workspace ID
WORKSPACE_ID=$(az monitor log-analytics workspace show \
  --resource-group $RESOURCE_GROUP \
  --name $WORKSPACE_NAME \
  --query id \
  --output tsv)
```

### 2. Application Insights

```bash
APP_INSIGHTS_NAME="zen-pentest-appinsights"

az monitor app-insights component create \
  --resource-group $RESOURCE_GROUP \
  --application-type web \
  --app $APP_INSIGHTS_NAME \
  --location $LOCATION \
  --workspace $WORKSPACE_ID

# Get instrumentation key
INSTRUMENTATION_KEY=$(az monitor app-insights component show \
  --resource-group $RESOURCE_GROUP \
  --app $APP_INSIGHTS_NAME \
  --query instrumentationKey \
  --output tsv)

echo "Instrumentation Key: $INSTRUMENTATION_KEY"
```

### 3. Alerts

```bash
# Create action group
ACTION_GROUP_NAME="zen-pentest-alerts"

az monitor action-group create \
  --resource-group $RESOURCE_GROUP \
  --name $ACTION_GROUP_NAME \
  --short-name zenpentest \
  --email-receivers admin@example.com \
  --email-receiver-names Admin

# Create CPU alert
az monitor metrics alert create \
  --resource-group $RESOURCE_GROUP \
  --name "High CPU Alert" \
  --scopes "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Compute/virtualMachines/$VM_NAME" \
  --condition "avg Percentage CPU > 80" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --action $ACTION_GROUP_NAME \
  --description "Alert when CPU exceeds 80%"

# Create database connection alert
az monitor metrics alert create \
  --resource-group $RESOURCE_GROUP \
  --name "DB Connections Alert" \
  --scopes "/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.DBforPostgreSQL/flexibleServers/$DB_SERVER_NAME" \
  --condition "avg active_connections > 80" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --action $ACTION_GROUP_NAME \
  --description "Alert when DB connections exceed 80"
```

---

## Security

### 1. Azure Key Vault

```bash
KEYVAULT_NAME="zen-pentest-kv-$(date +%s)"

# Create Key Vault
az keyvault create \
  --resource-group $RESOURCE_GROUP \
  --name $KEYVAULT_NAME \
  --location $LOCATION \
  --sku standard \
  --enable-rbac-authorization true \
  --enable-soft-delete true \
  --retention-days 90

# Add secrets
az keyvault secret set \
  --vault-name $KEYVAULT_NAME \
  --name "DatabasePassword" \
  --value "$DB_PASSWORD"

az keyvault secret set \
  --vault-name $KEYVAULT_NAME \
  --name "JWTSecret" \
  --value "$(openssl rand -hex 32)"

az keyvault secret set \
  --vault-name $KEYVAULT_NAME \
  --name "StorageConnectionString" \
  --value "$STORAGE_CONNECTION_STRING"
```

### 2. Managed Identities

```bash
# Create user-assigned managed identity
IDENTITY_NAME="zen-pentest-identity"

az identity create \
  --resource-group $RESOURCE_GROUP \
  --name $IDENTITY_NAME \
  --location $LOCATION

# Assign Key Vault access
az keyvault set-policy \
  --name $KEYVAULT_NAME \
  --object-id $(az identity show --resource-group $RESOURCE_GROUP --name $IDENTITY_NAME --query principalId -o tsv) \
  --secret-permissions get list
```

### 3. Azure Security Center

```bash
# Enable Azure Defender
az security pricing create \
  --name VirtualMachines \
  --tier Standard

az security pricing create \
  --name SqlServers \
  --tier Standard

az security pricing create \
  --name StorageAccounts \
  --tier Standard
```

---

## Cleanup

```bash
# Delete resource group (removes all resources)
az group delete \
  --name $RESOURCE_GROUP \
  --yes \
  --no-wait

# Or delete individual resources
az aks delete --resource-group $RESOURCE_GROUP --name $AKS_NAME --yes --no-wait
az postgres flexible-server delete --resource-group $RESOURCE_GROUP --name $DB_SERVER_NAME --yes
az vm delete --resource-group $RESOURCE_GROUP --name $VM_NAME --yes
```

---

## Troubleshooting

### Common Issues

#### AKS Connection Issues
```bash
# Reset credentials
az aks get-credentials --resource-group $RESOURCE_GROUP --name $AKS_NAME --overwrite-existing

# Check node status
kubectl get nodes
kubectl describe node <node-name>
```

#### Database Connection Failed
```bash
# Check firewall rules
az postgres flexible-server firewall-rule list \
  --resource-group $RESOURCE_GROUP \
  --name $DB_SERVER_NAME

# Test connection
psql -h $DB_HOST -U $DB_ADMIN_USER -d postgres
```

#### Application Gateway Issues
```bash
# Check backend health
az network application-gateway show-backend-health \
  --resource-group $RESOURCE_GROUP \
  --name $APPGW_NAME
```

---

## Additional Resources

- [Azure AKS Documentation](https://docs.microsoft.com/en-us/azure/aks/)
- [Azure Database for PostgreSQL](https://docs.microsoft.com/en-us/azure/postgresql/)
- [Azure Blob Storage](https://docs.microsoft.com/en-us/azure/storage/blobs/)
- [Azure Application Gateway](https://docs.microsoft.com/en-us/azure/application-gateway/)

---

<p align="center">
  <b>Azure Deployment Complete! ☁️</b><br>
  <sub>For support, see <a href="../../SUPPORT.md">SUPPORT.md</a></sub>
</p>
