# CloudPulse — Serverless Website and API Uptime Monitoring Platform

![CloudPulse Banner](https://img.shields.io/badge/AWS-Serverless-orange?style=for-the-badge&logo=amazon-aws)
![Python](https://img.shields.io/badge/Python-3.13-blue?style=for-the-badge&logo=python)
![React](https://img.shields.io/badge/React-19-cyan?style=for-the-badge&logo=react)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue?style=for-the-badge&logo=typescript)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**CloudPulse** is a serverless website and API uptime monitoring and incident alerting platform built on Amazon Web Services (AWS) for the **FT-III Cloud Computing Practical Examination**.

### 🌐 Live Production Deployment
- **Live Web Application (AWS Amplify):** [https://main.dw9pu8rtsj47n.amplifyapp.com](https://main.dw9pu8rtsj47n.amplifyapp.com)
- **Live HTTP API Gateway:** `https://9mo8pytaqj.execute-api.ap-south-1.amazonaws.com`
- **AWS Region:** `ap-south-1` (Mumbai)
- **Deployment Status:** Active & Tested (Serverless Free Tier)

---

## 🌟 Technology Stack

| Component | Technology | AWS Service |
| :--- | :--- | :--- |
| **Frontend SPA** | React 19, TypeScript, Vite, Tailwind CSS 4, Recharts, Lucide | Amazon S3 + Amazon CloudFront (CDN) |
| **Backend Compute** | Python 3.13 | AWS Lambda |
| **API Layer** | RESTful / JSON HTTP API with CORS & JWT Authorizer | Amazon API Gateway (HTTP API v2) |
| **Database** | NoSQL Key-Value & Time Series with 30-Day TTL | Amazon DynamoDB (On-Demand) |
| **Job Scheduler** | Automated 60-second periodic probe invocation | Amazon EventBridge Scheduler |
| **Alerting** | Real-time incident outage & recovery emails | Amazon SNS (Simple Notification Service) |
| **Identity & Auth** | OAuth2 / SRP Authentication & JWT verification | Amazon Cognito User Pool & App Client |
| **Observability** | Structured JSON logging, metrics, alarms | Amazon CloudWatch |
| **Infrastructure as Code** | Declarative cloud resource provisioning | AWS SAM & CloudFormation |

---

## 🚀 Key Features

1. **Responsive Real-Time Dashboard**:
   - Total monitors, Operational/Degraded/Down breakdown, overall uptime %, and average latency.
   - Interactive Recharts area charts displaying socket response time trends over time.
   - Live status badges, search by name/URL/tags, and filtering by status.
2. **Complete Monitor Lifecycle Management**:
   - Add, edit, pause, resume, and delete monitors.
   - Configurable check intervals (1m, 5m, 15m, 30m, 60m) and timeouts (3s–30s).
   - Support for GET, POST, HEAD, PUT with custom HTTP headers and JSON request payloads.
3. **High-Resolution Socket Telemetry**:
   - Granular breakdown of DNS lookup time, TCP connection handshake, Time to First Byte (TTFB), and total round-trip latency.
4. **State-Machine Incident Management**:
   - Tracks consecutive check failures to eliminate false positives from transient blips.
   - Automatically opens an incident when consecutive failures cross the configured `failure_threshold`.
   - Automatically resolves incidents with calculated total downtime duration upon sustained recovery (`recovery_threshold`).
5. **Amazon SNS Email Alerts**:
   - Formatted notifications dispatched to subscribed engineers detailing monitor name, target URL, root cause error, consecutive failure count, and downtime duration.
6. **Strict Multi-Layer SSRF Defense**:
   - Pre-request DNS resolution checks before connection establishment.
   - Blocks private RFC1918 networks (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), loopback (`127.0.0.1`), link-local/AWS IMDS (`169.254.169.254`), and bogons.
   - Safe redirect interception: validates every hop in 301/302 redirect chains.
7. **Zero-Idle-Cost Serverless Economics**:
   - Runs 100% within the AWS Free Tier (\$0.00 baseline monthly cost).
   - DynamoDB Time to Live (TTL) automatically cleans up 30-day telemetry records with zero read/write capacity consumption.
8. **Dual-Mode Operation (Local Dev & Production)**:
   - Run locally without AWS credentials via SQLite and local notification logger.
   - Deploy to AWS with a single command via AWS SAM.

---

## 📂 Project Structure

```text
CloudPulse/
├── backend/
│   ├── core/                  # Core engines (SSRF guard, HTTP prober, incident engine, auth, models)
│   ├── handlers/              # AWS Lambda entrypoints (api.py, checker.py)
│   ├── storage/               # Persistence layer (DynamoDBStorage & LocalStorage SQLite)
│   ├── notify/                # Notification layer (SNSNotifier & LocalNotifier)
│   ├── tests/                 # Comprehensive pytest test suite (18 unit & integration tests)
│   ├── local_server.py        # Local API Gateway & EventBridge simulation server (Port 5000)
│   └── requirements.txt       # Python dependencies (boto3, requests, flask, pytest)
├── frontend/
│   ├── src/
│   │   ├── api/               # API client & authentication
│   │   ├── components/        # React components (Navbar, Stats, Cards, Charts, Modals, Sandbox)
│   │   ├── types/             # TypeScript domain interfaces
│   │   ├── App.tsx            # Application shell
│   │   └── main.tsx
│   ├── package.json           # React, Vite, Tailwind, Recharts, Lucide
│   └── vite.config.ts         # Vite configuration with Tailwind v4 & API proxy
├── infrastructure/
│   ├── template.yaml          # AWS SAM Infrastructure as Code (100% cloud resources)
│   ├── samconfig.toml         # SAM CLI deployment parameters
│   └── iam-policies.json      # Documented least-privilege IAM policies
├── docs/
│   ├── ARCHITECTURE.md        # Detailed architecture, flow diagrams, service trade-offs
│   ├── DEPLOYMENT.md          # Step-by-step AWS deployment and teardown instructions
│   ├── COST_ANALYSIS.md       # AWS Free Tier breakdown & production scaling estimates
│   ├── VIVA_QUESTIONS.md      # 25+ comprehensive viva questions with in-depth answers
│   └── PRESENTATION_OUTLINE.md# 10-slide evaluation presentation outline
├── .env.example               # Environment variables configuration reference
└── README.md                  # Project overview
```

---

## ⚡ Quickstart Guide

### 1. Run Automated Test Suites

```bash
# Run backend pytest suite (SSRF guard, HTTP prober, incident engine, storage, API handlers)
python -m pytest backend/tests -v

# Run frontend production build test
cd frontend && npm run build
```

### 2. Run Locally (No AWS Credentials Needed)

**Terminal 1 — Local Backend & EventBridge Scheduler Simulator:**
```bash
python backend/local_server.py
```
*Runs on `http://localhost:5000` with SQLite persistence and active EventBridge timer.*

**Terminal 2 — React Frontend:**
```bash
cd frontend
npm run dev
```
*Open `http://localhost:3000` in your browser.*

### 3. Deploy to AWS Cloud

```bash
# 1. Build serverless artifacts
sam build --template-file infrastructure/template.yaml

# 2. Deploy infrastructure stack
sam deploy --guided

# 3. Deploy frontend SPA to S3 + CloudFront
cd frontend
npm run build
aws s3 sync dist/ s3://<Your-S3-Bucket-Name>/ --delete
aws cloudfront create-invalidation --distribution-id <Your-Dist-Id> --paths "/*"
```

---

## 📚 Evaluation & Viva Documentation

- **[Architecture Deep-Dive](file:///c:/CloudPulse/docs/ARCHITECTURE.md)**: System flow diagrams, service selection rationales, and security models.
- **[Deployment & Cleanup Guide](file:///c:/CloudPulse/docs/DEPLOYMENT.md)**: Step-by-step setup, verification commands, and safe teardown.
- **[AWS Cost & Free Tier Analysis](file:///c:/CloudPulse/docs/COST_ANALYSIS.md)**: In-depth economic comparison and zero-cost design.
- **[Viva Voce Examination Guide](file:///c:/CloudPulse/docs/VIVA_QUESTIONS.md)**: 25+ detailed questions and answers covering cloud computing concepts.
- **[Presentation Outline](file:///c:/CloudPulse/docs/PRESENTATION_OUTLINE.md)**: 10-slide evaluation presentation deck structure.

---

## 🛡️ Security & SSRF Protection Verification

To verify SSRF defense live:
1. Open the **SSRF Sandbox** tab in the dashboard.
2. Test preset attacks:
   - `http://169.254.169.254/latest/meta-data` -> **BLOCKED** (AWS Instance Metadata Service)
   - `http://127.0.0.1:8080/admin` -> **BLOCKED** (Loopback network)
   - `http://192.168.1.1/router` -> **BLOCKED** (Private RFC1918 subnet)
   - `https://dns.google` -> **PASSED** (Public IP resolution verified)

---

## 📄 License
MIT License. Developed for the FT-III Cloud Computing Practical Examination.
