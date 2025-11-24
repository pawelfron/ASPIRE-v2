from ..interfaces import Result

import pandas as pd


class TableResult(Result):
    def __init__(self, dataframe: pd.DataFrame):
        self.dataframe = dataframe

    def serialize(self):
        data = self.dataframe.to_dict("tight")
        data["data_with_index"] = [
            [index] + values for index, values in zip(data["index"], data["data"])
        ]
        return {
            "type": "table",
            "value": data,
        }
