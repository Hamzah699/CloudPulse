"""
Storage package factory for CloudPulse.
Returns DynamoDBStorage when in production AWS, or LocalStorage during local development.
"""

import os
from .db_interface import DatabaseInterface
from .local_storage import LocalStorage

_storage_instance = None


def get_storage(reset: bool = False) -> DatabaseInterface:
    global _storage_instance
    if _storage_instance is not None and not reset:
        return _storage_instance

    backend = os.environ.get("STORAGE_BACKEND", "").lower()
    is_aws_lambda = bool(os.environ.get("AWS_LAMBDA_FUNCTION_NAME") or os.environ.get("AWS_EXECUTION_ENV"))
    force_local = os.environ.get("USE_LOCAL_STORAGE", "auto").lower() in ("true", "1", "yes")

    # In AWS Lambda or when explicitly set to dynamodb and not forcing local
    if (backend == "dynamodb" or is_aws_lambda) and not force_local:
        from .dynamodb_storage import DynamoDBStorage
        _storage_instance = DynamoDBStorage()
    else:
        db_path = os.environ.get("SQLITE_DB_PATH", "cloudpulse.db")
        _storage_instance = LocalStorage(db_path=db_path)

    return _storage_instance
