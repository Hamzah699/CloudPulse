# CloudPulse — System Architecture & Technical Design

CloudPulse is a production-grade, serverless website and API uptime monitoring and incident alerting platform built on Amazon Web Services (AWS). It continuously probes distributed HTTP/HTTPS endpoints, collects high-resolution socket latency telemetry (DNS, TCP, TTFB), evaluates incident transitions through a state machine, and publishes multi-channel alert notifications via Amazon SNS.

---

## 1. High-Level Architecture Diagram

```mermaid
flowchart TD
    subgraph ClientTier ["1. Client & Delivery Tier"]
        User["DevOps Engineer / Browser"]
        CF["Amazon CloudFront (CDN Edge)"]
        S3Web["Amazon S3 (SPA Static Hosting)"]
        Cognito["Amazon Cognito (User Pool & JWT Auth)"]
    end

    subgraph ApiTier ["2. Ingress & Routing Tier"]
        APIGW["Amazon API Gateway (HTTP API v2)"]
    end

    subgraph ComputeTier ["3. Serverless Compute Tier"]
        ApiLambda["AWS Lambda: ApiFunction\n(CRUD, Telemetry, History)"]
        CheckerLambda["AWS Lambda: HealthCheckerFunction\n(SSRF Guard + HTTP Socket Prober)"]
        Scheduler["Amazon EventBridge Scheduler\n(rate: 1 minute)"]
    end

    subgraph StorageTier ["4. Persistence & Messaging Tier"]
        DDBMonitors[("DynamoDB: MonitorsTable")]
        DDBChecks[("DynamoDB: ChecksTable (TTL 30d)")]
        DDBIncidents[("DynamoDB: IncidentsTable")]
        SNSTopic["Amazon SNS: AlertsTopic"]
        EmailSub["DevOps Email Subscribers"]
    end

    subgraph Observability ["5. Observability Tier"]
        CWLogs["CloudWatch Logs"]
        CWAlarms["CloudWatch Metric Alarms"]
    end

    %% Client flows
    User -->|HTTPS Request| CF
    CF -->|Origin Fetch| S3Web
    User -->|Sign In / SRP Auth| Cognito
    User -->|API Calls + JWT Bearer| APIGW

    %% Ingress flows
    APIGW -->|Cognito JWT Validation| Cognito
    APIGW -->|Event Proxy| ApiLambda

    %% Compute flows
    Scheduler -->|Every 60s Invoke| CheckerLambda
    CheckerLambda -->|Fetch Active Monitors| DDBMonitors
    CheckerLambda -->|Store Telemetry| DDBChecks
    CheckerLambda -->|Update Incident State| DDBIncidents
    CheckerLambda -->|Threshold Breach / Recovery| SNSTopic

    ApiLambda -->|Read/Write Config| DDBMonitors
    ApiLambda -->|Query Telemetry| DDBChecks
    ApiLambda -->|Acknowledge / List| DDBIncidents

    %% Alerts & Logs
    SNSTopic -->|Email Notification| EmailSub
    CheckerLambda -->|Structured Logs| CWLogs
    ApiLambda -->|Structured Logs| CWLogs
    CWLogs -->|Error Spikes| CWAlarms
    CWAlarms -->|Trigger Alarm| SNSTopic
```

---

## 2. Telemetry & Probe Execution Flow

```mermaid
sequenceDiagram
    autonumber
    participant EB as EventBridge Scheduler
    participant L as HealthChecker Lambda
    participant Guard as SSRF Guard Engine
    participant Target as Target Endpoint (Web/API)
    participant DDB as Amazon DynamoDB
    participant SNS as Amazon SNS
    participant Dev as DevOps Engineer (Email)

    EB->>L: Trigger invocation (rate: 1 minute)
    L->>DDB: Scan active monitors (status != PAUSED)
    DDB-->>L: Return monitors list

    loop For each active monitor
        L->>Guard: Validate target URL against SSRF policy
        alt Target resolves to private IP or 169.254.169.254
            Guard-->>L: Reject (SSRF Violation)
            L->>DDB: Record CheckResult (DOWN, Reason: SSRF Violation)
        else Target is safe public host
            Guard-->>L: Approved (Resolved IPs)
            L->>Target: Measure DNS Lookup (ms)
            L->>Target: Measure TCP Connect (ms)
            L->>Target: Execute HTTP request (GET/POST)
            Target-->>L: HTTP Response (Status code, TTFB, Headers)
            L->>DDB: PutItem in ChecksTable (TTL: 30 days)
        end

        L->>DDB: Fetch active incident (if any)
        L->>L: Evaluate state machine (failures vs threshold)

        alt Consecutive Failures >= Threshold (Outage)
            L->>DDB: PutItem Incident (Status: OPEN)
            L->>SNS: Publish Alert ([CloudPulse Alert] INCIDENT OPEN)
            SNS->>Dev: Deliver incident email
        else Consecutive Passes >= Recovery Threshold (Recovered)
            L->>DDB: UpdateItem Incident (Status: RESOLVED, Duration)
            L->>SNS: Publish Alert ([CloudPulse Alert] RESOLVED)
            SNS->>Dev: Deliver recovery email
        end

        L->>DDB: UpdateItem MonitorsTable (Uptime %, Last Latency, Status)
    end
```

---

## 3. Key Architectural Decisions & Trade-Offs

### 3.1. AWS Lambda vs. Containerized Services (ECS / EC2)
- **Choice**: Serverless AWS Lambda.
- **Rationale**: An uptime monitor's workload is naturally episodic: health checks execute every minute and complete in 1–3 seconds. Running dedicated EC2 instances or ECS tasks incurs 24/7 idle server costs. Lambda executes on-demand, scales horizontally with zero capacity management, and falls comfortably within the AWS Free Tier (1 million free requests/month).

### 3.2. EventBridge Scheduler vs. Traditional Cron / Celery
- **Choice**: Amazon EventBridge Scheduler.
- **Rationale**: Traditional cron setups require persistent servers and introduce single points of failure (SPOF). EventBridge Scheduler is fully managed, highly available across multiple Availability Zones, supports automated retry policies with Dead-Letter Queues (DLQ), and invokes Lambda functions with millisecond accuracy.

### 3.3. Amazon DynamoDB vs. Relational RDS
- **Choice**: Amazon DynamoDB (On-Demand Capacity).
- **Rationale**: Uptime checks generate high-write, predictable key-value telemetry. DynamoDB delivers single-digit millisecond latency, scales seamlessly without connection pool bottlenecks, and provides native **Time to Live (TTL)** which automatically deletes historical checks older than 30 days without scheduled cron cleanup scripts or storage bloat.

### 3.4. Amazon Cognito vs. Self-Hosted Authentication
- **Choice**: Amazon Cognito User Pool + JWT Authorizer.
- **Rationale**: Cognito offloads password hashing (SRP protocol), token signing (RS256), email verification, and session management. API Gateway validates Cognito JWT tokens at the ingress boundary *before* invoking Lambda, protecting backend compute from unauthorized requests and Denial of Service (DoS) attacks.

---

## 4. Defense-in-Depth Security Model

1. **Strict SSRF Defense**:
   - Outgoing probe URLs are resolved to their target IP addresses using DNS before connection establishment.
   - Any address falling within private RFC 1918 blocks (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), loopback (`127.0.0.0/8`, `::1`), link-local (`169.254.0.0/16`), or AWS IMDS (`169.254.169.254`) is immediately aborted.
   - Redirect chains are intercepted (`SafeRedirectSession`); each subsequent redirect target is independently validated against the SSRF blocklist before the hop is made.
2. **Least-Privilege IAM Execution Roles**:
   - Lambda functions are granted only the precise IAM actions needed (`dynamodb:PutItem`, `dynamodb:GetItem`, `dynamodb:Query`, `sns:Publish`) scoped strictly to the specific resource ARNs created by the CloudFormation stack.
3. **Encrypted Ingress & Storage**:
   - S3 static assets are strictly private; public direct access is disabled via S3 Block Public Access. Only Amazon CloudFront via Origin Access Control (OAC) can read website objects.
   - DynamoDB tables utilize AWS-managed encryption at rest (KMS).
   - In-transit communication is exclusively TLS 1.3 / HTTPS.
