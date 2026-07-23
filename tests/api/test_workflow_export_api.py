"""API coverage for standalone workflow ZIP downloads."""

import io
import zipfile

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_download_standalone_workflow():
    response = client.get("/api/workflows/supervisor_simple/export")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert "supervisor_simple-standalone.zip" in response.headers[
        "content-disposition"
    ]
    assert int(response.headers["x-exported-file-count"]) > 0
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        assert (
            "supervisor_simple-standalone/standalone_workflow/runtime.py"
            in archive.namelist()
        )


def test_download_unknown_workflow_returns_404():
    response = client.get("/api/workflows/missing_workflow/export")
    assert response.status_code == 404
