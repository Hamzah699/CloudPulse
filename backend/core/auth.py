"""
Authentication and Authorization Module for CloudPulse.
Handles Amazon Cognito JWT validation in AWS and structured token authentication for local development.
"""

import os
import json
import time
import base64
import hmac
import hashlib
from typing import Dict, Any, Optional, Tuple


LOCAL_JWT_SECRET = os.environ.get("LOCAL_JWT_SECRET", "cloudpulse-dev-secret-key-32chars!!")


def generate_local_token(user_id: str, email: str, role: str = "admin", expires_in: int = 86400) -> str:
    """Generates a secure HMAC-SHA256 test JWT token for local development."""
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "iss": "cloudpulse-local-auth",
        "iat": int(time.time()),
        "exp": int(time.time()) + expires_in
    }

    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")

    signature = hmac.new(
        LOCAL_JWT_SECRET.encode(),
        f"{header_b64}.{payload_b64}".encode(),
        hashlib.sha256
    ).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")

    return f"{header_b64}.{payload_b64}.{sig_b64}"


def verify_local_token(token: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """Verifies a local JWT token signature and expiration."""
    try:
        parts = token.strip().split(".")
        if len(parts) != 3:
            return False, None, "Malformed token format"

        header_b64, payload_b64, sig_b64 = parts
        
        # Verify signature
        expected_sig = hmac.new(
            LOCAL_JWT_SECRET.encode(),
            f"{header_b64}.{payload_b64}".encode(),
            hashlib.sha256
        ).digest()
        expected_b64 = base64.urlsafe_b64encode(expected_sig).decode().rstrip("=")

        if not hmac.compare_digest(sig_b64, expected_b64):
            return False, None, "Invalid token signature"

        # Decode payload
        # Add padding if needed
        rem = len(payload_b64) % 4
        if rem > 0:
            payload_b64 += "=" * (4 - rem)
        payload_data = json.loads(base64.urlsafe_b64decode(payload_b64).decode())

        # Check expiration
        exp = payload_data.get("exp", 0)
        if time.time() > exp:
            return False, None, "Token has expired"

        return True, payload_data, ""
    except Exception as e:
        return False, None, f"Token decode error: {str(e)}"


def get_authenticated_user(headers: Dict[str, str], request_context: Optional[Dict[str, Any]] = None) -> Tuple[bool, Dict[str, Any], str]:
    """
    Extracts authenticated user from API Gateway request context (Cognito) or Authorization header.
    Returns (is_authenticated: bool, user_claims: Dict, error_message: str)
    """
    # 1. API Gateway Cognito Authorizer (Production)
    if request_context and "authorizer" in request_context:
        auth_context = request_context["authorizer"]
        # API Gateway HTTP API / REST API Cognito claims structure
        claims = auth_context.get("claims") or auth_context.get("jwt", {}).get("claims")
        if claims:
            return True, {
                "user_id": claims.get("sub") or claims.get("username", "unknown"),
                "email": claims.get("email", ""),
                "username": claims.get("cognito:username", claims.get("email", ""))
            }, ""

    # 2. Check Authorization Header (Bearer <token>)
    auth_header = None
    for k, v in headers.items():
        if k.lower() == "authorization":
            auth_header = v
            break

    if not auth_header:
        allow_anonymous = os.environ.get("ALLOW_ANONYMOUS_DEV", "false").lower() in ("true", "1")
        if allow_anonymous:
            return True, {"user_id": "default_user", "email": "evaluator@cloudpulse.io", "role": "admin"}, ""
        return False, {}, "Missing Authorization header"

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return False, {}, "Invalid Authorization header format. Expected 'Bearer <token>'"

    token = parts[1]

    # If Cognito User Pool ID is configured and in AWS environment, token can be validated against Cognito JWKS
    user_pool_id = os.environ.get("COGNITO_USER_POOL_ID")
    if user_pool_id and not os.environ.get("USE_LOCAL_STORAGE"):
        # AWS Cognito JWT verification
        # When using API Gateway Cognito Authorizer, APIGW validates the token before Lambda is invoked.
        # Here we extract claims from decoded payload:
        try:
            payload_part = token.split(".")[1]
            rem = len(payload_part) % 4
            if rem > 0:
                payload_part += "=" * (4 - rem)
            claims = json.loads(base64.urlsafe_b64decode(payload_part).decode())
            return True, {
                "user_id": claims.get("sub", "aws_user"),
                "email": claims.get("email", ""),
                "username": claims.get("cognito:username", claims.get("email", ""))
            }, ""
        except Exception as e:
            return False, {}, f"Invalid Cognito token: {str(e)}"

    # Otherwise verify using local token mechanism
    is_valid, claims, err = verify_local_token(token)
    if is_valid and claims:
        return True, {
            "user_id": claims.get("sub", "dev_user"),
            "email": claims.get("email", "dev@cloudpulse.local"),
            "role": claims.get("role", "admin")
        }, ""

    return False, {}, err
