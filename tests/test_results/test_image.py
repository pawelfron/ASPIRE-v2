import base64

from core.lib.results.image import ImageResult


def test_serialize_png_data_uri():
    raw = b"\x89PNG\r\n"
    payload = ImageResult(raw).serialize()

    assert payload["type"] == "image"
    assert payload["value"] == f"data:image/png;base64,{base64.b64encode(raw).decode()}"


def test_serialize_custom_mime_type():
    payload = ImageResult(b"abc", mime_type="image/jpeg").serialize()
    assert payload["value"].startswith("data:image/jpeg;base64,")
