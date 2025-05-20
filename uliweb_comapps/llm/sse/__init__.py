#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from uliweb import settings
from openai import OpenAI


def openai_event_stream(user_input, api_key=None, base_url=None, model=None):
    client = OpenAI(
        api_key=api_key or settings.LLM.api_key,
        base_url=base_url or settings.LLM.base_url
    )

    messages = [
        {'role': 'user', 'content': user_input}
    ]

    try:
        response = client.chat.completions.create(
            model=model or settings.LLM.model,
            messages=messages,
            stream=True
        )

        full_content = ""
        thinking = False
        for chunk in response:
            if hasattr(chunk.choices[0].delta, 'reasoning_content') and chunk.choices[0].delta.reasoning_content:
                if not thinking:
                    yield "data: <think>\n\n"
                    thinking = True
                content = chunk.choices[0].delta.reasoning_content
                yield "data: {}\n\n".format(content.replace('\n', '\\n'))
            elif chunk.choices[0].delta.content:
                if thinking:
                    yield "data: </think>\n\n"
                    thinking = False
                content = chunk.choices[0].delta.content
                full_content += content
                yield "data: {}\n\n".format(content.replace('\n', '\\n'))
            elif chunk.usage:
                yield "event: usage_stats\ndata: {}\n\n".format(json.dumps(chunk.usage.to_dict()))
        yield "event: end\ndata: {\"status\": \"done\"}\n\n"

    except Exception as e:
        yield f"data: Error: {str(e)}\n\n"
        yield "event: end\ndata: {\"status\": \"exception\"}\n\n"
