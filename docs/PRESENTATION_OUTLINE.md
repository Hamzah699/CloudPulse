# CloudPulse — FT-III Presentation Deck Outline (10 Slides)

Use this outline for your final evaluation presentation and viva demonstration.

---

### Slide 1: Title & Introduction
- **Project Name**: CloudPulse — Serverless Website and API Uptime Monitoring and Incident Alerting Platform
- **Course**: FT-III Cloud Computing Practical Examination
- **Student Name & Roll Number**: [Your Name / Roll No]
- **Key Proposition**: A multi-tier, zero-idle-cost cloud architecture on AWS providing real-time HTTP health checks, socket-level latency analysis, automated incident management, and SNS email alerts.

---

### Slide 2: Problem Statement & Motivation
- **The Challenge**: Traditional monitoring tools (Datadog, Pingdom) are expensive (\$30–\$300/month). Self-hosted open-source solutions rely on always-on virtual machines (EC2) that waste 95%+ of compute capacity sitting idle between check intervals.
- **The Solution**: An event-driven serverless architecture that pays purely per millisecond of check execution time, stores telemetry with automated TTL expiration, and scales to zero when idle.

---

### Slide 3: Cloud System Architecture
- **Visual**: CloudPulse AWS Architecture Diagram.
- **Service Stack**:
  - **Client & CDN**: React + Vite + Tailwind SPA hosted on Amazon S3 and delivered globally via Amazon CloudFront.
  - **Identity**: Amazon Cognito User Pool with JWT token verification.
  - **Ingress**: Amazon API Gateway (HTTP API v2) with CORS and Cognito Authorizer.
  - **Compute**: AWS Lambda (Python 3.13) for API operations and health check execution.
  - **Database**: Amazon DynamoDB with On-Demand Capacity and automated TTL.
  - **Scheduler**: Amazon EventBridge Scheduler (rate: 1 minute).
  - **Alerts**: Amazon SNS Topic delivering formatted email notifications.
  - **Monitoring**: Amazon CloudWatch Logs and Metric Alarms.
  - **IaC**: AWS SAM (`template.yaml`) for 100% reproducible deployment.

---

### Slide 4: Core Technical Features
- **Real Socket Latency Metrics**: High-resolution measurement of DNS lookup time, TCP handshake, Time to First Byte (TTFB), and total response latency.
- **Incident State Machine**: Tracks consecutive check failures to prevent false alarms; opens incident upon crossing threshold; automatically resolves upon sustained recovery.
- **Multi-Method Support**: Supports GET, POST, HEAD, PUT, custom headers, and request bodies.
- **Interactive UI**: Responsive dashboard featuring Recharts latency trend graphs, uptime percentages, and telemetry logs.

---

### Slide 5: Cloud Security & SSRF Defense in Depth
- **The SSRF Threat**: Outbound probers are vulnerable to Server-Side Request Forgery if users submit private endpoints or AWS instance metadata addresses (`169.254.169.254`).
- **CloudPulse Countermeasures**:
  - Pre-request DNS resolution with IP inspection (`ipaddress` module).
  - Strict blocking of private RFC1918 blocks, loopback (`127.0.0.1`), and link-local ranges.
  - Custom redirect interception (`SafeRedirectSession`) validating all redirect hops.
  - Least-privilege IAM policies strictly scoped to table and topic ARNs.

---

### Slide 6: Database Design & Storage Optimization
- **Monitors Table**: Stores target URLs, methods, intervals, thresholds, and aggregate metrics.
- **Checks Table**: Time-series telemetry keyed by `monitor_id` and `timestamp`.
  - **DynamoDB Time to Live (TTL)**: Automatically purges records older than 30 days without consuming WCU or incurring costs.
- **Incidents Table**: Tracks active and historical outages, root causes, duration, and acknowledgment timestamps.

---

### Slide 7: Automation & Alerting Pipeline
- **EventBridge Scheduler**: Replaces legacy cron servers; triggers prober Lambda every 60 seconds with millisecond precision and built-in retry handling.
- **Amazon SNS Integration**: Dispatches formatted incident alerts detailing monitor name, target URL, timestamp, error cause, and downtime duration directly to subscriber emails.

---

### Slide 8: Cost Analysis & AWS Free Tier Optimization
- **Zero-Idle Baseline**: Lambda, EventBridge, API Gateway, DynamoDB, and SNS incur zero cost when no events occur.
- **AWS Free Tier Coverage**:
  - Lambda: 1,000,000 free invocations/month (CloudPulse uses ~53,000/month).
  - DynamoDB: 25GB free storage.
  - SNS: 1,000 free email notifications/month.
- **Total Operational Cost**: **\$0.00 / month** within AWS Free Tier; < \$2.50/month for 25 production monitors post-free tier.

---

### Slide 9: Live Technical Results & Demonstration
- **Dashboard Walkthrough**:
  1. Add a monitor with SSRF security verification.
  2. Inspect real-time status and Recharts latency trend graphs.
  3. Simulate an outage (pointing to `500` status endpoint) and observe consecutive failure counting.
  4. Demonstrate automated incident creation and receipt of the SNS alert email.
  5. Restore endpoint and observe automated incident resolution and downtime calculation.
  6. Demonstrate the interactive SSRF verification sandbox.

---

### Slide 10: Conclusion & Future Scope
- **Evaluation Summary**: Full working serverless cloud architecture fulfilling all FT-III criteria: cloud design, IaC implementation, least-privilege IAM, real telemetry, automated alerting, and cost optimization.
- **Future Enhancements**:
  - Multi-region Lambda deployment (US, EU, APAC) for global latency triangulation.
  - Webhook integration with Slack and Microsoft Teams.
  - TLS/SSL certificate expiration countdown alarms.
