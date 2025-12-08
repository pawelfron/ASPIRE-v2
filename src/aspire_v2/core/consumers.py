from channels.generic.websocket import AsyncJsonWebsocketConsumer


class ReportGenerationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.report_id = self.scope["url_route"]["kwargs"]["report_id"]
        self.room_group_name = f"report.{self.report_id}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def analysis_complete(self, event):
        await self.send_json(
            {
                "type": "analysis_complete",
                "progress": event["progress"],
                "total": event["total"],
            }
        )

    async def report_complete(self, event):
        await self.send_json(
            {
                "type": "report_complete",
                "total": event["total"],
            },
            close=True,
        )

    async def analysis_error(self, event):
        await self.send_json(
            {
                "type": "analysis_error",
                "analysis_type": event["analysis_type"],
                "error": event["error"],
            },
            close=True,
        )
