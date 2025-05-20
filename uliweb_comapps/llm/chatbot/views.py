#!/usr/bin/env python
# -*- coding: utf-8 -*-

from werkzeug import Response
from uliweb import expose, functions, request


@expose('/chatbot')
class Chatbot:
    @expose('')
    def index(self):
        return {}

    def api_stream(self):
        input = request.values.get('input', '你好')
        return Response(
            functions.openai_event_stream(input),
            mimetype="text/event-stream",
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'
            }
        )
