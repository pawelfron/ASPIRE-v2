from ..interfaces import Result

import plotly.graph_objects as go

import json


class PlotResult(Result):
    def __init__(self, figure: go.Figure):
        self.fig = figure

    def serialize(self):
        value = json.loads(self.fig.to_json())
        return {"type": "plot", "value": value}
