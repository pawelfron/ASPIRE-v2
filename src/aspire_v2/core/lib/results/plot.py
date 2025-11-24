from ..interfaces import Result

import plotly.graph_objects as go


class PlotResult(Result):
    def __init__(self, figure: go.Figure):
        self.fig = figure

    def serialize(self):
        return {"type": "plot", "value": self.fig.to_dict()}
