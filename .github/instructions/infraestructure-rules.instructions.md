---
applyTo: '**'
---

# Infrastructure Rules and Guidelines for Setter Service

## Overview

This document defines the infrastructure architecture, deployment patterns, and cloud strategy for the **Setter Service** project. It covers current implementation, future migration plans, and best practices for maintaining a cloud-agnostic, scalable, and cost-effective infrastructure.

## Table of Contents

* [Current Architecture](#current-architecture)
* [N8N Workflow Management](#n8n-workflow-management)
* [Cloud Strategy](#cloud-strategy)
* [Deployment Patterns](#deployment-patterns)
* [Service Architecture](#service-architecture)
* [SSL/TLS Management](#ssltls-management)
* [Multi-Domain Architecture](#multi-domain-architecture)
* [Migration Strategy](#migration-strategy)
* [Monitoring and Observability](#monitoring-and-observability)
* [Security Guidelines](#security-guidelines)
* [Cost Optimization](#cost-optimization)
* [Future Roadmap](#future-roadmap)

## Current Architecture

### **Infrastructure Stack**

**Current Cloud Provider: AWS**
- **Region**: us-east-1
- **Instance Type**: EC2 (t3.medium/large recommended)
- **Domains**: 
  - `sanboxaivance.store` (primary domain)
  - `dealstormaibuildup.online` (secondary domain)
- **SSL**: Let's Encrypt with automatic renewal
- **Multi-Domain Support**: Variable-based nginx configuration

### **Deployment Model: Monorepo + Docker Compose**

Our infrastructure follows a **pragmatic monorepo approach** optimized for:
- ✅ **Rapid deployment cycles**
- ✅ **Simplified AWS configuration**
- ✅ **Cost-effective single-instance deployment**
- ✅ **Unified Celery ecosystem management**

**Why Monorepo over Microservices:**
- Faster iteration without complex EKS setup
- Unified networking for Celery workers
- Reduced AWS overhead (no ALB, ECR, complex networking)
- Better suited for small-medium team size
- Lower operational complexity

### **Service Architecture**

```
Internet → Route53 DNS → EC2 Instance
├── Nginx (SSL Termination + Reverse Proxy)
│   ├── Main App: localhost → Setter Front (React/Next Frontend)
│   ├── API Gateway: localhost/api → Setter Service (Flask API Backend)
│   └── Automation Gateway: n8n.localhost → N8N (Workflow Automation)
├── N8N Workflow Engine (Request Processing & Validation)
│   ├── Webhook Reception: /webhook/setter/manychat/instagram
│   ├── Input Validation & Processing
│   ├── Data Transformation & Enrichment
│   └── Internal API Calls: http://setter_service:5000/api/*
├── Setter Service (Flask API Backend)
│   ├── Business Logic Processing
│   ├── Database Operations
│   └── Task Queue Management
├── Celery Workers (Background Processing)
├── Celery Beat (Task Scheduler)
├── Flower (Queue Monitoring)
└── Portainer (Container Management)
    ↓
External Managed Services:
├── MongoDB Atlas (Primary Database)
├── Redis Cloud (Cache + Message Broker)
└── Let's Encrypt (SSL Certificates)
```

### **N8N Gateway Architecture**

**Request Flow Pattern:**
```
External System → N8N Webhook → Validation → Transformation → Setter Service → Response
```

**N8N Gateway Responsibilities:**
- ✅ **Webhook Reception**: Handles incoming requests from external systems
- ✅ **Input Validation**: Validates required fields before processing
- ✅ **Data Transformation**: Normalizes and enriches incoming data
- ✅ **Error Handling**: Provides consistent error responses
- ✅ **Service Routing**: Routes validated requests to appropriate Setter Service endpoints
- ✅ **Response Formatting**: Ensures consistent response structure

**Example Workflow Configuration:**
```yaml
Webhook Endpoint: POST /setter/manychat/instagram
├── Input Validation:
│   ├── lead_identification (required)
│   ├── lead_message (required)
│   └── chat_id (required)
├── Data Enrichment:
│   ├── channel: "telegram" (default)
│   ├── consumer: "MANYCHAT" (default)
│   └── workflow: "SETTER" (default)
├── Service Call: POST http://setter_service:5000/api/lead/messages
└── Response Handling:
    ├── Success (201): Extract {id, status, message}
    ├── Error (4xx/5xx): Extract error details
    └── Invalid Input: Return validation errors
```

### **Container Orchestration**

**Primary Stack** (`docker-compose.yml`):
- **Application Services**: Backend, Frontend, Workers
- **Infrastructure Services**: Nginx, Portainer
- **Health Monitoring**: External dependency checks
- **Network**: Internal bridge network (`setter_network`)

**Certificate Management**:
- **Method**: Standalone validation (proven reliable)
- **Multi-Domain Support**: Separate docker-compose files per domain
- **Files**: 
  - `docker-compose.cert.yml` (sanboxaivance.store)
  - `docker-compose-buildup.cert.yml` (dealstormaibuildup.online)
- **Automation**: Cron-based renewal pipeline

## N8N Workflow Management

### **N8N as API Gateway**

N8N serves as the primary entry point for external webhook requests, providing a robust workflow automation layer that preprocesses requests before they reach the Setter Service.

**Architecture Benefits:**
- ✅ **Request Validation**: Centralized input validation and sanitization
- ✅ **Data Transformation**: Standardization of incoming payloads
- ✅ **Error Handling**: Consistent error response formatting
- ✅ **Protocol Translation**: Webhook-to-API translation layer
- ✅ **Monitoring**: Built-in execution tracking and logging

### **Standard Workflow Pattern: Setter ManyChat Instagram**

**Workflow Name**: `SETTER`
**Webhook Endpoint**: `POST /setter/manychat/instagram`
**Service URL**: `http://n8n.localhost/webhook/setter/manychat/instagram`

**Node Flow Architecture:**
```
1. Webhook Reception
   ├── Method: POST
   ├── Path: setter/manychat/instagram
   └── Response Mode: responseNode

2. Input Validation
   ├── Validate: lead_identification (required)
   ├── Validate: lead_message (required)
   ├── Validate: chat_id (required)
   └── Branch: Valid → Process | Invalid → Error Response

3. Data Transformation
   ├── Extract: Required fields from request body
   ├── Set Defaults: 
   │   ├── channel: "telegram"
   │   ├── consumer: "MANYCHAT"
   │   └── workflow: "SETTER"
   └── Build: Standardized payload

4. Service Integration
   ├── HTTP Request: POST http://setter_service:5000/api/lead/messages
   ├── Timeout: 30 seconds
   ├── Headers: Content-Type: application/json
   └── Body: Transformed payload

5. Response Processing
   ├── Success (201): Extract {id, status, message}
   ├── Error (4xx/5xx): Extract error details
   └── Invalid Input: Build error response

6. Webhook Response
   ├── Headers: Content-Type: application/json
   ├── Status: Always 201 (for webhook compatibility)
   └── Body: Processed response data
```

**Workflow Configuration (JSON Export):**
```json
{
  "name": "SETTER",
  "nodes": [
    {
      "parameters": {
        "httpMethod": "POST",
        "path": "setter/manychat/instagram",
        "responseMode": "responseNode"
      },
      "name": "Webhook (POST /setter/manychat/instagram)",
      "type": "n8n-nodes-base.webhook"
    },
    {
      "parameters": {
        "conditions": {
          "string": [
            {"value1": "={{ $json.body.lead_identification }}", "operation": "isNotEmpty"},
            {"value1": "={{ $json.body.lead_message }}", "operation": "isNotEmpty"},
            {"value1": "={{ $json.body.chat_id }}", "operation": "isNotEmpty"}
          ]
        }
      },
      "name": "IF • Validate Required Fields",
      "type": "n8n-nodes-base.if"
    },
    {
      "parameters": {
        "method": "POST",
        "url": "http://setter_service:5000/api/lead/messages",
        "sendBody": true,
        "specifyBody": "json",
        "jsonBody": "={{ $json }}",
        "options": {"timeout": 30000}
      },
      "name": "POST Lead Message",
      "type": "n8n-nodes-base.httpRequest",
      "continueOnFail": true
    }
  ]
}
```

### **Error Handling Strategy**

**Input Validation Errors:**
```json
{
  "status": "INVALID_INPUT",
  "message": "Missing required fields",
  "id": null
}
```

**Service Integration Errors:**
```json
{
  "status": "ERROR",
  "message": "Upstream error details",
  "id": null
}
```

**Success Response:**
```json
{
  "id": "generated-message-id",
  "status": "SUCCESS",
  "message": "Message processed successfully"
}
```

### **Development Workflow**

**Local Development Setup:**
1. **N8N Interface**: http://n8n.localhost
2. **Workflow Import**: Import JSON configuration
3. **Webhook Testing**: Use provided test scripts
4. **Service Integration**: Monitor via Flower dashboard

**Testing Commands:**
```bash
# Test webhook endpoint
curl --location 'http://n8n.localhost/webhook/setter/manychat/instagram' \
--header 'Content-Type: application/json' \
--data '{
    "lead_identification": "test_user",
    "lead_message": "Test message",
    "chat_id": "123456789"
}'

# Run automated tests
bash scripts/test_n8n_webhook.sh
```

### **Production Considerations**

**Security:**
- Basic Authentication enabled for N8N interface
- Internal network communication (setter_service:5000)
- No direct external access to Setter Service

**Performance:**
- 30-second timeout for service calls
- Async processing via Celery workers
- Response caching where appropriate

**Monitoring:**
- N8N execution logs
- Webhook success/failure rates
- Service response times
- Error pattern analysis

## Cloud Strategy

### **Hybrid Architecture Philosophy**

Our architecture strategically separates **compute** from **data services**:

**EC2 Managed (Stateless)**:
- Application logic and business processes
- Request processing and API endpoints
- Background job processing
- SSL termination and routing

**Cloud Managed (Stateful)**:
- **MongoDB Atlas**: Database with built-in HA, backups, scaling
- **Redis Cloud**: Cache and message broker with clustering
- **Let's Encrypt**: Certificate authority with global trust

### **Cloud-Agnostic Design Principles**

1. **No Vendor Lock-in**: Standard Docker containers, portable configs
2. **External Dependencies**: Managed services available across clouds
3. **Configuration Management**: Environment variables for portability
4. **Standard Protocols**: HTTP, TCP, standard ports and interfaces

### **Multi-Cloud Readiness**

**Current (AWS)**:
```
AWS EC2 (us-east-1) → OpenAI API (Azure East US)
├── Latency: ~80-120ms cross-cloud
├── Egress costs: AWS → Azure charges
└── Rate limits: Impacted by network latency
```

**Target (Azure)**:
```
Azure VM (East US) → OpenAI API (Azure East US)
├── Latency: ~10-30ms same-cloud
├── Egress costs: No cross-cloud charges
└── Rate limits: Optimized performance
```

## Deployment Patterns

### **Environment Configuration**

**Environment Variables** (`.env`):
- ✅ **Database connections**: MongoDB Atlas, Redis Cloud
- ✅ **API keys**: OpenAI, third-party services
- ✅ **SSL configuration**: Certbot domain and email
- ✅ **Application settings**: Flask, Celery configuration
- ✅ **Multi-domain control**: `NGINX_CONFIG_FILE` variable

**Configuration Principles**:
- External configuration for all environment-specific values
- No secrets hardcoded in containers or images
- Consistent naming conventions across environments
- Support for multiple deployment targets
- **Domain-agnostic deployment**: Single infrastructure supports multiple domains

### **Container Strategy**

**Build Patterns**:
```dockerfile
# Multi-stage builds for production optimization
# Consistent base images across services
# Minimal attack surface with Alpine Linux
# Health checks for all critical services
```

**Volume Management**:
- **Persistent data**: SSL certificates, logs
- **Shared resources**: Webroot for ACME challenges
- **External mounts**: Configuration files (read-only)

### **Service Dependencies**

**Startup Order**:
1. **External Health Checks**: MongoDB Atlas, Redis Cloud availability
2. **Core Application**: Setter Service with health endpoints
3. **Background Processing**: Celery workers and beat scheduler
4. **Workflow Automation**: N8N with webhook capabilities
5. **Proxy Layer**: Nginx with SSL termination and subdomain routing
6. **Monitoring**: Flower and Portainer interfaces

**Dependency Management**:
- Health check conditions for critical services
- Graceful degradation for non-critical components
- Retry mechanisms for external service connections
- N8N workflow validation and testing capabilities

## Service Architecture

### **Application Services**

**N8N Workflow Engine (Gateway)**:
- **Technology**: N8N workflow automation platform
- **Port**: 5678 (internal), accessible via n8n.localhost
- **Purpose**: Primary entry point for external webhook requests
- **Features**: Input validation, data transformation, error handling
- **Health Check**: `/healthz` endpoint
- **Database**: SQLite for workflow storage

**Setter Service (Backend)**:
- **Technology**: Flask application with Hexagonal Architecture
- **Port**: 5000 (internal)
- **Health Check**: `/health` endpoint
- **Scaling**: Stateless, horizontally scalable
- **Integration**: Receives processed requests from N8N gateway

**Setter Front (Frontend)**:
- **Technology**: React/Next.js application
- **Port**: 3000 (internal)
- **Deployment**: Static build with hot reload in development
- **CDN Ready**: Prepared for future CDN integration

### **N8N Gateway Processing**

**Workflow Orchestration**:
- **Webhook Reception**: Handles incoming external requests
- **Input Validation**: Validates required fields (lead_identification, lead_message, chat_id)
- **Data Enrichment**: Adds default values (channel, consumer, workflow)
- **Service Integration**: Routes to appropriate Setter Service endpoints
- **Response Processing**: Standardizes response format

**Standard Processing Flow**:
```
External Request → N8N Webhook → Validation → Transformation → Setter Service → Processed Response
```

### **Background Processing**

**Celery Ecosystem**:
- **Workers**: Background task processing
- **Beat**: Scheduled task execution with RedBeat scheduler
- **Flower**: Web-based monitoring at port 5555
- **Broker**: Redis Cloud for message queuing
- **Result Backend**: Redis Cloud for task result storage

**Task Categories**:
- **Message Processing**: OpenAI API interactions triggered by N8N workflows
- **Lead Management**: CRM and pipeline operations
- **Data Synchronization**: External API integrations
- **Scheduled Tasks**: Maintenance and cleanup operations

### **Reverse Proxy Configuration**

**Nginx Routing**:
```
HTTP (80) → HTTPS (443) redirect + ACME challenges (Production)
HTTP (80) → Direct routing (Local Development)

Local Development Routing:
├── localhost/api/* → setter_service:5000 (Backend API)
├── localhost/* → setter_front:3000 (Frontend SPA)
└── n8n.localhost/* → n8n:5678 (N8N Workflow Engine)

Production Routing:
├── /api/* → setter_service:5000 (Backend API)
├── /* → setter_front:3000 (Frontend SPA)
└── /.well-known/acme-challenge/* → webroot (SSL validation)
```

**N8N Subdomain Configuration (Local Development)**:
```nginx
server {
  listen 80;
  server_name n8n.localhost;
  
  location / {
    proxy_pass http://n8n:5678;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # WebSocket support for N8N
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    
    # Timeouts for long-running workflows
    proxy_connect_timeout 300;
    proxy_send_timeout 300;
    proxy_read_timeout 300;
  }
}
```

**SSL Configuration** (Production):
- **Certificates**: Let's Encrypt with 90-day validity
- **Security Headers**: HSTS, CSP, X-Frame-Options
- **Protocol Support**: TLS 1.2+, HTTP/2 enabled

## SSL/TLS Management

### **Multi-Domain Certificate Strategy**

**Domain Configuration**:
- **Primary Domain**: `sanboxaivance.store` (production)
- **Secondary Domain**: `dealstormaibuildup.online` (projects)
- **Method**: Standalone validation (proven reliability)
- **Approach**: Separate certificate files per domain

### **Certificate Lifecycle**

**Initial Provisioning**:
```bash
# For sanboxaivance.store
docker compose -f docker-compose.cert.yml up

# For dealstormaibuildup.online  
docker compose -f docker-compose-buildup.cert.yml up
```

**Domain Selection via Environment**:
```bash
# Switch between domains
echo "NGINX_CONFIG_FILE=nginx.conf" > .env              # sanboxaivance.store
echo "NGINX_CONFIG_FILE=nginx-buildup.conf" > .env      # dealstormaibuildup.online

# Deploy with selected domain
docker compose up -d
```

**Renewal Process**:
```bash
# Renew all certificates
docker run --rm -v $(pwd)/certs:/etc/letsencrypt certbot/certbot:latest renew

# Reload nginx to apply renewed certificates
docker compose restart nginx
```

**Monitoring**:
- Certificate expiration tracking for both domains
- Automatic renewal 30 days before expiration
- Health checks for SSL endpoint validity
- Multi-domain certificate validation

### **Security Standards**

**TLS Configuration**:
- **Minimum Protocol**: TLS 1.2
- **Cipher Suites**: Modern, secure algorithms only
- **HSTS**: Enforced with long max-age
- **Certificate Transparency**: Automated CT log submission

**Security Headers**:
```nginx
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Referrer-Policy: no-referrer-when-downgrade
```

## Multi-Domain Architecture

### **Design Philosophy**

Our multi-domain implementation follows pragmatic principles:

- **Single Infrastructure**: One docker-compose setup serves multiple domains
- **Variable-Based Configuration**: Environment variables control domain selection
- **Standalone SSL Method**: Proven reliable method for certificate generation
- **Separate Certificate Management**: Domain-specific SSL certificate workflows

### **Domain Management Strategy**

**Current Domains**:
```
sanboxaivance.store (Primary)
├── Production services
├── Main customer traffic
└── Primary SSL certificate

dealstormaibuildup.online (Secondary)
├── Project-specific deployments
├── Testing and staging
└── Separate SSL certificate
```

**File Structure**:
```
setter/
├── docker-compose.yml                    # Main orchestration
├── docker-compose.cert.yml               # SSL for sanboxaivance.store
├── docker-compose-buildup.cert.yml       # SSL for dealstormaibuildup.online
├── nginx/
│   ├── nginx.conf                        # Config for sanboxaivance.store
│   └── nginx-buildup.conf                # Config for dealstormaibuildup.online
├── certs/
│   └── live/
│       ├── sanboxaivance.store/
│       └── dealstormaibuildup.online/
└── .env                                   # Domain selection variable
```

### **Variable-Based Domain Switching**

**Environment Control**:
```bash
# .env file controls active domain
NGINX_CONFIG_FILE=nginx.conf              # Activates sanboxaivance.store
NGINX_CONFIG_FILE=nginx-buildup.conf      # Activates dealstormaibuildup.online
```

**Docker Compose Integration**:
```yaml
nginx:
  image: nginx:alpine
  volumes:
    - ./nginx/${NGINX_CONFIG_FILE:-nginx.conf}:/etc/nginx/nginx.conf:ro
    - ./certs:/etc/letsencrypt:ro
```

**Benefits**:
- No code duplication in docker-compose.yml
- Single infrastructure supports multiple domains
- Easy domain switching via environment variables
- Consistent service deployment across domains

### **SSL Certificate Workflow**

**Per-Domain Certificate Generation**:

1. **Primary Domain (sanboxaivance.store)**:
   ```bash
   docker compose -f docker-compose.cert.yml up
   ```

2. **Secondary Domain (dealstormaibuildup.online)**:
   ```bash
   docker compose -f docker-compose-buildup.cert.yml up
   ```

**Certificate Storage**:
```
certs/live/
├── sanboxaivance.store/
│   ├── fullchain.pem
│   ├── privkey.pem
│   └── cert.pem
└── dealstormaibuildup.online/
    ├── fullchain.pem
    ├── privkey.pem
    └── cert.pem
```

### **Deployment Workflow**

**New Domain Addition**:
1. Create domain-specific nginx configuration
2. Create domain-specific certificate docker-compose file
3. Generate SSL certificates using standalone method
4. Update .env to select domain configuration
5. Deploy services with `docker compose up -d`

**Domain Switching**:
1. Update `NGINX_CONFIG_FILE` in .env
2. Restart services: `docker compose restart nginx`
3. Verify domain accessibility

### **Operational Benefits**

**Single Infrastructure Management**:
- One codebase serves multiple domains
- Consistent deployment process
- Unified monitoring and logging
- Shared external services (MongoDB Atlas, Redis Cloud)

**Cost Efficiency**:
- Single EC2 instance serves multiple domains
- Shared container resources
- No duplicate infrastructure costs
- Economies of scale for external services

**Maintenance Simplicity**:
- Single point of updates and patches
- Consistent security configurations
- Unified backup and disaster recovery
- Simplified monitoring and alerting

## Migration Strategy

### **Azure Migration Roadmap**

**Pre-Migration Phase**:
1. **Performance Baseline**: Measure current OpenAI API latency
2. **Azure VM Sizing**: Equivalent compute resources to current EC2
3. **Network Testing**: Validate connectivity to MongoDB Atlas and Redis Cloud
4. **DNS Preparation**: Lower TTL values for faster cutover

**Migration Execution**:
1. **Parallel Deployment**: Azure VM with identical configuration
2. **Data Validation**: Ensure external services connectivity
3. **SSL Re-provisioning**: Let's Encrypt certificates for new IP
4. **DNS Cutover**: Update A records to Azure VM
5. **Monitoring**: Validate performance improvements

**Post-Migration Validation**:
- **Latency Improvements**: Expected 70-80% reduction to OpenAI
- **Throughput Gains**: 40-60% improvement in Celery task processing
- **Cost Analysis**: Compare total cloud costs (compute + egress)

### **Migration Benefits**

**Performance Gains**:
- **OpenAI API Latency**: 80-120ms → 10-30ms
- **User Experience**: Noticeably faster response times
- **Background Processing**: More efficient task execution
- **Rate Limit Optimization**: Better utilization of API quotas

**Cost Optimization**:
- **Egress Elimination**: No cross-cloud data transfer charges
- **Azure Credits**: Potential AI workload discounts
- **Operational Efficiency**: Reduced complexity in cloud-to-cloud calls

## Monitoring and Observability

### **Application Monitoring**

**Health Checks**:
- **Application Level**: Flask health endpoints
- **Infrastructure Level**: Container health checks
- **External Dependencies**: MongoDB Atlas and Redis Cloud connectivity

**Logging Strategy**:
- **Centralized Logging**: Docker compose logs aggregation
- **Structured Logging**: JSON format with correlation IDs
- **Log Levels**: Appropriate leveling for production debugging
- **Retention**: Configurable retention policies

### **Performance Monitoring**

**Key Metrics**:
- **Response Times**: API endpoint performance
- **Task Queue Health**: Celery worker performance
- **External API Latency**: OpenAI and other third-party services
- **Resource Utilization**: CPU, memory, and network usage

**Alerting**:
- **Certificate Expiration**: 30-day advance warnings
- **Service Health**: Immediate alerts for service failures
- **Performance Degradation**: Threshold-based alerting
- **External Service Issues**: Dependency failure notifications

### **Business Intelligence**

**Flower Dashboard**:
- **Queue Length**: Monitor task backlog
- **Worker Performance**: Track processing efficiency
- **Failed Tasks**: Identify and retry failed operations
- **Peak Usage**: Capacity planning insights

**Portainer Interface**:
- **Container Management**: Start, stop, restart services
- **Resource Monitoring**: Real-time resource usage
- **Log Access**: Quick access to service logs
- **Image Management**: Container image lifecycle

## Security Guidelines

### **Network Security**

**EC2 Security Groups**:
- **Inbound Rules**: 
  - Port 22 (SSH): Restricted IP ranges only
  - Port 80 (HTTP): 0.0.0.0/0 (for Let's Encrypt validation)
  - Port 443 (HTTPS): 0.0.0.0/0 (public web traffic)
- **Outbound Rules**: All traffic (managed services communication)

**Internal Network Security**:
- **Container Isolation**: Bridge network for service communication
- **Service Communication**: Internal hostnames, no external exposure
- **Administrative Access**: Portainer and Flower behind authentication

### **Data Security**

**Secrets Management**:
- **Environment Variables**: Non-committed .env files
- **API Keys**: Rotated regularly, stored securely
- **Database Credentials**: MongoDB Atlas managed authentication
- **SSL Private Keys**: Protected file permissions, backup strategies

**Data Protection**:
- **Encryption in Transit**: All external communications over TLS
- **Database Encryption**: MongoDB Atlas encryption at rest
- **Cache Encryption**: Redis Cloud with encryption enabled
- **Backup Security**: Automated, encrypted backups

### **Access Control**

**Administrative Access**:
- **SSH Access**: Key-based authentication only
- **Container Access**: Docker exec for debugging only
- **Service Dashboards**: Protected with authentication
- **DNS Management**: Restricted access to Route53/Azure DNS

**Application Security**:
- **API Authentication**: JWT-based authentication system
- **Rate Limiting**: Request throttling for API endpoints
- **Input Validation**: Comprehensive request validation
- **Error Handling**: No sensitive information in error responses

## Cost Optimization

### **Current Cost Structure**

**AWS Costs**:
- **EC2 Instance**: Predictable monthly compute costs
- **Data Transfer**: Egress charges for OpenAI API calls
- **Route53**: Minimal DNS hosting costs
- **Monitoring**: Basic CloudWatch usage

**External Service Costs**:
- **MongoDB Atlas**: Tiered pricing based on usage
- **Redis Cloud**: Memory-based pricing model
- **Let's Encrypt**: Free SSL certificates
- **Domain Registration**: Annual domain costs

### **Cost Optimization Strategies**

**Current Optimizations**:
- **Single Instance**: Avoid complex multi-instance setups
- **Managed Services**: Leverage external expertise for databases
- **Free SSL**: Let's Encrypt instead of commercial certificates
- **Efficient Scaling**: Right-sized compute resources

**Future Optimizations**:
- **Azure Migration**: Eliminate cross-cloud egress charges
- **Reserved Instances**: Long-term compute commitments
- **Auto-scaling**: Dynamic resource allocation
- **CDN Integration**: Reduce bandwidth costs for static assets

### **Resource Planning**

**Capacity Management**:
- **CPU**: Monitor Celery worker utilization
- **Memory**: Track application memory usage patterns
- **Storage**: Plan for log growth and SSL certificate storage
- **Network**: Monitor OpenAI API call volumes

**Scaling Triggers**:
- **Horizontal Scaling**: Additional Celery workers
- **Vertical Scaling**: Larger instance types
- **Load Balancing**: Multiple instance deployment
- **CDN Implementation**: Global content distribution

## Future Roadmap

### **Short-term Goals (3-6 months)**

**Infrastructure Improvements**:
- ✅ **SSL Automation**: Complete Let's Encrypt integration
- ✅ **Multi-Domain Support**: Successfully implemented with variable-based configuration
- ✅ **N8N Gateway Integration**: Implemented as primary request entry point
- 🔄 **Monitoring Enhancement**: Advanced application monitoring
- 📋 **Backup Strategy**: Automated backup verification
- 🔧 **Performance Tuning**: Optimize Celery worker configuration

**N8N Workflow Gateway Achievements**:
- ✅ **Subdomain Configuration**: n8n.localhost routing implemented
- ✅ **Webhook Processing**: SETTER workflow with input validation
- ✅ **Service Integration**: Seamless N8N to Setter Service communication
- ✅ **Error Handling**: Consistent error response formatting
- ✅ **Development Tools**: Test scripts and automation tools

**Multi-Domain Achievements**:
- ✅ **Standalone SSL Method**: Proven reliable for production deployment
- ✅ **Variable-Based Configuration**: Seamless domain switching implementation
- ✅ **Certificate Management**: Automated renewal for multiple domains
- ✅ **Documentation**: Complete multi-domain deployment guide

**Operational Excellence**:
- **CI/CD Pipeline**: Automated deployment processes
- **Infrastructure as Code**: Terraform or similar tooling
- **Security Hardening**: Regular security audits and updates
- **Documentation**: Comprehensive runbooks and procedures

### **Medium-term Goals (6-12 months)**

**Azure Migration**:
- **Migration Planning**: Detailed migration strategy
- **Performance Testing**: Validate Azure performance improvements
- **Cost Analysis**: Comprehensive cost comparison
- **Risk Mitigation**: Rollback procedures and contingency plans
- **Multi-Domain Migration**: Seamless domain migration to Azure infrastructure

**Architecture Evolution**:
- **Microservices Evaluation**: Assess microservices transition benefits
- **Container Orchestration**: Evaluate Kubernetes adoption
- **Database Optimization**: Review MongoDB Atlas configuration
- **Caching Strategy**: Enhanced Redis utilization
- **Domain Scaling**: Infrastructure for additional domains as needed

### **Long-term Vision (12+ months)**

**Multi-Cloud Strategy**:
- **Cloud Agnostic Deployment**: Standardized deployment across clouds
- **Disaster Recovery**: Multi-region backup and recovery
- **Global Distribution**: Geographic distribution for performance
- **Cost Arbitrage**: Optimize costs across cloud providers

**Technology Evolution**:
- **Serverless Integration**: Evaluate serverless computing benefits
- **Edge Computing**: CDN and edge function utilization
- **AI/ML Optimization**: Specialized AI infrastructure considerations
- **Container Security**: Advanced container security practices

## Compliance and Best Practices

### **Development Practices**

**Code Organization**:
- **Hexagonal Architecture**: Maintain clean architecture principles
- **Domain-Driven Design**: Preserve business logic separation
- **Configuration Management**: External configuration for all environments
- **Testing Strategy**: Comprehensive testing for infrastructure changes

**Deployment Practices**:
- **Blue-Green Deployment**: Zero-downtime deployment strategies
- **Rollback Procedures**: Quick rollback capabilities
- **Health Validation**: Automated health checks post-deployment
- **Monitoring Integration**: Deployment monitoring and alerting

### **Operational Practices**

**Change Management**:
- **Infrastructure Changes**: Documented change procedures
- **Security Updates**: Regular security patch management
- **Capacity Planning**: Proactive resource planning
- **Incident Response**: Clear incident response procedures

**Documentation Standards**:
- **Architecture Documentation**: Up-to-date system architecture
- **Runbook Maintenance**: Operational procedures documentation
- **Disaster Recovery**: Recovery procedures and contact information
- **Knowledge Transfer**: Team knowledge sharing practices

## Conclusion

This infrastructure strategy balances **pragmatism with scalability**, **cost-effectiveness with performance**, and **simplicity with future flexibility**. The current monorepo approach provides rapid development velocity while maintaining the foundation for future architectural evolution.

The **N8N Gateway implementation** establishes a robust workflow automation layer that preprocesses and validates external requests before they reach the Setter Service. This architecture provides enhanced input validation, data transformation capabilities, and centralized error handling.

The **multi-domain implementation** demonstrates our ability to scale infrastructure efficiently while maintaining operational simplicity. The cloud-agnostic design ensures that migration to Azure (or any other cloud provider) remains straightforward, while the hybrid architecture leverages the best of both managed services and custom application deployment.

**Key Infrastructure Achievements:**
- ✅ **N8N Workflow Gateway**: Implemented as primary entry point for external requests
- ✅ **Webhook Processing Pipeline**: SETTER workflow with validation and transformation
- ✅ **Subdomain Architecture**: n8n.localhost routing for development environment
- ✅ **Successful Multi-Domain Deployment**: sanboxaivance.store and dealstormaibuildup.online
- ✅ **Reliable SSL Management**: Standalone method proven in production
- ✅ **Variable-Based Configuration**: Flexible domain switching capability
- ✅ **Pragmatic Architecture**: Single infrastructure serving multiple domains

**N8N Gateway Benefits:**
- ✅ **Input Validation**: Centralized validation of required fields before processing
- ✅ **Data Transformation**: Standardization and enrichment of incoming payloads
- ✅ **Error Handling**: Consistent error response formatting across all endpoints
- ✅ **Service Integration**: Seamless communication with Setter Service internal APIs
- ✅ **Monitoring**: Built-in execution tracking and workflow analytics

Regular review and updates of this document ensure that infrastructure decisions remain aligned with business objectives and technical requirements as the Setter Service platform continues to evolve.

---

**Document Version**: 1.0  
**Last Updated**: July 2025  
**Next Review**: October 2025  
**Owner**: Infrastructure Team  
**Approved By**: Technical Leadership
