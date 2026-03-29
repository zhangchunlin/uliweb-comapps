#!/usr/bin/env python
# -*- coding: utf-8 -*-

from uliweb import expose, functions, request
from uliweb.starlette.responses import StreamingResponse


@expose('/chatbot')
class Chatbot:
    @expose('')
    def index(self):
        return {}

    async def api_stream(self):
        params = await request.get_params()
        user_input = params.get('input', '你好')

        async def event_stream():
            async for chunk in functions.openai_event_stream(user_input):
                yield chunk

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'
            }
        )
