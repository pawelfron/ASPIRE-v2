from ..interfaces import Result


class CompositeResult(Result):
    def __init__(self, children: dict[str, Result]):
        self.children = children

    def serialize(self):
        return {
            "type": "composite",
            "value": {
                label: result.serialize() for label, result in self.children.items()
            },
        }
