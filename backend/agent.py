"""The Campus Customs shop agent, built with PydanticAI.

Wraps the data-access functions in tools.py as agent tools, loads the system
prompt from prompts/prompt.md, and talks to Anthropic's Claude (through Portkey
when PORTKEY_API_KEY is set, else directly with ANTHROPIC_API_KEY; a backend/.env
file is loaded automatically if present).

Each turn runs step by step so every model step and tool call is written to the
audit trail (see audit.py), with per-turn usage limits and an output guard.
"""
from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_ai import Agent, RunContext
from pydantic_ai.exceptions import UsageLimitExceeded
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    RetryPromptPart,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)
from pydantic_ai.usage import UsageLimits

import audit
import tools
from models import (
    AgentDeps,
    CategoryCount,
    ChatProduct,
    ChatTurn,
    ProductDetail,
    ProductSummary,
    StockReport,
)

BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(BACKEND_DIR / ".env")

# Overridable so you can swap models without touching code.
MODEL_NAME = os.environ.get("CHATBOT_MODEL", "claude-haiku-4-5")

# Portkey gateway (an AI gateway that fronts Anthropic). If PORTKEY_API_KEY is
# set we route through it; otherwise we call Anthropic directly with ANTHROPIC_API_KEY.
PORTKEY_API_KEY = os.environ.get("PORTKEY_API_KEY")
PORTKEY_BASE_URL = os.environ.get("PORTKEY_BASE_URL", "https://api.portkey.ai")
PORTKEY_PROVIDER = os.environ.get("PORTKEY_PROVIDER", "anthropic")
PORTKEY_VIRTUAL_KEY = os.environ.get("PORTKEY_VIRTUAL_KEY")
PORTKEY_CONFIG = os.environ.get("PORTKEY_CONFIG")


def _portkey_base_url() -> str:
    """The Anthropic SDK appends '/v1/messages', so the base must NOT end in /v1.

    Normalizes whatever the course provided (e.g. https://api.portkey.ai/v1) down
    to the host root so the final URL is exactly <host>/v1/messages.
    """
    url = PORTKEY_BASE_URL.rstrip("/")
    if url.endswith("/v1"):
        url = url[: -len("/v1")]
    return url


def _portkey_headers() -> dict[str, str]:
    headers = {"x-portkey-api-key": PORTKEY_API_KEY or ""}
    if PORTKEY_PROVIDER:
        headers["x-portkey-provider"] = PORTKEY_PROVIDER
    if PORTKEY_VIRTUAL_KEY:
        headers["x-portkey-virtual-key"] = PORTKEY_VIRTUAL_KEY
    if PORTKEY_CONFIG:
        headers["x-portkey-config"] = PORTKEY_CONFIG
    return headers


class AgentNotConfigured(RuntimeError):
    """Raised when no Anthropic API key is available."""


def _system_prompt() -> str:
    return (BACKEND_DIR / "prompts" / "prompt.md").read_text(encoding="utf-8")


def _remember(deps: AgentDeps, cards: list[ChatProduct]) -> None:
    """Record products surfaced during the run, de-duplicated, for the UI cards."""
    seen = {p.product_id for p in deps.shown}
    for card in cards:
        if card.product_id not in seen:
            deps.shown.append(card)
            seen.add(card.product_id)


def make_agent(model: object) -> Agent[AgentDeps, str]:
    """Build the agent graph (prompt + tools) bound to the given model.

    Kept separate from `build_agent` so tests can pass a TestModel without a key.
    """
    agent: Agent[AgentDeps, str] = Agent(
        model,
        deps_type=AgentDeps,
        system_prompt=_system_prompt(),
        retries=2,
    )

    @agent.instructions
    def _context(ctx: RunContext[AgentDeps]) -> str:
        lines: list[str] = []
        customer = ctx.deps.customer
        if customer:
            lines.append(
                f"You are chatting with {customer.name} (email: {customer.email}). "
                "Greet them warmly by first name and remember your earlier conversation."
            )
        else:
            lines.append("The shopper is browsing as a guest (no account; no saved history).")

        page = ctx.deps.page_context
        if page and page.product_id:
            lines.append(
                f"The shopper is currently viewing the product page for product_id "
                f"'{page.product_id}'. If they say 'this', 'it', 'this one', or ask about "
                "another color/size without naming a product, they mean that product — "
                "look it up with get_product_details or check_stock."
            )
        elif page and page.path:
            lines.append(f"The shopper is on the '{page.path}' page.")
        return "\n".join(lines)

    @agent.tool
    def search_products(
        ctx: RunContext[AgentDeps],
        query: str = "",
        category: str | None = None,
        color: str | None = None,
        max_price: float | None = None,
    ) -> list[ProductSummary]:
        """Search the catalogue, with optional filters. Results list in-stock items first.

        Args:
            query: Space-separated keywords matched against name, description, and tags.
            category: Optional exact category (e.g. "hoodie", "fleece jacket").
            color: Optional color to match (e.g. "gray", "navy blue").
            max_price: Optional maximum price in dollars (e.g. 60 for "under $60").
        """
        results = tools.search_products(
            ctx.deps.db_path, query=query, category=category, color=color, max_price=max_price
        )
        _remember(ctx.deps, [ChatProduct.from_summary(p) for p in results])
        return results

    @agent.tool
    def get_product_details(ctx: RunContext[AgentDeps], product_id: str) -> ProductDetail | None:
        """Get full details (description, colors, price) and per-size stock for one product."""
        detail = tools.get_product(ctx.deps.db_path, product_id)
        if detail is not None:
            _remember(ctx.deps, [ChatProduct.from_summary(detail)])
        return detail

    @agent.tool
    def check_stock(
        ctx: RunContext[AgentDeps], product_id: str, size: str | None = None
    ) -> StockReport | None:
        """Check live stock for a product, broken down by size.

        Use this for availability questions ("is it in stock?", "how many mediums?").
        Pass `size` (XS, S, M, L, XL, XXL) to focus on one size; omit it for the full
        breakdown. Returns real quantities from the database — never estimate stock.
        """
        report = tools.check_stock(ctx.deps.db_path, product_id, size=size)
        if report is not None:
            _remember(
                ctx.deps,
                [ChatProduct(
                    product_id=report.product_id,
                    name=report.name,
                    price=report.price,
                    image_url=report.image_url,
                )],
            )
        return report

    @agent.tool
    def list_categories(ctx: RunContext[AgentDeps]) -> list[CategoryCount]:
        """List the product categories and how many items each contains."""
        return tools.list_categories(ctx.deps.db_path)

    return agent


def _build_model() -> object:
    """Build the Claude model, via Portkey if configured, else direct Anthropic."""
    # Imported here so the module still imports without the anthropic provider deps.
    from anthropic import AsyncAnthropic
    from pydantic_ai.models.anthropic import AnthropicModel
    from pydantic_ai.providers.anthropic import AnthropicProvider

    if PORTKEY_API_KEY:
        # Route through the Portkey gateway. The Portkey key authenticates via the
        # x-portkey-* headers; the Anthropic SDK's own api_key is unused by Portkey.
        client = AsyncAnthropic(
            api_key=PORTKEY_API_KEY,
            base_url=_portkey_base_url(),
            default_headers=_portkey_headers(),
        )
        return AnthropicModel(MODEL_NAME, provider=AnthropicProvider(anthropic_client=client))

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if anthropic_key:
        return AnthropicModel(MODEL_NAME, provider=AnthropicProvider(api_key=anthropic_key))

    raise AgentNotConfigured(
        "No API key configured. Set PORTKEY_API_KEY (recommended) or ANTHROPIC_API_KEY "
        "in backend/.env or the environment."
    )


@lru_cache(maxsize=1)
def build_agent() -> Agent[AgentDeps, str]:
    """The production agent, bound to Claude (through Portkey when configured)."""
    return make_agent(_build_model())


def _to_message_history(history: list[ChatTurn]) -> list[ModelMessage]:
    messages: list[ModelMessage] = []
    for turn in history:
        if turn.role == "user":
            messages.append(ModelRequest(parts=[UserPromptPart(content=turn.content)]))
        else:
            messages.append(ModelResponse(parts=[TextPart(content=turn.content)]))
    return messages


# Safety limits for one chat turn. A normal answer needs 1-3 model requests and a
# few tool calls; anything past this is a runaway loop, so stop and reply politely.
USAGE_LIMITS = UsageLimits(request_limit=6, tool_calls_limit=8)
LOOP_LIMIT_REPLY = (
    "Sorry, I got a bit tangled up looking that up! Could you ask again, maybe a little "
    "more specifically? You can also browse everything on the Products page."
)

# Output guard: never let anything that looks like a password hash or API key out.
_SECRET = re.compile(
    r"(pbkdf2_sha256\$\S+|\$2[aby]\$\d\d\$[./A-Za-z0-9]{20,}|\b(?:sk-ant-|pk-)[\w-]{8,})"
)


def _guard(reply: str) -> tuple[str, bool]:
    cleaned = _SECRET.sub("[removed]", reply)
    return cleaned, cleaned != reply


def _stop_reason(response: ModelResponse) -> str | None:
    """The provider's own stop reason (e.g. "end_turn", "tool_use"), else PydanticAI's."""
    details = response.provider_details or {}
    return details.get("finish_reason") or details.get("stop_reason") or response.finish_reason


async def run_agent(
    message: str,
    history: list[ChatTurn],
    deps: AgentDeps,
    agent: Agent[AgentDeps, str] | None = None,
) -> str:
    """Run one turn and return the assistant's reply text.

    Products surfaced during the run are collected on `deps.shown`. `agent` can be
    supplied in tests (e.g. with a TestModel); production uses the cached Claude agent.
    Every step is recorded in the audit trail as it happens.
    """
    run_id = audit.new_run_id()
    page = deps.page_context
    audit.record(
        run_id,
        "run_start",
        shopper=f"user:{deps.customer.user_id}" if deps.customer else "guest",
        page=(page.product_id or page.path) if page else None,
        message=audit.short(message, 100),
        history_turns=len(history),
    )

    calls: dict[str, ToolCallPart] = {}
    steps = tool_calls = 0
    last_stop: str | None = None

    def end(stop_reason: str | None, **fields: object) -> None:
        audit.record(
            run_id,
            "run_end",
            stop_reason=stop_reason,
            model_steps=steps,
            tool_calls=tool_calls,
            products_shown=len(deps.shown),
            **fields,
        )

    try:
        agent = agent or build_agent()
        async with agent.iter(
            message,
            message_history=_to_message_history(history),
            deps=deps,
            usage_limits=USAGE_LIMITS,
        ) as run:
            async for node in run:
                if Agent.is_call_tools_node(node):
                    # The model just answered: log its stop reason and any tools it asked for.
                    response = node.model_response
                    steps += 1
                    last_stop = _stop_reason(response)
                    requested = [p for p in response.parts if isinstance(p, ToolCallPart)]
                    calls.update({p.tool_call_id: p for p in requested})
                    audit.record(
                        run_id,
                        "model_step",
                        step=steps,
                        stop_reason=last_stop,
                        tools_requested=[p.tool_name for p in requested] or None,
                    )
                elif Agent.is_model_request_node(node):
                    # Tool results are sent back to the model here, paired with their calls.
                    for part in node.request.parts:
                        if isinstance(part, (ToolReturnPart, RetryPromptPart)) and part.tool_name:
                            call = calls.pop(part.tool_call_id, None)
                            tool_calls += 1
                            result = (
                                audit.summarize(part.content)
                                if isinstance(part, ToolReturnPart)
                                else audit.short(f"retry: {part.model_response()}")
                            )
                            audit.record(
                                run_id,
                                "tool_call",
                                tool=part.tool_name,
                                args=audit.short(call.args_as_dict()) if call else None,
                                result=result,
                            )
            output = run.result.output if run.result else ""
    except UsageLimitExceeded as exc:
        end("usage_limit", detail=audit.short(str(exc)))
        return LOOP_LIMIT_REPLY
    except Exception as exc:
        end("error", detail=type(exc).__name__)
        raise

    reply, redacted = _guard(output)
    end(last_stop, reply=audit.short(reply, 120), guard="redacted" if redacted else None)
    return reply
