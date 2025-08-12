from tests.utils import auth_headers, client


def test_update_storage_config_s3_missing_bucket():
    headers = auth_headers("admin.s3a@example.com")
    resp = client.put("/api/v1/admin/storage-config", headers=headers, json={"backend": "s3"})
    assert resp.status_code == 400


def test_update_storage_config_s3_ok():
    headers = auth_headers("admin.s3b@example.com")
    resp = client.put(
        "/api/v1/admin/storage-config",
        headers=headers,
        json={"backend": "s3", "s3_bucket": "demo-bucket", "s3_region": "eu-west-3"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["backend"] == "s3"
    assert body["s3_bucket"] == "demo-bucket"
