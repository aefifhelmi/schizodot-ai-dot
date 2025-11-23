# app/repositories/__init__.py
"""
Data access layer for DynamoDB operations
"""
from repositories.jobs_repository import jobs_repo, JobsRepository
from repositories.results_repository import results_repo, ResultsRepository

__all__ = [
    "jobs_repo",
    "JobsRepository",
    "results_repo",
    "ResultsRepository",
]
