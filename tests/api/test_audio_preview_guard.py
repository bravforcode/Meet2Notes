from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient


@pytest.mark.parametrize(
    ("method", "headers", "expected"),
    [
        ("GET", {}, 405),
        ("POST", {}, 403),
        ("POST", {"Origin": "http://testserver"}, 403),
        ("POST", {"Origin": "http://evil.test", "X-Meet2Notes-Preview": "1"}, 403),
        ("POST", {"Origin": "http://testserver:9999", "X-Meet2Notes-Preview": "1"}, 403),
        ("POST", {"Origin": "null", "X-Meet2Notes-Preview": "1"}, 403),
        ("POST", {"Origin": "http://testserver", "X-Meet2Notes-Preview": "1"}, 200),
    ],
)
def test_audio_preview_only_probes_for_same_origin_post(
    client: TestClient, method, headers, expected
):
    backend = client.app.state.container.audio_capture_backend
    backend.probe_level = Mock(return_value=0.42)
    response = client.request(method, "/api/audio/sources/synthetic/level", headers=headers)
    assert response.status_code == expected
    if expected == 200:
        backend.probe_level.assert_called_once_with("synthetic")
        assert response.json() == {"source_id": "synthetic", "level": 0.42}
    else:
        backend.probe_level.assert_not_called()
