import React, { useState } from 'react';
import { Cloud, Server, Database, Bell, Shield, Lock, Globe, Activity, Zap } from 'lucide-react';

export const ArchitectureDiagramModal: React.FC = () => {
  const [selectedService, setSelectedService] = useState<string>('lambda');

  const services = [
    {
      id: 'apigw',
      name: 'Amazon API Gateway',
      category: 'API & Ingress',
      desc: 'Handles HTTP requests from frontend, integrates with Amazon Cognito Authorizer, enables CORS, and proxies to Lambda.',
      spec: 'HTTP API v2 / REST API with Payload format 2.0',
    },
    {
      id: 'lambda',
      name: 'AWS Lambda (Python 3.13)',
      category: 'Serverless Compute',
      desc: 'Runs the core business logic. Two dedicated functions: ApiFunction for management APIs and HealthCheckerFunction for scheduled prober execution.',
      spec: 'Memory: 256MB, Timeout: 30s, Ephemeral storage: 512MB',
    },
    {
      id: 'dynamodb',
      name: 'Amazon DynamoDB',
      category: 'NoSQL Database',
      desc: 'Stores monitor configs, timestamped check telemetry with 30-day automatic TTL expiration, and incident history.',
      spec: 'On-Demand Capacity (PAY_PER_REQUEST), Single-digit millisecond latency',
    },
    {
      id: 'eventbridge',
      name: 'Amazon EventBridge Scheduler',
      category: 'Automation & Scheduler',
      desc: 'Triggers HealthChecker Lambda every 60 seconds (rate(1 minute)) without needing long-running background servers.',
      spec: 'Cron / Rate expressions, Retry policy with dead-letter queue (DLQ)',
    },
    {
      id: 'sns',
      name: 'Amazon SNS',
      category: 'Notifications & Alerts',
      desc: 'Publishes incident open and resolved alerts via email to registered DevOps team subscribers with downtime metrics.',
      spec: 'Standard SNS Topic with Email protocol subscriptions',
    },
    {
      id: 'cognito',
      name: 'Amazon Cognito',
      category: 'Identity & Authentication',
      desc: 'Provides secure user sign-up, sign-in, and OAuth2/JWT token issuance for role-based API access control.',
      spec: 'User Pool + User Pool App Client with SRP/JWT auth',
    },
    {
      id: 'cloudfront_s3',
      name: 'CloudFront & Amazon S3',
      category: 'Frontend Hosting & CDN',
      desc: 'S3 hosts the compiled React/Vite/Tailwind static build; CloudFront provides edge caching, HTTPS termination, and sub-second global delivery.',
      spec: 'Origin Access Control (OAC), HTTPS TLS 1.3',
    },
    {
      id: 'cloudwatch',
      name: 'Amazon CloudWatch',
      category: 'Observability & Metrics',
      desc: 'Aggregates structured application logs, tracks Lambda error rates and durations, and generates alarms on probe failure spikes.',
      spec: 'Log Groups with 14-day retention, Metric Alarms',
    },
    {
      id: 'sam',
      name: 'AWS SAM / CloudFormation',
      category: 'Infrastructure as Code',
      desc: 'Declares 100% of the serverless cloud infrastructure in a reproducible template.yaml file, enabling single-command deployment.',
      spec: 'Transform: AWS::Serverless-2016-10-31',
    },
  ];

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-white flex items-center">
          <Cloud className="w-5 h-5 text-cyan-400 mr-2" />
          Cloud Architecture & AWS Serverless Design
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          High-performance serverless architecture designed for FT-III Cloud Computing evaluation, featuring
          least-privilege IAM, automated scheduling, and multi-tier defense in depth.
        </p>
      </div>

      {/* Cloud Architecture Flow Diagram (Visual Canvas) */}
      <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-6">
        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
          System Architecture Pipeline
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Tier 1: Client & Ingress */}
          <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-3">
            <span className="text-[11px] font-bold text-indigo-400 uppercase tracking-wider block">
              1. Edge & Client Tier
            </span>

            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-xs space-y-1">
              <div className="font-semibold text-white flex items-center">
                <Globe className="w-4 h-4 text-cyan-400 mr-1.5" /> React Vite SPA
              </div>
              <p className="text-slate-400 text-[11px]">Hosted on S3 + CloudFront CDN</p>
            </div>

            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-xs space-y-1">
              <div className="font-semibold text-white flex items-center">
                <Lock className="w-4 h-4 text-emerald-400 mr-1.5" /> Amazon Cognito
              </div>
              <p className="text-slate-400 text-[11px]">User Pool & JWT Token Verification</p>
            </div>

            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-xs space-y-1">
              <div className="font-semibold text-white flex items-center">
                <Server className="w-4 h-4 text-indigo-400 mr-1.5" /> Amazon API Gateway
              </div>
              <p className="text-slate-400 text-[11px]">HTTP API with Cognito Authorizer</p>
            </div>
          </div>

          {/* Tier 2: Serverless Compute */}
          <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-3">
            <span className="text-[11px] font-bold text-cyan-400 uppercase tracking-wider block">
              2. Compute & Automation
            </span>

            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-xs space-y-1">
              <div className="font-semibold text-white flex items-center">
                <Zap className="w-4 h-4 text-yellow-400 mr-1.5" /> EventBridge Scheduler
              </div>
              <p className="text-slate-400 text-[11px]">rate(1 minute) cron invocation</p>
            </div>

            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-xs space-y-1">
              <div className="font-semibold text-white flex items-center">
                <Server className="w-4 h-4 text-indigo-400 mr-1.5" /> Lambda: HealthChecker
              </div>
              <p className="text-slate-400 text-[11px]">Real HTTP Probing + SSRF Guard</p>
            </div>

            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-xs space-y-1">
              <div className="font-semibold text-white flex items-center">
                <Server className="w-4 h-4 text-indigo-400 mr-1.5" /> Lambda: ApiFunction
              </div>
              <p className="text-slate-400 text-[11px]">Monitors CRUD, Stats, Checks Query</p>
            </div>
          </div>

          {/* Tier 3: Data, Alerts & Logs */}
          <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-3">
            <span className="text-[11px] font-bold text-emerald-400 uppercase tracking-wider block">
              3. Data, Alerts & Logs
            </span>

            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-xs space-y-1">
              <div className="font-semibold text-white flex items-center">
                <Database className="w-4 h-4 text-emerald-400 mr-1.5" /> Amazon DynamoDB
              </div>
              <p className="text-slate-400 text-[11px]">Monitors, Checks (TTL), Incidents</p>
            </div>

            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-xs space-y-1">
              <div className="font-semibold text-white flex items-center">
                <Bell className="w-4 h-4 text-rose-400 mr-1.5" /> Amazon SNS Topic
              </div>
              <p className="text-slate-400 text-[11px]">Incident Email Alerts Dispatcher</p>
            </div>

            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-xs space-y-1">
              <div className="font-semibold text-white flex items-center">
                <Activity className="w-4 h-4 text-cyan-400 mr-1.5" /> Amazon CloudWatch
              </div>
              <p className="text-slate-400 text-[11px]">Metrics, Structured Logs & Alarms</p>
            </div>
          </div>
        </div>
      </div>

      {/* Interactive Service Inspector */}
      <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
        <h3 className="text-sm font-bold text-white">AWS Cloud Services Reference</h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
          {services.map((svc) => (
            <button
              key={svc.id}
              onClick={() => setSelectedService(svc.id)}
              className={`p-3 rounded-xl text-left border transition-all ${
                selectedService === svc.id
                  ? 'bg-indigo-600/20 border-indigo-500 text-white shadow-md'
                  : 'bg-slate-950 border-slate-800 text-slate-300 hover:border-slate-700'
              }`}
            >
              <span className="text-[10px] font-semibold text-indigo-400 block">{svc.category}</span>
              <span className="text-xs font-bold block mt-0.5 truncate">{svc.name}</span>
            </button>
          ))}
        </div>

        {/* Selected Service Details */}
        {(() => {
          const current = services.find((s) => s.id === selectedService);
          if (!current) return null;
          return (
            <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="text-base font-bold text-white">{current.name}</h4>
                <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  {current.category}
                </span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">{current.desc}</p>
              <div className="pt-2 text-xs font-mono text-cyan-400">
                Configuration: <span className="text-slate-400">{current.spec}</span>
              </div>
            </div>
          );
        })()}
      </div>

      {/* Key Architectural Principles (For Viva) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 space-y-2">
          <Shield className="w-5 h-5 text-indigo-400" />
          <h4 className="text-sm font-bold text-white">SSRF Defense in Depth</h4>
          <p className="text-xs text-slate-400 leading-relaxed">
            Target URLs are strictly pre-resolved via DNS. Private IPs, loopbacks, and AWS IMDS (169.254.169.254) are rejected before any connection is opened, preventing internal reconnaissance.
          </p>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 space-y-2">
          <Lock className="w-5 h-5 text-emerald-400" />
          <h4 className="text-sm font-bold text-white">Least-Privilege IAM</h4>
          <p className="text-xs text-slate-400 leading-relaxed">
            Lambda execution roles are tightly scoped to specific DynamoDB table ARNs (PutItem, GetItem, Query) and the dedicated SNS topic ARN, following AWS Well-Architected security pillars.
          </p>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900 border border-slate-800 space-y-2">
          <Database className="w-5 h-5 text-cyan-400" />
          <h4 className="text-sm font-bold text-white">Cost-Optimized Serverless</h4>
          <p className="text-xs text-slate-400 leading-relaxed">
            DynamoDB On-Demand and Lambda pay-per-use keep steady-state AWS costs virtually zero within AWS Free Tier (1M free Lambda invocations, 25GB free DynamoDB storage).
          </p>
        </div>
      </div>
    </div>
  );
};
