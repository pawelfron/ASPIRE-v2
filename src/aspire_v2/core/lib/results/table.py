from ..interfaces import Result

import pandas as pd


class TableResult(Result):
    def __init__(self, dataframe: pd.DataFrame):
        self.dataframe = dataframe

    def serialize(self):
        return {
            "type": "table",
            "value": self.dataframe.to_dict("records"),
        }
