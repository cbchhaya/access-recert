"""
API Tests for ARAS
==================

Tests for the REST API endpoints.

Author: Chiradeep Chhaya
"""

import pytest
import requests
from datetime import datetime, timedelta
import time

BASE_URL = "http://127.0.0.1:8000"


class TestHealthEndpoints:
    """Test health and status endpoints."""

    def test_health(self):
        """Test health endpoint."""
        resp = requests.get(f"{BASE_URL}/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    def test_status(self):
        """Test status endpoint."""
        resp = requests.get(f"{BASE_URL}/api/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "operational"
        assert "statistics" in data
        assert data["statistics"]["employees"] > 0


class TestWeightsEndpoints:
    """Test proximity weights endpoints."""

    def test_get_weights(self):
        """Test getting current weights."""
        resp = requests.get(f"{BASE_URL}/api/weights")
        assert resp.status_code == 200
        data = resp.json()
        assert "structural" in data
        assert "functional" in data
        assert "behavioral" in data
        assert "temporal" in data
        # Verify they sum to 1
        total = data["structural"] + data["functional"] + data["behavioral"] + data["temporal"]
        assert abs(total - 1.0) < 0.01

    def test_update_weights(self):
        """Test updating weights."""
        new_weights = {
            "structural": 0.20,
            "functional": 0.40,
            "behavioral": 0.30,
            "temporal": 0.10
        }
        resp = requests.put(f"{BASE_URL}/api/weights", json=new_weights)
        assert resp.status_code == 200
        data = resp.json()
        assert data["structural"] == 0.20
        assert data["functional"] == 0.40

    def test_invalid_weights(self):
        """Test that invalid weights are rejected."""
        bad_weights = {
            "structural": 0.50,
            "functional": 0.50,
            "behavioral": 0.50,
            "temporal": 0.50
        }
        resp = requests.put(f"{BASE_URL}/api/weights", json=bad_weights)
        assert resp.status_code == 400


class TestCampaignEndpoints:
    """Test campaign endpoints."""

    @pytest.fixture
    def campaign_data(self):
        """Campaign creation data."""
        return {
            "name": f"Test Campaign {datetime.now().isoformat()}",
            "scope_type": "manager",
            "scope_filter": {"lob": "Technology"},
            "auto_approve_threshold": 80.0,
            "review_threshold": 50.0,
            "due_date": (datetime.now() + timedelta(days=30)).isoformat()
        }

    def test_create_campaign(self, campaign_data):
        """Test campaign creation."""
        resp = requests.post(f"{BASE_URL}/api/campaigns", json=campaign_data)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == campaign_data["name"]
        assert data["status"] == "Draft"
        assert "id" in data
        return data["id"]

    def test_list_campaigns(self, campaign_data):
        """Test listing campaigns."""
        # Create a campaign first
        requests.post(f"{BASE_URL}/api/campaigns", json=campaign_data)

        resp = requests.get(f"{BASE_URL}/api/campaigns")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_get_campaign(self, campaign_data):
        """Test getting campaign details."""
        # Create campaign
        create_resp = requests.post(f"{BASE_URL}/api/campaigns", json=campaign_data)
        campaign_id = create_resp.json()["id"]

        # Get campaign
        resp = requests.get(f"{BASE_URL}/api/campaigns/{campaign_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert "campaign" in data
        assert data["campaign"]["id"] == campaign_id
        assert "total_items" in data

    def test_update_campaign(self, campaign_data):
        """Test updating campaign."""
        # Create campaign
        create_resp = requests.post(f"{BASE_URL}/api/campaigns", json=campaign_data)
        campaign_id = create_resp.json()["id"]

        # Update
        update_data = {"name": "Updated Campaign Name"}
        resp = requests.patch(f"{BASE_URL}/api/campaigns/{campaign_id}", json=update_data)
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Updated Campaign Name"

    def test_campaign_not_found(self):
        """Test 404 for non-existent campaign."""
        resp = requests.get(f"{BASE_URL}/api/campaigns/nonexistent-id")
        assert resp.status_code == 404


class TestEmployeeEndpoints:
    """Test employee endpoints."""

    def test_get_employee(self):
        """Test getting employee details."""
        # First get an employee ID from the database
        status_resp = requests.get(f"{BASE_URL}/api/status")
        assert status_resp.json()["statistics"]["employees"] > 0

        # We'll need to get an actual employee ID
        # For now, test 404 case
        resp = requests.get(f"{BASE_URL}/api/employees/nonexistent")
        assert resp.status_code == 404


class TestAnalyticsEndpoints:
    """Test analytics endpoints."""

    def test_run_analytics(self):
        """Test running analytics."""
        resp = requests.post(f"{BASE_URL}/api/analytics/run")
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert "employees_analyzed" in data["data"]
        assert data["data"]["employees_analyzed"] > 0

    def test_run_analytics_with_filter(self):
        """Test running analytics with LOB filter."""
        resp = requests.post(f"{BASE_URL}/api/analytics/run?lob=Technology")
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["lob_filter"] == "Technology"


class TestAuditEndpoints:
    """Test audit endpoints."""

    def test_list_audit_records(self):
        """Test listing audit records."""
        resp = requests.get(f"{BASE_URL}/api/audit")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data


class TestGraduationEndpoints:
    """Test graduation status endpoints."""

    def test_list_graduation_status(self):
        """Test listing graduation statuses."""
        resp = requests.get(f"{BASE_URL}/api/graduation-status")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)


# Integration test
class TestCampaignWorkflow:
    """Test full campaign workflow."""

    def test_full_workflow(self):
        """Test complete campaign workflow: create -> activate -> review."""
        # 1. Create campaign
        campaign_data = {
            "name": f"Integration Test {datetime.now().isoformat()}",
            "scope_type": "lob",
            "scope_filter": {"lob": "Technology"},
            "auto_approve_threshold": 80.0,
            "review_threshold": 50.0,
            "due_date": (datetime.now() + timedelta(days=30)).isoformat()
        }

        create_resp = requests.post(f"{BASE_URL}/api/campaigns", json=campaign_data)
        assert create_resp.status_code == 201
        campaign_id = create_resp.json()["id"]
        print(f"Created campaign: {campaign_id}")

        # 2. Verify it's in draft status
        get_resp = requests.get(f"{BASE_URL}/api/campaigns/{campaign_id}")
        assert get_resp.json()["campaign"]["status"] == "Draft"

        # 3. Activate campaign (this runs analytics)
        print("Activating campaign (running analytics)...")
        activate_resp = requests.post(f"{BASE_URL}/api/campaigns/{campaign_id}/activate")
        assert activate_resp.status_code == 200
        data = activate_resp.json()
        assert data["campaign"]["status"] == "Active"
        assert data["total_items"] > 0
        print(f"Campaign activated with {data['total_items']} review items")

        # 4. List review items
        items_resp = requests.get(f"{BASE_URL}/api/campaigns/{campaign_id}/review-items")
        assert items_resp.status_code == 200
        items_data = items_resp.json()
        assert items_data["total"] > 0
        print(f"Found {items_data['total']} review items")

        # 5. Get campaign progress
        progress_resp = requests.get(f"{BASE_URL}/api/campaigns/{campaign_id}/progress")
        assert progress_resp.status_code == 200

        print("Full workflow test passed!")


if __name__ == "__main__":
    # Run quick smoke test
    print("Running API smoke tests...")

    # Health check
    resp = requests.get(f"{BASE_URL}/api/health")
    print(f"Health: {resp.json()}")

    # Status
    resp = requests.get(f"{BASE_URL}/api/status")
    print(f"Status: {resp.json()}")

    # Run full workflow test
    print("\n--- Running Full Workflow Test ---")
    test = TestCampaignWorkflow()
    test.test_full_workflow()

    print("\nAll smoke tests passed!")
