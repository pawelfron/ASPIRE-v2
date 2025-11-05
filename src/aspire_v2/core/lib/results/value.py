from ..interfaces import Result


class ValueResult(Result):
    def __init__(self, value):
        self.value = value

    def serialize(self):
        return {"value": self.value}
