# AWS Deployment Guide

Complete guide for deploying Zen AI Pentest on Amazon Web Services (AWS) with production-ready configurations.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [EC2 Setup](#ec2-setup)
4. [RDS PostgreSQL](#rds-postgresql)
5. [EKS Deployment](#eks-deployment)
6. [S3 for Reports](#s3-for-reports)
7. [Security Groups](#security-groups)
8. [IAM Roles](#iam-roles)
9. [Auto Scaling](#auto-scaling)
10. [Monitoring](#monitoring)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AWS Architecture                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐        │
│  │   Route 53   │────▶│  CloudFront  │────▶│   ALB        │        │
│  └──────────────┘     └──────────────┘     └──────┬───────┘        │
│                                                   │                  │
│                           ┌───────────────────────┼───────────┐     │
│                           │                       │           │     │
│                           ▼                       ▼           ▼     │
│                    ┌────────────┐          ┌──────────┐  ┌──────┐  │
│                    │  EKS Pod   │          │  EKS Pod │  │ EKS  │  │
│                    │  (API)     │          │  (Worker)│  │ Pod  │  │
│                    └─────┬──────┘          └────┬─────┘  │(Web) │  │
│                          │                      │        └──────┘  │
│                          └──────────────────────┘                  │
│                                     │                               │
│                                     ▼                               │
│                    ┌────────────────────────────────────┐          │
│                    │         RDS PostgreSQL             │          │
│                    │    (Multi-AZ, Encrypted)           │          │
│                    └────────────────────────────────────┘          │
│                                     │                               │
│                                     ▼                               │
│                    ┌────────────────────────────────────┐          │
│                    │         ElastiCache Redis          │          │
│                    │    (Cluster Mode Enabled)          │          │
│                    └────────────────────────────────────┘          │
│                                                                     │
│                    ┌────────────────────────────────────┐          │
│                    │         S3 Bucket                  │          │
│                    │    (Reports, Logs, Backups)        │          │
│                    └────────────────────────────────────┘          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### AWS CLI Installation

```bash
# Install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure credentials
aws configure
# Enter your Access Key ID, Secret Access Key, region (e.g., us-east-1), and output format (json)
```

### Required AWS Services

| Service | Purpose | Estimated Cost |
|---------|---------|----------------|
| EC2 | Compute instances | $50-200/month |
| RDS | PostgreSQL database | $30-100/month |
| EKS | Kubernetes cluster | $75/month + nodes |
| S3 | Storage for reports | $5-20/month |
| ALB | Load balancer | $20-50/month |
| ElastiCache | Redis cache | $15-50/month |

---

## EC2 Setup

### 1. Create VPC and Networking

```bash
# Create VPC
VPC_ID=$(aws ec2 create-vpc \
  --cidr-block 10.0.0.0/16 \
  --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=zen-pentest-vpc}]' \
  --query 'Vpc.VpcId' --output text)

# Enable DNS hostnames
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-hostnames

# Create Internet Gateway
IGW_ID=$(aws ec2 create-internet-gateway \
  --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=zen-pentest-igw}]' \
  --query 'InternetGateway.InternetGatewayId' --output text)

aws ec2 attach-internet-gateway --vpc-id $VPC_ID --internet-gateway-id $IGW_ID

# Create Public Subnets
SUBNET_1A=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.1.0/24 \
  --availability-zone us-east-1a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=zen-pentest-public-1a}]' \
  --query 'Subnet.SubnetId' --output text)

SUBNET_1B=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.2.0/24 \
  --availability-zone us-east-1b \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=zen-pentest-public-1b}]' \
  --query 'Subnet.SubnetId' --output text)

# Create Route Table
ROUTE_TABLE_ID=$(aws ec2 create-route-table \
  --vpc-id $VPC_ID \
  --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=zen-pentest-public-rt}]' \
  --query 'RouteTable.RouteTableId' --output text)

aws ec2 create-route --route-table-id $ROUTE_TABLE_ID \
  --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW_ID

aws ec2 associate-route-table --route-table-id $ROUTE_TABLE_ID --subnet-id $SUBNET_1A
aws ec2 associate-route-table --route-table-id $ROUTE_TABLE_ID --subnet-id $SUBNET_1B
```

### 2. Launch EC2 Instance

```bash
# Get latest Amazon Linux 2023 AMI
AMI_ID=$(aws ssm get-parameters \
  --names /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64 \
  --query 'Parameters[0].Value' --output text)

# Create key pair
aws ec2 create-key-pair --key-name zen-pentest-key \
  --query 'KeyMaterial' --output text > zen-pentest-key.pem
chmod 400 zen-pentest-key.pem

# Create security group
SECURITY_GROUP_ID=$(aws ec2 create-security-group \
  --group-name zen-pentest-sg \
  --description "Security group for Zen AI Pentest" \
  --vpc-id $VPC_ID \
  --query 'GroupId' --output text)

# Add inbound rules
aws ec2 authorize-security-group-ingress \
  --group-id $SECURITY_GROUP_ID \
  --protocol tcp --port 22 --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
  --group-id $SECURITY_GROUP_ID \
  --protocol tcp --port 8000 --cidr 0.0.0.0/0

aws ec2 authorize-security-group-ingress \
  --group-id $SECURITY_GROUP_ID \
  --protocol tcp --port 3000 --cidr 0.0.0.0/0

# Launch instance
INSTANCE_ID=$(aws ec2 run-instances \
  --image-id $AMI_ID \
  --instance-type t3.large \
  --key-name zen-pentest-key \
  --security-group-ids $SECURITY_GROUP_ID \
  --subnet-id $SUBNET_1A \
  --block-device-mappings '[{"DeviceName":"/dev/xvda","Ebs":{"VolumeSize":50,"VolumeType":"gp3","Encrypted":true}}]' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=zen-pentest-server}]' \
  --query 'Instances[0].InstanceId' --output text)

# Allocate and associate Elastic IP
ALLOCATION_ID=$(aws ec2 allocate-address --domain vpc --query 'AllocationId' --output text)
aws ec2 associate-address --instance-id $INSTANCE_ID --allocation-id $ALLOCATION_ID

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID \
  --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)

echo "Instance created with IP: $PUBLIC_IP"
```

### 3. Install Zen AI Pentest on EC2

```bash
# SSH into instance
ssh -i zen-pentest-key.pem ec2-user@$PUBLIC_IP

# Update system
sudo dnf update -y

# Install Docker
sudo dnf install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
  -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone repository
cd /opt
sudo git clone https://github.com/SHAdd0WTAka/zen-ai-pentest.git
sudo chown -R ec2-user:ec2-user zen-ai-pentest
cd zen-ai-pentest

# Create environment file
cp .env.example .env

# Edit .env with production values
cat > .env << 'EOF'
# Production Configuration
JWT_SECRET_KEY=$(openssl rand -hex 32)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=$(openssl rand -base64 24)
DATABASE_URL=postgresql://postgres:your-rds-password@your-rds-endpoint:5432/zen_pentest
DATABASE_SECRET_KEY=$(openssl rand -hex 32)
CORS_ORIGINS=https://your-domain.com
RATE_LIMIT_REQUESTS_PER_MINUTE=100
LOG_LEVEL=INFO
EOF

# Start application
docker-compose up -d
```

---

## RDS PostgreSQL

### 1. Create RDS Subnet Group

```bash
# Create private subnets
PRIVATE_SUBNET_1A=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.3.0/24 \
  --availability-zone us-east-1a \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=zen-pentest-private-1a}]' \
  --query 'Subnet.SubnetId' --output text)

PRIVATE_SUBNET_1B=$(aws ec2 create-subnet \
  --vpc-id $VPC_ID \
  --cidr-block 10.0.4.0/24 \
  --availability-zone us-east-1b \
  --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=zen-pentest-private-1b}]' \
  --query 'Subnet.SubnetId' --output text)

# Create DB subnet group
aws rds create-db-subnet-group \
  --db-subnet-group-name zen-pentest-db-subnet \
  --db-subnet-group-description "Subnet group for Zen AI Pentest RDS" \
  --subnet-ids "[$PRIVATE_SUBNET_1A, $PRIVATE_SUBNET_1B]"
```

### 2. Create RDS Instance

```bash
# Generate secure password
DB_PASSWORD=$(openssl rand -base64 32)

# Create RDS PostgreSQL instance
aws rds create-db-instance \
  --db-instance-identifier zen-pentest-db \
  --db-instance-class db.t3.medium \
  --engine postgres \
  --engine-version 15.4 \
  --allocated-storage 100 \
  --storage-type gp3 \
  --storage-encrypted \
  --master-username postgres \
  --master-user-password "$DB_PASSWORD" \
  --vpc-security-group-ids $DB_SECURITY_GROUP_ID \
  --db-subnet-group-name zen-pentest-db-subnet \
  --multi-az \
  --publicly-accessible false \
  --backup-retention-period 7 \
  --preferred-backup-window 03:00-04:00 \
  --preferred-maintenance-window Mon:04:00-Mon:05:00 \
  --enable-performance-insights \
  --performance-insights-retention-period 7 \
  --enable-cloudwatch-logs-exports '["postgresql", "upgrade"]' \
  --deletion-protection \
  --tags '[{"Key":"Name","Value":"zen-pentest-postgres"}]'

# Wait for instance to be available
echo "Waiting for RDS instance to be available..."
aws rds wait db-instance-available --db-instance-identifier zen-pentest-db

# Get endpoint
DB_ENDPOINT=$(aws rds describe-db-instances \
  --db-instance-identifier zen-pentest-db \
  --query 'DBInstances[0].Endpoint.Address' --output text)

echo "RDS Endpoint: $DB_ENDPOINT"
echo "Database Password: $DB_PASSWORD (SAVE THIS SECURELY)"
```

### 3. Database Security Group

```bash
# Create DB security group
DB_SECURITY_GROUP_ID=$(aws ec2 create-security-group \
  --group-name zen-pentest-db-sg \
  --description "Security group for Zen AI Pentest database" \
  --vpc-id $VPC_ID \
  --query 'GroupId' --output text)

# Allow PostgreSQL from app security group only
aws ec2 authorize-security-group-ingress \
  --group-id $DB_SECURITY_GROUP_ID \
  --protocol tcp --port 5432 \
  --source-group $SECURITY_GROUP_ID
```

---

## EKS Deployment

### 1. Create EKS Cluster

```bash
# Install eksctl
curl --silent --location "https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" | tar xz -C /tmp
sudo mv /tmp/eksctl /usr/local/bin

# Create cluster
eksctl create cluster \
  --name zen-pentest-cluster \
  --version 1.29 \
  --region us-east-1 \
  --node-type t3.large \
  --nodes 2 \
  --nodes-min 1 \
  --nodes-max 4 \
  --managed \
  --vpc-private-subnets "$PRIVATE_SUBNET_1A,$PRIVATE_SUBNET_1B" \
  --vpc-public-subnets "$SUBNET_1A,$SUBNET_1B"

# Verify cluster
eksctl get cluster --name zen-pentest-cluster
```

### 2. Deploy Zen AI Pentest to EKS

```yaml
# zen-pentest-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: zen-pentest-api
  namespace: default
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
        image: your-registry/zen-ai-pentest:latest
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
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
spec:
  rules:
  - http:
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
# Create secrets
kubectl create secret generic zen-pentest-secrets \
  --from-literal=database-url="postgresql://postgres:$DB_PASSWORD@$DB_ENDPOINT:5432/zen_pentest" \
  --from-literal=jwt-secret="$(openssl rand -hex 32)"

# Apply deployment
kubectl apply -f zen-pentest-deployment.yaml

# Check status
kubectl get pods
kubectl get svc
kubectl get ingress
```

---

## S3 for Reports

### 1. Create S3 Bucket

```bash
# Generate unique bucket name
BUCKET_NAME="zen-pentest-reports-$(date +%s)"

# Create bucket
aws s3 mb s3://$BUCKET_NAME --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket $BUCKET_NAME \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket $BUCKET_NAME \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      },
      "BucketKeyEnabled": true
    }]
  }'

# Block public access
aws s3api put-public-access-block \
  --bucket $BUCKET_NAME \
  --public-access-block-configuration \
    BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

# Set lifecycle policy for old reports
aws s3api put-bucket-lifecycle-configuration \
  --bucket $BUCKET_NAME \
  --lifecycle-configuration '{
    "Rules": [{
      "ID": "DeleteOldReports",
      "Status": "Enabled",
      "Filter": {"Prefix": "reports/"},
      "Expiration": {"Days": 90}
    }]
  }'

echo "S3 Bucket created: $BUCKET_NAME"
```

### 2. IAM Policy for S3 Access

```bash
cat > s3-access-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::zen-pentest-reports-*",
        "arn:aws:s3:::zen-pentest-reports-*/*"
      ]
    }
  ]
}
EOF

# Create policy
POLICY_ARN=$(aws iam create-policy \
  --policy-name ZenPentestS3Access \
  --policy-document file://s3-access-policy.json \
  --query 'Policy.Arn' --output text)

echo "S3 Policy ARN: $POLICY_ARN"
```

---

## Security Groups

### Complete Security Group Setup

```bash
# Create security groups
ALB_SG=$(aws ec2 create-security-group \
  --group-name zen-pentest-alb-sg \
  --description "ALB Security Group" \
  --vpc-id $VPC_ID \
  --query 'GroupId' --output text)

EKS_SG=$(aws ec2 create-security-group \
  --group-name zen-pentest-eks-sg \
  --description "EKS Security Group" \
  --vpc-id $VPC_ID \
  --query 'GroupId' --output text)

# ALB Rules - Allow HTTPS from anywhere
aws ec2 authorize-security-group-ingress \
  --group-id $ALB_SG \
  --protocol tcp --port 443 --cidr 0.0.0.0/0

# EKS Rules - Allow from ALB only
aws ec2 authorize-security-group-ingress \
  --group-id $EKS_SG \
  --protocol tcp --port 8000 \
  --source-group $ALB_SG

# Save security group IDs
echo "ALB Security Group: $ALB_SG"
echo "EKS Security Group: $EKS_SG"
echo "DB Security Group: $DB_SECURITY_GROUP_ID"
```

---

## IAM Roles

### 1. EKS Node Role

```bash
cat > eks-trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {"Service": "ec2.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create role
NODE_ROLE=$(aws iam create-role \
  --role-name ZenPentestEKSNodeRole \
  --assume-role-policy-document file://eks-trust-policy.json \
  --query 'Role.Arn' --output text)

# Attach required policies
aws iam attach-role-policy \
  --role-name ZenPentestEKSNodeRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy

aws iam attach-role-policy \
  --role-name ZenPentestEKSNodeRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy

aws iam attach-role-policy \
  --role-name ZenPentestEKSNodeRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly

# Attach custom S3 policy
aws iam attach-role-policy \
  --role-name ZenPentestEKSNodeRole \
  --policy-arn $POLICY_ARN
```

### 2. Service Account Role (IRSA)

```bash
cat > irsa-trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):oidc-provider/$(aws eks describe-cluster --name zen-pentest-cluster --query 'cluster.identity.oidc.issuer' --output text | sed 's|https://||')"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "$(aws eks describe-cluster --name zen-pentest-cluster --query 'cluster.identity.oidc.issuer' --output text | sed 's|https://||'):sub": "system:serviceaccount:default:zen-pentest-sa"
        }
      }
    }
  ]
}
EOF

aws iam create-role \
  --role-name ZenPentestIRSA \
  --assume-role-policy-document file://irsa-trust-policy.json
```

---

## Auto Scaling

### 1. EC2 Auto Scaling

```bash
# Create launch template
aws ec2 create-launch-template \
  --launch-template-name zen-pentest-lt \
  --launch-template-data '{
    "ImageId": "'"$AMI_ID"'",
    "InstanceType": "t3.large",
    "KeyName": "zen-pentest-key",
    "SecurityGroupIds": ["'"$SECURITY_GROUP_ID"'"],
    "UserData": "'"$(base64 -w 0 << 'USERDATA'
#!/bin/bash
yum update -y
yum install -y docker
systemctl start docker
systemctl enable docker
USERDATA
)'"'],
    "BlockDeviceMappings": [{
      "DeviceName": "/dev/xvda",
      "Ebs": {"VolumeSize": 50, "VolumeType": "gp3", "Encrypted": true}
    }]
  }'

# Create auto scaling group
aws autoscaling create-auto-scaling-group \
  --auto-scaling-group-name zen-pentest-asg \
  --launch-template LaunchTemplateName=zen-pentest-lt,Version='$Latest' \
  --min-size 1 \
  --max-size 4 \
  --desired-capacity 2 \
  --vpc-zone-identifier "$SUBNET_1A,$SUBNET_1B" \
  --target-group-arns $TARGET_GROUP_ARN \
  --health-check-type ELB \
  --health-check-grace-period 300

# Configure scaling policies
aws autoscaling put-scaling-policy \
  --auto-scaling-group-name zen-pentest-asg \
  --policy-name zen-pentest-scale-up \
  --policy-type TargetTrackingScaling \
  --target-tracking-configuration '{
    "PredefinedMetricSpecification": {"PredefinedMetricType": "ASGAverageCPUUtilization"},
    "TargetValue": 70.0
  }'
```

### 2. EKS Cluster Autoscaler

```bash
# Deploy Cluster Autoscaler
kubectl apply -f https://raw.githubusercontent.com/kubernetes/autoscaler/master/cluster-autoscaler/cloudprovider/aws/examples/cluster-autoscaler-autodiscover.yaml

# Annotate deployment
kubectl annotate deployment cluster-autoscaler \
  -n kube-system \
  cluster-autoscaler.kubernetes.io/safe-to-evict="false"

# Update deployment with cluster name
kubectl set image deployment cluster-autoscaler \
  -n kube-system \
  cluster-autoscaler=k8s.gcr.io/autoscaling/cluster-autoscaler:v1.29.0
```

---

## Monitoring

### 1. CloudWatch Dashboard

```bash
# Create dashboard
aws cloudwatch put-dashboard \
  --dashboard-name ZenPentest-Production \
  --dashboard-body '{
    "widgets": [
      {
        "type": "metric",
        "properties": {
          "title": "CPU Utilization",
          "metrics": [["AWS/EC2", "CPUUtilization", "AutoScalingGroupName", "zen-pentest-asg"]],
          "period": 300,
          "yAxis": {"left": {"min": 0, "max": 100}}
        }
      },
      {
        "type": "metric",
        "properties": {
          "title": "Database Connections",
          "metrics": [["AWS/RDS", "DatabaseConnections", "DBInstanceIdentifier", "zen-pentest-db"]],
          "period": 300
        }
      },
      {
        "type": "metric",
        "properties": {
          "title": "ALB Request Count",
          "metrics": [["AWS/ApplicationELB", "RequestCount", "LoadBalancer", "app/zen-pentest-alb"]],
          "period": 300
        }
      }
    ]
  }'
```

### 2. CloudWatch Alarms

```bash
# High CPU alarm
aws cloudwatch put-metric-alarm \
  --alarm-name zen-pentest-high-cpu \
  --alarm-description "CPU utilization > 80%" \
  --metric-name CPUUtilization \
  --namespace AWS/EC2 \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --alarm-actions arn:aws:sns:us-east-1:ACCOUNT_ID:alerts-topic \
  --dimensions Name=AutoScalingGroupName,Value=zen-pentest-asg

# Database connections alarm
aws cloudwatch put-metric-alarm \
  --alarm-name zen-pentest-db-connections \
  --alarm-description "Database connections > 80" \
  --metric-name DatabaseConnections \
  --namespace AWS/RDS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --alarm-actions arn:aws:sns:us-east-1:ACCOUNT_ID:alerts-topic \
  --dimensions Name=DBInstanceIdentifier,Value=zen-pentest-db
```

---

## Cleanup

To avoid unnecessary charges, clean up resources when not needed:

```bash
# Delete EKS cluster
eksctl delete cluster --name zen-pentest-cluster --region us-east-1

# Delete RDS instance
aws rds delete-db-instance \
  --db-instance-identifier zen-pentest-db \
  --skip-final-snapshot

# Delete S3 bucket
aws s3 rb s3://$BUCKET_NAME --force

# Delete EC2 instances
aws ec2 terminate-instances --instance-ids $INSTANCE_ID

# Release Elastic IP
aws ec2 release-address --allocation-id $ALLOCATION_ID

# Delete VPC (after all resources are deleted)
aws ec2 delete-vpc --vpc-id $VPC_ID
```

---

## Troubleshooting

### Common Issues

#### RDS Connection Failures
```bash
# Check security group rules
aws ec2 describe-security-groups --group-ids $DB_SECURITY_GROUP_ID

# Test connectivity from EC2
psql -h $DB_ENDPOINT -U postgres -d zen_pentest
```

#### EKS Pod Scheduling Issues
```bash
# Check node status
kubectl get nodes

# Describe pod for events
kubectl describe pod <pod-name>

# Check logs
kubectl logs <pod-name>
```

#### ALB Ingress Not Working
```bash
# Check ingress status
kubectl get ingress

# Verify ALB controller logs
kubectl logs -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller
```

---

## Additional Resources

- [AWS EKS Documentation](https://docs.aws.amazon.com/eks/)
- [AWS RDS Best Practices](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_BestPractices.html)
- [AWS S3 Security Best Practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html)
- [eksctl Documentation](https://eksctl.io/)

---

<p align="center">
  <b>AWS Deployment Complete! ☁️</b><br>
  <sub>For support, see <a href="../../SUPPORT.md">SUPPORT.md</a></sub>
</p>
