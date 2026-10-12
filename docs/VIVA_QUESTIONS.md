# CloudPulse — Viva Voce Examination Guide (25+ Questions & Answers)

This guide covers 25+ comprehensive questions and answers designed specifically for the **FT-III Cloud Computing Practical Evaluation**. It encompasses architectural design, service mechanics, security, cost optimization, and trade-offs.

---

### Q1: What is CloudPulse, and what core cloud computing problem does it address?
**Answer**: CloudPulse is a serverless website and API uptime monitoring and incident alerting platform. Traditional uptime tools (e.g. Pingdom, Datadog) either require costly subscriptions or rely on always-on virtual machines (EC2) that waste compute resources during idle intervals. CloudPulse implements an on-demand, event-driven serverless architecture that executes health checks with millisecond billing, stores check telemetry with automatic expiration, and dispatches incident alerts via Amazon SNS, operating entirely within the AWS Free Tier.

---

### Q2: Why choose AWS Lambda over containerized solutions like Amazon ECS or EKS?
**Answer**:
1. **Event-driven episodic nature**: Health checks run periodically (e.g., once per minute) and execute in 200–500ms. An EC2 or ECS container would sit idle for over 95% of each minute while incurring continuous 24/7 billing.
2. **Zero cluster management**: Lambda eliminates OS patching, container orchestration overhead, and cluster capacity autoscaling.
3. **Cost**: Lambda provides 1,000,000 free requests and 3.2M seconds of compute time every month forever.

---

### Q3: Explain how EventBridge Scheduler triggers the health check Lambda.
**Answer**: Amazon EventBridge Scheduler maintains an internal distributed timer. When configured with `rate(1 minute)`, EventBridge assumes an IAM execution role with `lambda:InvokeFunction` permissions and invokes `cloudpulse-checker` asynchronously. Unlike legacy CloudWatch Events, EventBridge Scheduler supports flexible time windows, automatic retry policies with exponential backoff, and direct Dead-Letter Queue (DLQ) integration.

---

### Q4: How is Server-Side Request Forgery (SSRF) prevented in CloudPulse?
**Answer**: SSRF is a critical vulnerability where an attacker inputs an internal address (e.g. `http://169.254.169.254` or `http://10.0.0.1`) forcing the cloud server to query its private metadata or internal services.
CloudPulse prevents this through a multi-stage validation engine in `ssrf_guard.py`:
1. **Protocol Restriction**: Only `http` and `https` schemes are allowed. Schemes like `file://`, `gopher://`, or `ftp://` are rejected.
2. **DNS Pre-resolution**: Before establishing a socket connection, `socket.getaddrinfo()` resolves the domain name to all associated IP addresses.
3. **IP Range Filtering**: Each resolved IP is parsed via Python's `ipaddress` module and checked against private RFC1918 blocks (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), loopback (`127.0.0.0/8`), link-local/AWS IMDS (`169.254.0.0/16`), and carrier-grade NAT blocks.
4. **Safe Redirect Interception**: When following HTTP redirects (301/302), a custom requests session (`SafeRedirectSession`) inspects the `Location` header before the redirect is dispatched to prevent open-redirect SSRF bypasses.

---

### Q5: What is the AWS Instance Metadata Service (169.254.169.254), and why is it dangerous?
**Answer**: AWS EC2 and container instances expose a link-local IP (`169.254.169.254`) that returns instance configuration, security group details, and temporary IAM execution role credentials via IMDSv1 without authentication. If an attacker submits `http://169.254.169.254/latest/meta-data/iam/security-credentials/`, they can steal the Lambda function's IAM session tokens and compromise the AWS account. CloudPulse explicitly blocks all requests to `169.254.0.0/16`.

---

### Q6: How does DynamoDB Time to Live (TTL) work, and why is it used here?
**Answer**: Continuous health checks produce hundreds of thousands of records over time. In `ChecksTable`, each item stores an epoch timestamp attribute named `ttl` set to `timestamp + 30 days`. DynamoDB runs a background process that identifies and deletes expired items without consuming read or write capacity units (WCU/RCU) and with zero financial cost, avoiding database bloat without writing custom batch-delete scripts.

---

### Q7: Why use Amazon API Gateway HTTP API instead of REST API?
**Answer**:
1. **Cost**: HTTP APIs cost \$1.00 per million requests vs \$3.50 per million for REST APIs (a 71% cost savings).
2. **Latency**: HTTP APIs have a streamlined architecture optimized for serverless proxies, resulting in lower p99 latency.
3. **Native Features**: Built-in support for CORS and native JWT authorizers (Amazon Cognito) without requiring a separate custom Lambda authorizer.

---

### Q8: Explain the state machine used for incident creation and resolution.
**Answer**:
- **Incident Creation**: A single HTTP check failure transitions a monitor to `DEGRADED`. An incident is only opened when the number of consecutive failures reaches the configured `failure_threshold` (e.g. 2 or 3). This avoids false alarms from temporary network hiccups.
- **Incident Resolution**: Once an incident is `OPEN`, it remains open until the endpoint records consecutive successful checks equal to `recovery_threshold` (e.g. 2). Upon meeting this threshold, the incident status transitions to `RESOLVED`, downtime duration is calculated, and an SNS recovery alert is dispatched.

---

### Q9: How does Amazon SNS deliver email notifications?
**Answer**: Amazon SNS (Simple Notification Service) is a managed pub/sub messaging service. In CloudPulse:
1. `template.yaml` provisions an SNS topic `cloudpulse-alerts`.
2. An `AWS::SNS::Subscription` registers the subscriber's email.
3. AWS dispatches a verification email requiring the user to click "Confirm Subscription".
4. When `boto3.client('sns').publish()` is invoked with subject and message attributes, SNS formats and delivers the notification to all confirmed email endpoints.

---

### Q10: How does Cognito User Pool authentication work with API Gateway?
**Answer**:
1. The user logs in via SRP (Secure Remote Password) or username/password against the Cognito User Pool.
2. Cognito validates credentials and issues signed RS256 JWT tokens: `IdToken`, `AccessToken`, and `RefreshToken`.
3. The frontend passes the `IdToken` in the `Authorization: Bearer <token>` HTTP header.
4. API Gateway's built-in JWT Authorizer verifies the cryptographic signature against Cognito's JWKS (JSON Web Key Set), checks the issuer URL and audience client ID, and extracts user claims before invoking the Lambda function.

---

### Q11: What is the difference between AWS SAM and CloudFormation?
**Answer**: AWS SAM (Serverless Application Model) is an open-source extension of CloudFormation specifically designed for serverless architectures. SAM introduces simplified resource abstractions like `AWS::Serverless::Function` and `AWS::Serverless::HttpApi`. During `sam build` or deployment, the SAM macro transforms these concise resource definitions into standard, verbose AWS CloudFormation resources.

---

### Q12: How are Lambda cold starts minimized in Python?
**Answer**:
1. **Lightweight Dependencies**: Standard library modules (`urllib`, `socket`, `sqlite3`, `ipaddress`) are preferred where possible.
2. **Initialization Re-use**: Global scope objects (e.g., `boto3.resource('dynamodb')`, HTTP sessions) are initialized outside the handler function so they persist across warm Lambda invocations.
3. **Optimal Memory Allocation**: Allocating 256MB of RAM provides proportional CPU allocation that reduces cold start initialization time to < 200ms.

---

### Q13: How does CloudPulse handle high-resolution socket timings?
**Answer**: Using Python's `time.perf_counter()`, CloudPulse measures:
- **DNS Lookup Time**: Duration of `socket.getaddrinfo()` in milliseconds.
- **TCP Connect Time**: Duration of raw socket connection `sock.connect((ip, port))`.
- **TTFB (Time to First Byte)**: Elapsed time between request transmission and receipt of the first HTTP response header byte.
- **Total Latency**: End-to-end round trip time.

---

### Q14: What is Origin Access Control (OAC) in CloudFront and S3?
**Answer**: OAC is AWS's modern, secure mechanism for authenticating CloudFront requests to Amazon S3. S3 buckets can block all public access completely. CloudFront signs requests using SigV4, and S3 bucket policies grant access exclusively to the specific CloudFront distribution ARN via the `cloudfront.amazonaws.com` service principal, preventing direct public access to S3.

---

### Q15: How does the local development mode work without AWS credentials?
**Answer**:
CloudPulse implements an abstraction layer with the `DatabaseInterface` and `Notifier` classes:
- When running locally (`USE_LOCAL_STORAGE=true`), the system injects `LocalStorage` (backed by SQLite) and `LocalNotifier` (inbox log).
- `backend/local_server.py` converts standard HTTP requests into AWS API Gateway event dictionaries and invokes `handlers.api.handler()` directly.
- This ensures that 100% of business logic and state machine transitions execute identically in local dev and cloud production.

---

### Q16: How is least-privilege IAM applied to the Lambda functions?
**Answer**: Neither Lambda function uses wildcard `*` permissions:
- `ApiFunction` and `HealthCheckerFunction` are granted `dynamodb:PutItem`, `GetItem`, `Query`, `UpdateItem`, and `DeleteItem` strictly scoped to the table ARNs (`arn:aws:dynamodb:*:*:table/cloudpulse-*`).
- SNS publishing is restricted strictly to `arn:aws:sns:*:*:cloudpulse-alerts-*`.
- Logging is restricted to standard CloudWatch log groups.

---

### Q17: What happens if an endpoint returns a 301 or 302 redirect?
**Answer**: The custom `SafeRedirectSession` handles redirects safely:
- It tracks the redirect hop count (up to 5 redirects max to prevent infinite redirect loops).
- Crucially, it intercepts each `Location` header URL and runs it through `ssrf_guard.validate_target_url()`. If an endpoint attempts an open-redirect to an internal IP (e.g., `http://169.254.169.254`), the redirect is blocked immediately.

---

### Q18: What is the role of CloudWatch Metric Alarms?
**Answer**: CloudWatch monitors operational telemetry from the Lambda functions. CloudPulse provisions `CloudPulseAlarmCheckFailures` on the `Errors` metric in the `AWS/Lambda` namespace. If the prober Lambda encounters exceptions across 5 minutes, CloudWatch automatically transitions to `ALARM` state and sends an alert to the SNS topic.

---

### Q19: Why use On-Demand capacity for DynamoDB rather than Provisioned?
**Answer**: On-Demand mode (`PAY_PER_REQUEST`) charges exclusively per read/write unit consumed. Since monitoring checks run at discrete intervals and dashboard access is intermittent, provisioning static Read/Write Capacity Units (RCUs/WCUs) would waste money on idle capacity. On-Demand scales up instantly to absorb bursts and scales down to zero cost when idle.

---

### Q20: How are CORS preflight OPTIONS requests handled?
**Answer**: In API Gateway HTTP API, CORS headers are configured declaratively in `template.yaml`. Additionally, `handlers/api.py` checks `http_method == 'OPTIONS'` and immediately returns an HTTP 200 response with `Access-Control-Allow-Origin: *` and allowed headers, preventing CORS errors in browsers.

---

### Q21: What is the difference between synchronous and asynchronous Lambda invocations?
**Answer**:
- **API Gateway**: Invokes Lambda **synchronously** (`RequestResponse`). API Gateway waits for Lambda to finish and returns the response to the frontend.
- **EventBridge Scheduler**: Invokes Lambda **asynchronously** (`Event`). EventBridge hands off the event payload to Lambda's internal queue and acknowledges immediately, with automatic retries if Lambda fails.

---

### Q22: What happens if a monitored endpoint is slow to respond?
**Answer**: Each monitor has a configurable `timeout_seconds` attribute (e.g., 5s, 10s). The HTTP client enforces this timeout strictly. If the target server fails to complete headers or body within the window, a `requests.exceptions.Timeout` exception is caught, the check is marked `DOWN`, and latency is recorded as the elapsed timeout interval.

---

### Q23: How is uptime percentage calculated?
**Answer**:
$$\text{Uptime Percentage} = \left(\frac{\text{Successful Checks (status = UP)}}{\text{Total Checks Executed}}\right) \times 100$$
This is computed incrementally on every check execution and updated on the monitor's DynamoDB record.

---

### Q24: Can CloudPulse monitor POST or PUT APIs that require request bodies and auth tokens?
**Answer**: Yes. CloudPulse supports `method` (GET, POST, HEAD, PUT, DELETE), custom HTTP headers (e.g. `{"Authorization": "Bearer token", "Content-Type": "application/json"}`), and a custom JSON request payload body.

---

### Q25: How would you scale CloudPulse to monitor 100,000 websites simultaneously?
**Answer**:
1. **Fan-Out via SQS**: Instead of having a single Lambda check all monitors, EventBridge would trigger a Dispatcher Lambda that pushes monitor batches into an Amazon SQS FIFO queue.
2. **Worker Pool Autoscaling**: A fleet of Worker Lambdas (with concurrency up to 1,000) would consume batches from SQS and execute probes concurrently in parallel.
3. **Multi-Region Probing**: Deploy worker Lambdas in `eu-west-1`, `ap-southeast-1`, and `us-west-2` to measure latency from multiple global perspectives and detect geographic outages.
