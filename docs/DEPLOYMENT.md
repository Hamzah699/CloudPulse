# CloudPulse — Deployment & Operations Guide

This guide details the complete deployment process for CloudPulse, covering local development mode, automated testing, AWS SAM cloud provisioning, static frontend hosting on Amazon S3 and CloudFront, troubleshooting, and teardown cleanup.

---

## 1. Prerequisites

Before deploying to AWS, ensure the following tools are installed:
- **Python**: Version 3.10+ (Python 3.13 tested)
- **Node.js**: Version 18+ (Node.js 20/22/26 tested) with npm
- **AWS CLI**: Configured with credentials (`aws configure`) having CloudFormation, Lambda, DynamoDB, APIGateway, Cognito, and S3 administrative permissions.
- **AWS SAM CLI**: Version 1.100+ (`sam --version`)

---

## 2. Local Development (Without AWS Credentials)

CloudPulse includes a high-fidelity local simulation server that executes the exact same Lambda handlers using local SQLite persistence and local notification logging:

### Step 2.1. Backend Setup & Run
```bash
# 1. Install backend dependencies
python -m pip install -r backend/requirements.txt

# 2. Run backend test suite
python -m pytest backend/tests -v

# 3. Start local development server (Port 5000)
python backend/local_server.py
```
The server will boot on `http://localhost:5000` with the background EventBridge scheduler simulation active.

### Step 2.2. Frontend Setup & Run
In a separate terminal:
```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install npm dependencies
npm install

# 3. Run production build test
npm run build

# 4. Start Vite development server
npm run dev
```
Open `http://localhost:3000` in your browser. All API calls are automatically routed to `http://localhost:5000`.

---

## 3. AWS Cloud Deployment (Production)

### Step 3.1. Build Serverless Artifacts with AWS SAM
From the root repository directory:
```bash
sam build --template-file infrastructure/template.yaml
```
SAM packages the Python Lambda functions, validates dependencies, and prepares the CloudFormation changeset.

### Step 3.2. Deploy Infrastructure Stack
```bash
sam deploy --guided
```
When prompted by SAM CLI:
- **Stack Name**: `cloudpulse-stack`
- **AWS Region**: `us-east-1` (or your preferred region)
- **Parameter Environment**: `prod`
- **Parameter AlertNotificationEmail**: `your-devops-email@domain.com` (Enter a real email to receive SNS alerts)
- **Confirm changes before deploy**: `Y`
- **Allow SAM CLI IAM role creation**: `Y`
- **Disable rollback**: `N`
- **Save arguments to configuration file**: `Y`

SAM will provision:
1. Amazon Cognito User Pool & App Client
2. Amazon DynamoDB Tables (`cloudpulse-monitors-prod`, `cloudpulse-checks-prod`, `cloudpulse-incidents-prod`)
3. Amazon SNS Topic (`cloudpulse-alerts-prod`) with your email subscription
4. Amazon API Gateway (HTTP API v2) with CORS and Cognito Authorizer
5. AWS Lambda Functions (`cloudpulse-api-prod`, `cloudpulse-checker-prod`)
6. Amazon EventBridge Scheduler rule (`rate(1 minute)`)
7. Amazon CloudWatch Metric Alarms & Log Groups
8. Amazon S3 Bucket & CloudFront Distribution

*Note: Immediately check your email inbox and click **"Confirm subscription"** in the email sent by AWS Notifications to enable incident alerting.*

### Step 3.3. Deploy Frontend to S3 and CloudFront

1. Note the `ApiEndpoint` and `CloudFrontEndpoint` from the SAM outputs:
   ```bash
   # Retrieve stack outputs
   aws cloudformation describe-stacks --stack-name cloudpulse-stack --query "Stacks[0].Outputs" --output table
   ```

2. Configure production API URL in `frontend/.env.production`:
   ```env
   VITE_API_URL=https://<your-api-id>.execute-api.us-east-1.amazonaws.com
   ```

3. Build the production React SPA:
   ```bash
   cd frontend
   npm run build
   ```

4. Upload assets to S3 and invalidate CloudFront CDN cache:
   ```bash
   # Set your bucket name and distribution ID from SAM outputs
   export BUCKET_NAME=$(aws cloudformation describe-stacks --stack-name cloudpulse-stack --query "Stacks[0].Outputs[?OutputKey=='FrontendBucketName'].OutputValue" --output text)
   export CF_DIST_ID=$(aws cloudformation describe-stacks --stack-name cloudpulse-stack --query "Stacks[0].Outputs[?OutputKey=='CloudFrontDistributionId'].OutputValue" --output text)

   # Sync compiled files
   aws s3 sync dist/ s3://$BUCKET_NAME/ --delete

   # Invalidate CloudFront edge cache
   aws cloudfront create-invalidation --distribution-id $CF_DIST_ID --paths "/*"
   ```

5. Visit your CloudFront URL (`https://<distribution-id>.cloudfront.net`) to access the live cloud platform!

---

## 4. Verification & Operational Testing

1. **Verify API Gateway Health**:
   ```bash
   curl -i https://<your-api-id>.execute-api.us-east-1.amazonaws.com/health
   # Expected: HTTP 200 {"status": "healthy", "service": "CloudPulse API"}
   ```

2. **Inspect CloudWatch Structured Logs**:
   ```bash
   # Stream real-time logs from the health checker Lambda
   aws logs tail /aws/lambda/cloudpulse-checker-prod --follow
   ```

3. **Verify Incident State Machine**:
   - Create a test monitor pointing to `https://httpbin.org/status/500`.
   - Set failure threshold to `2`.
   - Wait 2 minutes for EventBridge to execute two checks.
   - Observe an incident automatically opened in the dashboard.
   - Verify receipt of the SNS outage alert email.
   - Edit the monitor URL to `https://httpbin.org/status/200`.
   - Observe the incident automatically transition to **RESOLVED** with downtime metrics and receipt of the recovery email!

---

## 5. Troubleshooting Common Issues

| Issue | Root Cause | Resolution |
| :--- | :--- | :--- |
| `SSRF Security Violation` | Target URL resolves to 127.0.0.1, 169.254.169.254, or RFC1918 private IP | Working as designed. CloudPulse enforces strict outbound filtering to protect cloud infrastructure. |
| `401 Unauthorized` on API call | Missing or expired Cognito JWT token | Sign in via the "Sign In" modal to obtain a fresh authenticated bearer token. |
| SNS Email not received | Subscription pending confirmation | Check spam/junk folder for "AWS Notification - Subscription Confirmation" and click the confirmation link. |
| `Missing Authorization Header` in local dev | Local dev request without credentials | The local mock auth provider returns test tokens via `POST /api/auth/login`. |
| CloudFront returns 403 Forbidden | S3 bucket permissions or OAC mismatch | Verify `AWS::CloudFront::OriginAccessControl` is associated with the S3 origin in `template.yaml`. |

---

## 6. Teardown & Resource Cleanup

To eliminate any ongoing charges after your evaluation or demonstration:

```bash
# 1. Empty the S3 frontend bucket (CloudFormation cannot delete non-empty buckets)
aws s3 rm s3://$BUCKET_NAME/ --recursive

# 2. Delete the AWS SAM infrastructure stack
sam delete --stack-name cloudpulse-stack --no-prompts
```
All Lambda functions, DynamoDB tables, API Gateway routes, Cognito pools, SNS topics, and CloudFront distributions will be cleanly deleted within 3–5 minutes.
