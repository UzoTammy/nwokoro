import json

from anthropic import Anthropic
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from advisor.context import SYSTEM_PROMPT, build_financial_context
from advisor.schemas import ChatRequest
from advisor.tools import EXTRACT_TOOL, SEARCH_TOOL, tavily_extract, tavily_search

router = APIRouter(tags=["AI"])

_client = Anthropic()
_MODEL = "claude-sonnet-4-6"
_MAX_TOKENS = 2048
_TOOLS = [SEARCH_TOOL, EXTRACT_TOOL]


@router.post("/chat")
def chat(body: ChatRequest):
    """Stream an AI advisor response, using web search when current data is needed."""
    context = build_financial_context()
    system = f"{SYSTEM_PROMPT}\n\n{context}"
    messages = body.history + [{"role": "user", "content": body.question}]

    def generate():
        current_messages = list(messages)
        tools_used = False

        response = _client.messages.create(
            model=_MODEL,
            max_tokens=_MAX_TOKENS,
            system=system,
            messages=current_messages,
            tools=_TOOLS,
        )

        while response.stop_reason == "tool_use":
            tools_used = True
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                if block.name == "web_search":
                    query = block.input.get("query", "")
                    yield f"data: {json.dumps(chr(10) + '🔍 *Searching: ' + query + '…*' + chr(10) + chr(10))}\n\n"
                    tool_results.append({
                        "type":        "tool_result",
                        "tool_use_id": block.id,
                        "content":     tavily_search(query),
                    })
                elif block.name == "read_url":
                    url = block.input.get("url", "")
                    yield f"data: {json.dumps(chr(10) + '📄 *Reading: ' + url + '…*' + chr(10) + chr(10))}\n\n"
                    tool_results.append({
                        "type":        "tool_result",
                        "tool_use_id": block.id,
                        "content":     tavily_extract(url),
                    })

            current_messages = current_messages + [
                {"role": "assistant", "content": response.content},
                {"role": "user",      "content": tool_results},
            ]
            response = _client.messages.create(
                model=_MODEL,
                max_tokens=_MAX_TOKENS,
                system=system,
                messages=current_messages,
                tools=_TOOLS,
            )

        if tools_used:
            with _client.messages.stream(
                model=_MODEL,
                max_tokens=_MAX_TOKENS,
                system=system,
                messages=current_messages,
            ) as stream:
                for text in stream.text_stream:
                    yield f"data: {json.dumps(text)}\n\n"
        else:
            for block in response.content:
                if hasattr(block, "text") and block.text:
                    text = block.text
                    for i in range(0, len(text), 80):
                        yield f"data: {json.dumps(text[i:i + 80])}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
