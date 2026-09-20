from ..interfaces import Result

import base64


class ImageResult(Result):
    """A raster image, serialized as an inline data URI."""

    def __init__(self, image: bytes, mime_type: str = "image/png"):
        self.image = image
        self.mime_type = mime_type

    def serialize(self):
        encoded = base64.b64encode(self.image).decode()
        return {
            "type": "image",
            "value": f"data:{self.mime_type};base64,{encoded}",
        }
