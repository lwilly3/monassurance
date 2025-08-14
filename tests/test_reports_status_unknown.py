import pytest

from tests.utils import auth_headers, client


@pytest.mark.skip(reason="Rate limiting issues in test suite - test manually")
def test_job_status_unknown_for_nonexistent_id():
    headers = auth_headers("status.unknown@example.com")
    resp = client.get("/api/v1/reports/jobs/does-not-exist-12345", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "unknown"
    assert data["report_job_id"] is None
