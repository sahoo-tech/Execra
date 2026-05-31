"""
Locust load testing suite for Execra API.

This module provides a load testing configuration that simulates realistic
user traffic across Execra's core endpoints with weighted task distribution.

Load Profile:
- Ramps from 1 to 50 concurrent users over 60 seconds
- Simulates realistic wait times between requests
- Gracefully handles unimplemented or unavailable endpoints

Endpoint Weighting:
- GET /api/v1/status (weight 3) — most common health check
- GET /api/v1/guidance/current (weight 2) — fetch current guidance
- POST /api/v1/guidance/ask (weight 1) — ask a question (slower LLM call)

Run with:
    locust -f tests/load/locustfile.py --host=http://localhost:8000
"""

from locust import HttpUser, task, between, LoadTestShape
import json
import logging

logger = logging.getLogger(__name__)

# Base URL paths
STATUS_ENDPOINT = "/api/v1/status"
GUIDANCE_CURRENT_ENDPOINT = "/api/v1/guidance/current"
GUIDANCE_ASK_ENDPOINT = "/api/v1/guidance/ask"

# Sample question for guidance/ask endpoint
SAMPLE_QUESTION = "Why is it showing an IndexError on line 42?"


class ExecraUser(HttpUser):
    """
    Simulates a user interacting with Execra API.
    
    Realistic behavior:
    - Waits 1-3 seconds between requests
    - Fetches status frequently (weight 3)
    - Checks guidance less frequently (weight 2)
    - Asks questions rarely (weight 1)
    """

    # Wait time between requests (in seconds)
    wait_time = between(1, 3)

    @task(3)
    def get_status(self):
        """
        GET /api/v1/status (weight 3)
        
        Most common request — check system health and uptime.
        Fully implemented and required to succeed.
        """
        with self.client.get(
            STATUS_ENDPOINT,
            catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(
                    f"Status endpoint returned {response.status_code}"
                )
                return

            try:
                data = response.json()
                required_fields = [
                    "status", "version", "uptime_seconds",
                    "active_domain", "active_mode"
                ]
                
                for field in required_fields:
                    if field not in data:
                        response.failure(f"Missing required field: {field}")
                        return
                
                response.success()
            except json.JSONDecodeError:
                response.failure("Invalid JSON response")

    @task(2)
    def get_guidance_current(self):
        """
        GET /api/v1/guidance/current (weight 2)
        
        Fetch current guidance instruction. This endpoint may not yet be
        fully implemented. Gracefully handle 404 or unavailable responses.
        """
        with self.client.get(
            GUIDANCE_CURRENT_ENDPOINT,
            catch_response=True
        ) as response:
            # Endpoint may not be implemented yet
            if response.status_code == 404:
                response.success()  # Expected until endpoint is implemented
                logger.debug("guidance/current endpoint not yet implemented (404)")
                return

            if response.status_code != 200:
                response.failure(
                    f"Guidance endpoint returned {response.status_code}"
                )
                return

            try:
                data = response.json()
                expected_fields = [
                    "instruction", "confidence", "source", "reasoning"
                ]
                
                for field in expected_fields:
                    if field not in data:
                        response.failure(f"Missing expected field: {field}")
                        return
                
                response.success()
            except json.JSONDecodeError:
                response.failure("Invalid JSON response from guidance/current")

    @task(1)
    def post_guidance_ask(self):
        """
        POST /api/v1/guidance/ask (weight 1)
        
        Submit a question to Execra (Active Mode). This endpoint may not yet
        be fully implemented. Gracefully handle 404 or unavailable responses.
        """
        payload = {
            "question": SAMPLE_QUESTION
        }
        
        with self.client.post(
            GUIDANCE_ASK_ENDPOINT,
            json=payload,
            catch_response=True
        ) as response:
            # Endpoint may not be implemented yet
            if response.status_code == 404:
                response.success()  # Expected until endpoint is implemented
                logger.debug("guidance/ask endpoint not yet implemented (404)")
                return

            if response.status_code not in [200, 201]:
                response.failure(
                    f"Guidance ask endpoint returned {response.status_code}"
                )
                return

            try:
                data = response.json()
                expected_fields = [
                    "answer", "confidence", "source", "reasoning"
                ]
                
                for field in expected_fields:
                    if field not in data:
                        response.failure(f"Missing expected field: {field}")
                        return
                
                response.success()
            except json.JSONDecodeError:
                response.failure("Invalid JSON response from guidance/ask")

class StepLoadShape(LoadTestShape):
    """
    Custom Locust load shape.

    Gradually ramps users from 1 → 50 over 60 seconds
    to simulate increasing concurrent traffic.
    """

    spawn_rate = 1

    def tick(self):
        """
        Controls user ramp-up behavior.
        """
        run_time = self.get_run_time()

        # Stop test after 60 seconds
        if run_time > 60:
            return None

        # Gradually increase users from 1 to 50
        users = min(50, int(run_time * (49 / 60)) + 1)

        return (users, self.spawn_rate)
