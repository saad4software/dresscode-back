import inspect
import logging
from typing import Any, Awaitable, Callable, Optional

from src.ai.client import _get_client
from src.core.config import config

logger = logging.getLogger(__name__)

ToolFn = Callable[..., Awaitable[Any] | Any]


async def run_with_tools(
    *,
    contents: list,
    tools: list[dict],
    available_tools: dict[str, ToolFn],
    final_response_schema: Optional[type] = None,
    max_turns: int = 4,
    model: Optional[str] = None,
) -> tuple[str, list]:
    """Run a multi-turn Gemma function-calling loop.

    The model may request tool calls; we execute them and feed results back.
    When the model stops requesting tools, we issue one final turn using
    `final_response_schema` (if provided) to coerce a structured JSON answer.

    Returns the final response text and the full content history.
    """
    client = _get_client()
    from google.genai import types

    model_id = model or config.gemma_model_id
    tool_block = types.Tool(function_declarations=tools)
    tool_config = types.GenerateContentConfig(tools=[tool_block])

    history: list = list(contents)

    for turn in range(max_turns):
        response = await client.aio.models.generate_content(
            model=model_id,
            contents=history,
            config=tool_config,
        )

        function_calls = getattr(response, "function_calls", None)
        if not function_calls:
            if final_response_schema is None:
                return response.text or "", history
            break

        # Record the model's tool-call message so it can be referenced
        # alongside our function response in the next turn.
        if response.candidates and response.candidates[0].content:
            history.append(response.candidates[0].content)

        for fc in function_calls:
            tool = available_tools.get(fc.name)
            if tool is None:
                tool_output: Any = {"error": f"Unknown tool: {fc.name}"}
            else:
                args = dict(fc.args or {})
                try:
                    result = tool(**args)
                    if inspect.isawaitable(result):
                        result = await result
                    tool_output = result
                except Exception as exc:
                    logger.exception("Tool %s failed", fc.name)
                    tool_output = {"error": f"Tool execution failed: {exc}"}

            history.append(
                types.Part.from_function_response(
                    name=fc.name,
                    response={"result": tool_output},
                )
            )

    final_config = types.GenerateContentConfig(
        tools=[tool_block],
        response_mime_type="application/json",
        response_schema=final_response_schema,
    )
    final = await client.aio.models.generate_content(
        model=model_id,
        contents=history,
        config=final_config,
    )
    return final.text or "", history
