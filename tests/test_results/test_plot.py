import plotly.graph_objects as go

from core.lib.results.plot import PlotResult


def test_serialize_round_trips_plotly_figure():
    figure = go.Figure(go.Scatter(x=[0, 1], y=[2, 3], name="run"))
    payload = PlotResult(figure).serialize()

    assert payload["type"] == "plot"
    assert "data" in payload["value"]
    assert "layout" in payload["value"]
    assert payload["value"]["data"][0]["name"] == "run"
    assert payload["value"]["data"][0]["x"] == [0, 1]
    assert payload["value"]["data"][0]["y"] == [2, 3]
