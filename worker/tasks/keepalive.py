"""Keepalive tasks to keep services awake."""

import logging
import os

import httpx

from worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task
def ping_services():
    """Ping services to keep them awake (for free/starter tier hosting)."""
    results = {
        "api": None,
        "mini_app": None,
    }
    
    # Get service URLs from environment
    webhook_url = os.getenv("WEBHOOK_URL", "")
    mini_app_url = os.getenv("MINI_APP_URL", "")
    
    # Derive API base URL from webhook URL
    api_base_url = webhook_url.split("/webhook")[0] if webhook_url else None
    
    # Ping API health endpoint
    if api_base_url:
        health_url = f"{api_base_url}/health"
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(health_url)
                results["api"] = {
                    "url": health_url,
                    "status_code": response.status_code,
                    "success": response.status_code == 200,
                }
                logger.info(f"Pinged API: {health_url} - Status: {response.status_code}")
        except Exception as e:
            results["api"] = {
                "url": health_url,
                "success": False,
                "error": str(e),
            }
            logger.warning(f"Failed to ping API: {e}")
    else:
        results["api"] = {"skipped": True, "reason": "WEBHOOK_URL not set"}
    
    # Ping Mini App
    if mini_app_url:
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(mini_app_url)
                results["mini_app"] = {
                    "url": mini_app_url,
                    "status_code": response.status_code,
                    "success": response.status_code == 200,
                }
                logger.info(f"Pinged Mini App: {mini_app_url} - Status: {response.status_code}")
        except Exception as e:
            results["mini_app"] = {
                "url": mini_app_url,
                "success": False,
                "error": str(e),
            }
            logger.warning(f"Failed to ping Mini App: {e}")
    else:
        results["mini_app"] = {"skipped": True, "reason": "MINI_APP_URL not set"}
    
    return results
