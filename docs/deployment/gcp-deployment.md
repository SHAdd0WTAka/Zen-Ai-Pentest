# GCP Deployment Guide

Complete guide for deploying Zen AI Pentest on Google Cloud Platform (GCP) with production-ready configurations.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Compute Engine](#compute-engine)
4. [Cloud SQL](#cloud-sql)
5. [GKE Deployment](#gke-deployment)
6. [Cloud Storage](#cloud-storage)
7. [VPC Configuration](#vpc-configuration)
8. [Cloud Armor](#cloud-armor)
9. [Monitoring](#monitoring)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         GCP Architecture                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐        │
│  │ Cloud DNS    │────▶│ Cloud CDN    │────▶│ Cloud Load   │        │
│  └──────────────┘     └──────────────┘     │ Balancer     │        │
│                                            └──────┬───────┘        │
│                                                   │                  │
│                           ┌───────────────────────┼───────────┐     │
│                           │                       │           │     │
│                           ▼                       ▼           ▼     │
│                    ┌────────────┐          ┌──────────┐  ┌──────┐  │
│                    │  GKE Pod   │          │  GKE Pod │  │ GKE  │  │
│                    │  (API)     │          │  (Worker)│  │ Pod  │  │
│                    └─────┬──────┘          └────┬─────┘  │(Web) │  │
│                          │                      │        └──────┘  │
│                          └──────────────────────┘                  │
│                                     │                               │
│                                     ▼                               │
│                    ┌────────────────────────────────────┐          │
│                    │     Cloud SQL PostgreSQL           │          │
│                    │    (High Availability)             │          │
│                    └────────────────────────────────────┘          │
│                                     │                               │
│                                     ▼                               │
│                    ┌────────────────────────────────────┐          │
│                    │     Memorystore Redis              │          │
│                    │    (Standard Tier)                 │          │
│                    └────────────────────────────────────┘          │
│                                                                     │
│                    ┌────────────────────────────────────┐          │
│                    │     Cloud Storage                  │          │
│                    │    (Standard + Nearline)           │          │
│                    └────────────────────────────────────┘          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### GCP CLI Installation

```bash
# Install Google Cloud SDK
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | \
  sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list

curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | \
  sudo apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -

sudo apt-get update && sudo apt-get install -y google-cloud-sdk

# Initialize gcloud
gcloud init

# Set project
gcloud config set project YOUR_PROJECT_ID
```

### Enable Required APIs

```bash
# Enable APIs
gcloud services enable compute.googleapis.com
gcloud services enable container.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable servicenetworking.googleapis.com
gcloud services enable cloudresourcemanager.googleapis.com
gcloud services enable monitoring.googleapis.com
gcloud services enable logging.googleapis.com
gcloud services enable cloudkms.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

### Required GCP Services

| Service | Purpose | Estimated Cost |
|---------|---------|----------------|
| Compute Engine | VM instances | $50-150/month |
| Cloud SQL | PostgreSQL | $30-100/month |
| GKE | Kubernetes | $75/month + nodes |
| Cloud Storage | Storage | $5-15/month |
| Cloud Load Balancing | Load balancer | $20-50/month |
| Cloud Armor | WAF | $10-30/month |

---

## Compute Engine

### 1. Create VPC Network

```bash
# Variables
PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"
ZONE="us-central1-a"
NETWORK_NAME="zen-pentest-network"

# Create VPC network
gcloud compute networks create $NETWORK_NAME \
  --subnet-mode=custom \
  --mtu=1460 \
  --bgp-routing-mode=regional

# Create subnets
SUBNET_NAME="zen-pentest-subnet"
gcloud compute networks subnets create $SUBNET_NAME \
  --network=$NETWORK_NAME \
  --range=10.0.0.0/24 \
  --region=$REGION \
  --enable-private-ip-google-access

# Create private subnet for database
PRIVATE_SUBNET="zen-pentest-private"
gcloud compute networks subnets create $PRIVATE_SUBNET \
  --network=$NETWORK_NAME \
  --range=10.0.1.0/24 \
  --region=$REGION \
  --enable-private-ip-google-access \
  --enable-flow-logs
```

### 2. Create Firewall Rules

```bash
# Allow SSH
gcloud compute firewall-rules create allow-ssh \
  --network=$NETWORK_NAME \
  --direction=INGRESS \
  --priority=1000 \
  --action=ALLOW \
  --rules=tcp:22 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=zen-pentest

# Allow HTTP/HTTPS
gcloud compute firewall-rules create allow-http \
  --network=$NETWORK_NAME \
  --direction=INGRESS \
  --priority=1001 \
  --action=ALLOW \
  --rules=tcp:80,tcp:443,tcp:8000,tcp:3000 \
  --source-ranges=0.0.0.0/0 \
  --target-tags=zen-pentest

# Allow internal communication
gcloud compute firewall-rules create allow-internal \
  --network=$NETWORK_NAME \
  --direction=INGRESS \
  --priority=1002 \
  --action=ALLOW \
  --rules=tcp:0-65535,udp:0-65535,icmp \
  --source-ranges=10.0.0.0/16
```

### 3. Create VM Instance

```bash
# Generate SSH key
ssh-keygen -t rsa -b 4096 -f ~/.ssh/zen-pentest-gcp -N ""

# Create instance template
INSTANCE_NAME="zen-pentest-vm"
MACHINE_TYPE="e2-standard-4"

gcloud compute instances create $INSTANCE_NAME \
  --zone=$ZONE \
  --machine-type=$MACHINE_TYPE \
  --subnet=$SUBNET_NAME \
  --tags=zen-pentest,http-server,https-server \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=50GB \
  --boot-disk-type=pd-ssd \
  --boot-disk-device-name=$INSTANCE_NAME \
  --metadata-from-file ssh-keys=~/.ssh/zen-pentest-gcp.pub \
  --metadata startup-script='#!/bin/bash
    apt-get update
    apt-get install -y docker.io docker-compose
    systemctl start docker
    systemctl enable docker
  '

# Get external IP
VM_IP=$(gcloud compute instances describe $INSTANCE_NAME \
  --zone=$ZONE \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

echo "VM External IP: $VM_IP"
```

### 4. Configure VM

```bash
# SSH into VM
ssh -i ~/.ssh/zen-pentest-gcp ubuntu@$VM_IP

# Install Docker
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Clone and setup application
cd /opt
sudo git clone https://github.com/SHAdd0WTAka/zen-ai-pentest.git
sudo chown -R $USER:$USER zen-ai-pentest
cd zen-ai-pentest

# Create environment file
cp .env.example .env

# Configure database connection
# (Will be updated after Cloud SQL setup)
echo "Setup complete. Configure .env with Cloud SQL details."
```

---

## Cloud SQL

### 1. Create Cloud SQL Instance

```bash
DB_INSTANCE_NAME="zen-pentest-postgres"
DB_ROOT_PASSWORD=$(openssl rand -base64 32)

# Create Cloud SQL instance
gcloud sql instances create $DB_INSTANCE_NAME \
  --database-version=POSTGRES_15 \
  --tier=db-g1-small \
  --region=$REGION \
  --storage-type=SSD \
  --storage-size=100GB \
  --storage-auto-increase \
  --availability-type=REGIONAL \
  --backup-start-time=03:00 \
  --maintenance-window-day=SUN \
  --maintenance-window-hour=4 \
  --enable-point-in-time-recovery \
  --root-password="$DB_ROOT_PASSWORD" \
  --network=$NETWORK_NAME \
  --no-assign-ip \
  --enable-google-private-path

# Get instance connection name
DB_CONNECTION_NAME=$(gcloud sql instances describe $DB_INSTANCE_NAME \
  --format='value(connectionName)')

echo "DB Connection Name: $DB_CONNECTION_NAME"
echo "DB Root Password: $DB_ROOT_PASSWORD (SAVE SECURELY)"
```

### 2. Create Database and User

```bash
DB_NAME="zen_pentest"
DB_USER="zen_app"
DB_PASSWORD=$(openssl rand -base64 32)

# Create database
gcloud sql databases create $DB_NAME \
  --instance=$DB_INSTANCE_NAME

# Create user
gcloud sql users create $DB_USER \
  --instance=$DB_INSTANCE_NAME \
  --password="$DB_PASSWORD"

# Get private IP
DB_PRIVATE_IP=$(gcloud sql instances describe $DB_INSTANCE_NAME \
  --format='value(ipAddresses[0].ipAddress)')

echo "Database Private IP: $DB_PRIVATE_IP"
echo "App User Password: $DB_PASSWORD"
```

### 3. Configure Private Service Connect

```bash
# Allocate IP range for private services
gcloud compute addresses create google-managed-services-$NETWORK_NAME \
  --global \
  --purpose=VPC_PEERING \
  --prefix-length=16 \
  --network=$NETWORK_NAME

# Create private connection
gcloud services vpc-peerings connect \
  --service=servicenetworking.googleapis.com \
  --ranges=google-managed-services-$NETWORK_NAME \
  --network=$NETWORK_NAME \
  --project=$PROJECT_ID
```

### 4. Cloud SQL Proxy (for local connections)

```bash
# Download Cloud SQL Proxy
curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.linux.amd64
chmod +x cloud-sql-proxy

# Run proxy
./cloud-sql-proxy --port 5432 $DB_CONNECTION_NAME &

# Test connection
psql -h 127.0.0.1 -U postgres -d $DB_NAME
```

---

## GKE Deployment

### 1. Create GKE Cluster

```bash
CLUSTER_NAME="zen-pentest-cluster"
CLUSTER_VERSION="1.29.0-gke.1000"

# Create cluster
gcloud container clusters create $CLUSTER_NAME \
  --zone=$ZONE \
  --cluster-version=$CLUSTER_VERSION \
  --machine-type=e2-standard-4 \
  --num-nodes=2 \
  --enable-autoscaling \
  --min-nodes=1 \
  --max-nodes=5 \
  --enable-autorepair \
  --enable-autoupgrade \
  --enable-network-policy \
  --enable-vertical-pod-autoscaling \
  --enable-horizontal-pod-autoscaling \
  --network=$NETWORK_NAME \
  --subnetwork=$SUBNET_NAME \
  --enable-ip-alias \
  --enable-private-nodes \
  --master-ipv4-cidr=172.16.0.0/28 \
  --enable-master-authorized-networks \
  --master-authorized-networks=$VM_IP/32 \
  --enable-shielded-nodes \
  --shielded-secure-boot \
  --shielded-integrity-monitoring \
  --workload-pool=$PROJECT_ID.svc.id.goog \
  --release-channel=regular

# Get credentials
gcloud container clusters get-credentials $CLUSTER_NAME --zone=$ZONE

# Verify
kubectl get nodes
```

### 2. Create Namespace and Secrets

```bash
# Create namespace
kubectl create namespace zen-pentest

# Create secrets
kubectl create secret generic zen-pentest-secrets \
  --namespace=zen-pentest \
  --from-literal=database-url="postgresql://$DB_USER:$DB_PASSWORD@$DB_PRIVATE_IP:5432/$DB_NAME" \
  --from-literal=jwt-secret="$(openssl rand -hex 32)" \
  --from-literal=db-connection-name="$DB_CONNECTION_NAME"
```

### 3. Deploy Application

```yaml
# zen-pentest-gke.yaml
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
      serviceAccountName: zen-pentest-sa
      containers:
      - name: api
        image: gcr.io/PROJECT_ID/zen-ai-pentest:latest
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
    kubernetes.io/ingress.class: gce
    kubernetes.io/ingress.global-static-ip-name: zen-pentest-ip
    networking.gke.io/managed-certificates: zen-pentest-cert
    kubernetes.io/ingress.allow-http: "false"
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
# Deploy
kubectl apply -f zen-pentest-gke.yaml

# Check status
kubectl get pods -n zen-pentest
kubectl get svc -n zen-pentest
kubectl get ingress -n zen-pentest
```

### 4. Cloud SQL Proxy Sidecar

```yaml
# For connecting to Cloud SQL from GKE
apiVersion: apps/v1
kind: Deployment
metadata:
  name: zen-pentest-api-with-proxy
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
      serviceAccountName: zen-pentest-sa
      containers:
      - name: api
        image: gcr.io/PROJECT_ID/zen-ai-pentest:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          value: "postgresql://localhost:5432/zen_pentest"
        # ... other env vars
      - name: cloud-sql-proxy
        image: gcr.io/cloud-sql-connectors/cloud-sql-proxy:2.8.0
        args:
          - "--structured-logs"
          - "--port=5432"
          - "PROJECT_ID:REGION:DB_INSTANCE_NAME"
        securityContext:
          runAsNonRoot: true
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
```

---

## Cloud Storage

### 1. Create Storage Bucket

```bash
BUCKET_NAME="zen-pentest-reports-$PROJECT_ID"

# Create bucket
gsutil mb -l $REGION gs://$BUCKET_NAME/

# Enable versioning
gsutil versioning set on gs://$BUCKET_NAME/

# Set lifecycle policy
cat > lifecycle.json << 'EOF'
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {
          "age": 90,
          "matchesPrefix": ["reports/"]
        }
      },
      {
        "action": {"type": "SetStorageClass", "storageClass": "NEARLINE"},
        "condition": {
          "age": 30,
          "matchesPrefix": ["reports/"]
        }
      }
    ]
  }
}
EOF
gsutil lifecycle set lifecycle.json gs://$BUCKET_NAME/

# Set uniform bucket-level access
gsutil uniformbucketlevelaccess set on gs://$BUCKET_NAME/

# Enable encryption with CMEK (optional)
# gsutil kms encryption -k projects/PROJECT/locations/LOCATION/keyRings/RING/cryptoKeys/KEY gs://$BUCKET_NAME/

echo "Bucket created: gs://$BUCKET_NAME/"
```

### 2. Create Folders and IAM

```bash
# Create folders
gsutil cp /dev/null gs://$BUCKET_NAME/reports/
gsutil cp /dev/null gs://$BUCKET_NAME/logs/
gsutil cp /dev/null gs://$BUCKET_NAME/backups/

# Create service account for application
gcloud iam service-accounts create zen-pentest-app \
  --display-name="Zen Pentest Application"

# Grant storage access
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:zen-pentest-app@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

# Create and download key
gcloud iam service-accounts keys create ~/zen-pentest-storage-key.json \
  --iam-account=zen-pentest-app@$PROJECT_ID.iam.gserviceaccount.com
```

### 3. Workload Identity (Recommended)

```bash
# Create Kubernetes service account
kubectl create serviceaccount zen-pentest-sa \
  --namespace=zen-pentest

# Allow Kubernetes SA to impersonate GCP SA
gcloud iam service-accounts add-iam-policy-binding \
  zen-pentest-app@$PROJECT_ID.iam.gserviceaccount.com \
  --role="roles/iam.workloadIdentityUser" \
  --member="serviceAccount:$PROJECT_ID.svc.id.goog[zen-pentest/zen-pentest-sa]"

# Annotate Kubernetes SA
kubectl annotate serviceaccount zen-pentest-sa \
  --namespace=zen-pentest \
  iam.gke.io/gcp-service-account=zen-pentest-app@$PROJECT_ID.iam.gserviceaccount.com
```

---

## VPC Configuration

### 1. VPC Peering

```bash
# Create VPC peering (if connecting to another VPC)
PEERING_NAME="zen-pentest-peering"
PEER_NETWORK="projects/other-project/global/networks/other-network"

gcloud compute networks peerings create $PEERING_NAME \
  --network=$NETWORK_NAME \
  --peer-network=$PEER_NETWORK \
  --auto-create-routes
```

### 2. Cloud NAT

```bash
# Create Cloud Router
ROUTER_NAME="zen-pentest-router"
gcloud compute routers create $ROUTER_NAME \
  --network=$NETWORK_NAME \
  --region=$REGION

# Create Cloud NAT
NAT_NAME="zen-pentest-nat"
gcloud compute routers nats create $NAT_NAME \
  --router=$ROUTER_NAME \
  --region=$REGION \
  --auto-allocate-nat-external-ips \
  --nat-all-subnet-ip-ranges \
  --enable-logging
```

### 3. Private Google Access

```bash
# Enable Private Google Access for subnet
gcloud compute networks subnets update $SUBNET_NAME \
  --region=$REGION \
  --enable-private-ip-google-access
```

---

## Cloud Armor

### 1. Create Security Policy

```bash
SECURITY_POLICY_NAME="zen-pentest-security-policy"

# Create policy
gcloud compute security-policies create $SECURITY_POLICY_NAME \
  --description="Security policy for Zen AI Pentest"

# Add default rule (allow)
gcloud compute security-policies rules create 2147483647 \
  --security-policy=$SECURITY_POLICY_NAME \
  --description="Default rule" \
  --action="allow"

# Add rate limiting rule
gcloud compute security-policies rules create 1000 \
  --security-policy=$SECURITY_POLICY_NAME \
  --expression="true" \
  --action="rate-based-ban" \
  --rate-limit-threshold-count=100 \
  --rate-limit-threshold-interval-sec=60 \
  --ban-duration-sec=3600 \
  --conformance-level=STRICT \
  --description="Rate limiting"

# Add SQL injection protection
gcloud compute security-policies rules create 1001 \
  --security-policy=$SECURITY_POLICY_NAME \
  --expression="evaluatePreconfiguredExpr('sqli-v33-stable')" \
  --action="deny(403)" \
  --description="SQL Injection protection"

# Add XSS protection
gcloud compute security-policies rules create 1002 \
  --security-policy=$SECURITY_POLICY_NAME \
  --expression="evaluatePreconfiguredExpr('xss-v33-stable')" \
  --action="deny(403)" \
  --description="XSS protection"
```

### 2. Apply to Load Balancer

```bash
# Get backend service name
BACKEND_SERVICE=$(gcloud compute backend-services list \
  --filter="name ~ zen-pentest" \
  --format="value(name)")

# Attach security policy
gcloud compute backend-services update $BACKEND_SERVICE \
  --security-policy=$SECURITY_POLICY_NAME \
  --global
```

---

## Monitoring

### 1. Cloud Monitoring Setup

```bash
# Create custom dashboard
cat > dashboard.json << 'EOF'
{
  "displayName": "Zen Pentest Dashboard",
  "gridLayout": {
    "columns": "2",
    "widgets": [
      {
        "title": "CPU Usage",
        "xyChart": {
          "dataSets": [{
            "timeSeriesQuery": {
              "timeSeriesFilter": {
                "filter": "resource.type=\"gke_container\" AND metric.type=\"kubernetes.io/container/cpu/core_usage_time\"",
                "aggregation": {
                  "alignmentPeriod": {"seconds": 60},
                  "perSeriesAligner": "ALIGN_RATE"
                }
              }
            }
          }]
        }
      },
      {
        "title": "Memory Usage",
        "xyChart": {
          "dataSets": [{
            "timeSeriesQuery": {
              "timeSeriesFilter": {
                "filter": "resource.type=\"gke_container\" AND metric.type=\"kubernetes.io/container/memory/used_bytes\""
              }
            }
          }]
        }
      }
    ]
  }
}
EOF

gcloud monitoring dashboards create --config-from-file=dashboard.json
```

### 2. Alerting Policies

```bash
# Create notification channel
NOTIFICATION_CHANNEL=$(gcloud monitoring channels create \
  --display-name="Zen Pentest Alerts" \
  --type=email \
  --channel-labels=email_address=admin@example.com \
  --format="value(name)")

# Create CPU alert
gcloud monitoring alert-policies create \
  --display-name="High CPU Usage" \
  --condition-display-name="CPU > 80%" \
  --condition-filter="resource.type=\"gce_instance\" AND metric.type=\"compute.googleapis.com/instance/cpu/utilization\" AND metric.labels.instance_name=\"$INSTANCE_NAME\"" \
  --comparison=COMPARISON_GT \
  --threshold-value=0.8 \
  --duration=300s \
  --notification-channels=$NOTIFICATION_CHANNEL

# Create database connections alert
gcloud monitoring alert-policies create \
  --display-name="High DB Connections" \
  --condition-display-name="DB connections > 80" \
  --condition-filter="resource.type=\"cloudsql_database\" AND metric.type=\"cloudsql.googleapis.com/database/postgresql/num_backends\"" \
  --comparison=COMPARISON_GT \
  --threshold-value=80 \
  --duration=300s \
  --notification-channels=$NOTIFICATION_CHANNEL
```

### 3. Cloud Logging

```bash
# Create log sink to BigQuery (for long-term analysis)
LOG_SINK_NAME="zen-pentest-logs"
DATASET_NAME="zen_pentest_logs"

# Create BigQuery dataset
bq mk --dataset $PROJECT_ID:$DATASET_NAME

# Create log sink
gcloud logging sinks create $LOG_SINK_NAME \
  bigquery.googleapis.com/projects/$PROJECT_ID/datasets/$DATASET_NAME \
  --log-filter="resource.type=\"k8s_container\" AND resource.labels.namespace_name=\"zen-pentest\""

# Get sink writer identity
WRITER_IDENTITY=$(gcloud logging sinks describe $LOG_SINK_NAME --format="value(writerIdentity)")

# Grant permissions
gbq query --use_legacy_sql=false \
  "GRANT WRITER ON DATASET $PROJECT_ID:$DATASET_NAME TO \"$WRITER_IDENTITY\""
```

---

## Cleanup

```bash
# Delete GKE cluster
gcloud container clusters delete $CLUSTER_NAME --zone=$ZONE --quiet

# Delete Cloud SQL instance
gcloud sql instances delete $DB_INSTANCE_NAME --quiet

# Delete VM instance
gcloud compute instances delete $INSTANCE_NAME --zone=$ZONE --quiet

# Delete storage bucket
gsutil rm -r gs://$BUCKET_NAME/

# Delete VPC
gcloud compute networks delete $NETWORK_NAME --quiet
```

---

## Troubleshooting

### Common Issues

#### GKE Pod Not Starting
```bash
# Check pod status
kubectl describe pod <pod-name> -n zen-pentest

# Check logs
kubectl logs <pod-name> -n zen-pentest

# Check events
kubectl get events -n zen-pentest --sort-by='.lastTimestamp'
```

#### Cloud SQL Connection Issues
```bash
# Test proxy connection
./cloud-sql-proxy --port 5432 $DB_CONNECTION_NAME &
psql -h 127.0.0.1 -U postgres

# Check Cloud SQL logs
gcloud logging read "resource.type=cloudsql_database AND resource.labels.database_id=$PROJECT_ID:$DB_INSTANCE_NAME" --limit=10
```

#### Load Balancer Issues
```bash
# Get ingress IP
kubectl get ingress -n zen-pentest

# Check backend health
gcloud compute backend-services get-health BACKEND_SERVICE --global
```

---

## Additional Resources

- [GKE Documentation](https://cloud.google.com/kubernetes-engine/docs)
- [Cloud SQL Documentation](https://cloud.google.com/sql/docs)
- [Cloud Storage Documentation](https://cloud.google.com/storage/docs)
- [Cloud Armor Documentation](https://cloud.google.com/armor/docs)

---

<p align="center">
  <b>GCP Deployment Complete! ☁️</b><br>
  <sub>For support, see <a href="../../SUPPORT.md">SUPPORT.md</a></sub>
</p>
