#!/usr/bin/env python3
"""Inject mocked OpenTelemetry (OTLP/HTTP JSON) LLM traces into Netra.

Uses the same credentials as the Netra Python SDK: ``NETRA_API_KEY`` and
``NETRA_OTLP_ENDPOINT`` from the environment (e.g. after loading ``.env``).
The API key selects the Netra project on the server; no separate project id is required.

Example::

    python inject_mock_netra_otlp_traces.py --count 25
    python inject_mock_netra_otlp_traces.py -n 5 --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
import time
import uuid
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

# Curated user / assistant pairs for mock traces (extend as needed).
MOCK_CONVERSATION_TURNS: list[tuple[str, str]] = [
    ("hellohello", "Hello! How can I assist you today?"),
    ("Summarize what OpenTelemetry does in two sentences.", "OpenTelemetry provides a unified API and SDK for observability signals like traces, metrics, and logs. It lets you instrument once and export to many backends through a common pipeline."),
    ("What is the capital of France?", "The capital of France is Paris."),
    ("Write a haiku about debugging.", "Stack trace unwinds—\nA null where truth should have been.\nBreakpoint, then dawn."),
    ("Translate to Spanish: Good morning.", "Buenos días."),
    ("Give me three bullet tips for faster Python tests.", "- Use pytest-xdist for parallel runs.\n- Prefer fixtures over ad-hoc setup in each test.\n- Mock I/O at boundaries, not deep internals unless necessary."),
    ("Explain JSON vs protobuf for OTLP.", "JSON OTLP encodes the same protobuf schema as human-readable JSON over HTTP. Protobuf is more compact; JSON is easier to hand-craft and debug."),
    ("What is 17 * 23?", "391"),
    ("Draft a one-line product description for an AI observability dashboard.", "See every LLM call, latency spike, and token cost in one place—from raw traces to business metrics."),
    ("Is this trace synthetic?", "Yes—this message pair is generated for load and UI testing."),
]

SERVICE_NAME_DEFAULT = "cohere-simple-cli"
DEPLOYMENT_ENV = "dev"
MODEL_NAME = "test-model"
COHERE_CHAT_URL = "https://api.cohere.com/v2/chat"
AGENT_NAME = "automation-agent"
NETRA_LIB_VERSION = "0.1.83"
HTTPX_SCOPE_VERSION = "0.28.1"
COHERE_SCOPE_VERSION = "0.40.13"


def _load_env() -> None:
    load_dotenv()
    load_dotenv(Path(__file__).resolve().parent / ".env")


def _auth_headers(endpoint: str, api_key: str) -> dict[str, str]:
    """Match ``netra.config.Config._setup_authentication``."""
    if "getnetra" in endpoint.lower():
        return {"x-api-key": api_key}
    return {"Authorization": f"Bearer {api_key}"}


def _traces_url(endpoint: str) -> str:
    base = endpoint.rstrip("/")
    if base.endswith("/v1/traces"):
        return base
    return f"{base}/v1/traces"


def _estimate_tokens(text: str) -> int:
    """Rough stand-in for tokenizer output (stable, deterministic enough for mocks)."""
    return max(1, (len(text) + 3) // 4)


def _build_spans_for_trace(
    *,
    user_content: str,
    assistant_content: str,
    trace_id: str,
    root_span_id: str,
    llm_span_id: str,
    http_span_id: str,
    base_ns: int,
    session_id: str,
    user_id: str,
    tenant_id: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    prompt_tokens = _estimate_tokens(user_content)
    completion_tokens = _estimate_tokens(assistant_content)
    total_tokens = prompt_tokens + completion_tokens

    # Nested durations: HTTP finishes first, then LLM, then workflow root.
    t0 = base_ns
    t_http_end = t0 + 50_000_000  # 50ms
    t_llm_end = t0 + 120_000_000
    t_root_end = t0 + 150_000_000

    common_netra_attrs: list[dict[str, Any]] = [
        {"key": "library.name", "value": {"stringValue": "netra"}},
        {"key": "library.version", "value": {"stringValue": NETRA_LIB_VERSION}},
        {"key": "sdk.name", "value": {"stringValue": "netra"}},
        {"key": "sdk.version", "value": {"stringValue": NETRA_LIB_VERSION}},
        {"key": "netra.session_id", "value": {"stringValue": session_id}},
        {"key": "netra.user_id", "value": {"stringValue": user_id}},
        {"key": "netra.tenant_id", "value": {"stringValue": tenant_id}},
        {"key": "netra.agent.name", "value": {"stringValue": AGENT_NAME}},
    ]

    llm_agg = json.dumps(
        {"has_error": "false", "has_pii": "false", "has_violation": "false"},
        separators=(",", ":"),
    )
    workflow_agg = json.dumps(
        {
            "has_error": "false",
            "tokens": {
                MODEL_NAME: {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                }
            },
            "models": [MODEL_NAME],
            "has_pii": "false",
            "has_violation": "false",
        },
        separators=(",", ":"),
    )

    http_span = {
        "traceId": trace_id,
        "spanId": http_span_id,
        "parentSpanId": llm_span_id,
        "name": "Outbound LLM API Request",
        "kind": "SPAN_KIND_CLIENT",
        "startTimeUnixNano": str(t0),
        "endTimeUnixNano": str(t_http_end),
        "attributes": [
            {"key": "http.method", "value": {"stringValue": "POST"}},
            {"key": "http.url", "value": {"stringValue": COHERE_CHAT_URL}},
            *common_netra_attrs,
            {"key": "http.status_code", "value": {"intValue": 200}},
        ],
        "events": [],
        "links": [],
    }

    llm_span = {
        "traceId": trace_id,
        "spanId": llm_span_id,
        "parentSpanId": root_span_id,
        "name": "LLM Chat Completion",
        "kind": "SPAN_KIND_CLIENT",
        "startTimeUnixNano": str(t0),
        "endTimeUnixNano": str(t_llm_end),
        "attributes": [
            {"key": "gen_ai.system", "value": {"stringValue": "Cohere"}},
            {"key": "llm.request.type", "value": {"stringValue": "chat"}},
            *common_netra_attrs,
            {"key": "gen_ai.request.model", "value": {"stringValue": MODEL_NAME}},
            {"key": "gen_ai.prompt.0.role", "value": {"stringValue": "user"}},
            {"key": "gen_ai.prompt.0.content", "value": {"stringValue": user_content}},
            {"key": "netra.aggregated_attributes", "value": {"stringValue": llm_agg}},
            {"key": "gen_ai.response.id", "value": {"stringValue": str(uuid.uuid4())}},
            {"key": "gen_ai.completion.0.role", "value": {"stringValue": "assistant"}},
            {"key": "gen_ai.completion.0.content", "value": {"stringValue": assistant_content}},
            {"key": "gen_ai.usage.prompt_tokens", "value": {"intValue": prompt_tokens}},
            {"key": "gen_ai.usage.completion_tokens", "value": {"intValue": completion_tokens}},
            {"key": "llm.usage.total_tokens", "value": {"intValue": total_tokens}},
        ],
        "events": [],
        "links": [],
    }

    root_span = {
        "traceId": trace_id,
        "spanId": root_span_id,
        "parentSpanId": "",
        "name": "AI Workflow Execution",
        "kind": "SPAN_KIND_INTERNAL",
        "startTimeUnixNano": str(t0),
        "endTimeUnixNano": str(t_root_end),
        "attributes": [
            *common_netra_attrs,
            {"key": "netra.entity.type", "value": {"stringValue": "workflow"}},
            {"key": "netra.aggregated_attributes", "value": {"stringValue": workflow_agg}},
        ],
        "events": [],
        "links": [],
    }

    return http_span, llm_span, root_span


def build_export_request(
    n: int,
    *,
    inject_unix_nano: int,
    service_name: str,
    deployment_environment: str,
    session_prefix: str,
    stagger_ns: int,
) -> dict[str, Any]:
    """Single OTLP ``ExportTraceServiceRequest`` JSON object with ``n`` traces.

    ``inject_unix_nano`` should be ``time.time_ns()`` at the moment you inject
    (typically immediately before serializing / POSTing) so span times match wall clock.
    """
    http_spans: list[dict[str, Any]] = []
    llm_spans: list[dict[str, Any]] = []
    root_spans: list[dict[str, Any]] = []

    for i in range(n):
        user, assistant = MOCK_CONVERSATION_TURNS[i % len(MOCK_CONVERSATION_TURNS)]
        trace_id = secrets.token_hex(16)
        root_id = secrets.token_hex(8)
        llm_id = secrets.token_hex(8)
        http_id = secrets.token_hex(8)
        base_ns = inject_unix_nano + i * stagger_ns
        session_id = f"{session_prefix}-{i:04d}"
        user_id = f"{session_prefix}-user-{i:04d}"
        tenant_id = f"{session_prefix}-tenant-{i:04d}"

        h, l, r = _build_spans_for_trace(
            user_content=user,
            assistant_content=assistant,
            trace_id=trace_id,
            root_span_id=root_id,
            llm_span_id=llm_id,
            http_span_id=http_id,
            base_ns=base_ns,
            session_id=session_id,
            user_id=user_id,
            tenant_id=tenant_id,
        )
        http_spans.append(h)
        llm_spans.append(l)
        root_spans.append(r)

    resource = {
        "attributes": [
            {"key": "service.name", "value": {"stringValue": service_name}},
            {"key": "deployment.environment", "value": {"stringValue": deployment_environment}},
        ]
    }

    scope_spans = [
        {
            "scope": {"name": "netra.instrumentation.httpx", "version": HTTPX_SCOPE_VERSION},
            "spans": http_spans,
        },
        {
            "scope": {"name": "netra.instrumentation.cohere", "version": COHERE_SCOPE_VERSION},
            "spans": llm_spans,
        },
        {"scope": {"name": "__main__"}, "spans": root_spans},
    ]

    return {"resourceSpans": [{"resource": resource, "scopeSpans": scope_spans}]}


def main() -> int:
    _load_env()

    parser = argparse.ArgumentParser(
        description="POST mocked OTLP/JSON LLM traces to Netra (project implied by API key)."
    )
    parser.add_argument(
        "-n",
        "--count",
        type=int,
        default=10,
        help="Number of synthetic traces to generate (default: 10).",
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("NETRA_API_KEY"),
        help="Netra API key (default: NETRA_API_KEY from env).",
    )
    parser.add_argument(
        "--endpoint",
        default=os.getenv("NETRA_OTLP_ENDPOINT") or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"),
        help="Base OTLP URL, e.g. https://api.demo.getnetra.ai/telemetry (default: env).",
    )
    parser.add_argument(
        "--service-name",
        default=os.getenv("NETRA_APP_NAME") or os.getenv("OTEL_SERVICE_NAME") or SERVICE_NAME_DEFAULT,
        help="service.name resource attribute.",
    )
    parser.add_argument(
        "--environment",
        default=os.getenv("NETRA_ENV", DEPLOYMENT_ENV),
        help="deployment.environment resource attribute (default: NETRA_ENV or dev).",
    )
    parser.add_argument(
        "--session-prefix",
        default=os.getenv("MOCK_TRACE_SESSION_PREFIX", "mock-otlp-inject"),
        help="Prefix for synthetic session/user/tenant ids.",
    )
    parser.add_argument(
        "--stagger-ms",
        type=float,
        default=0.0,
        help=(
            "Extra offset per trace index in milliseconds, added to injection time "
            "(default: 0 — all traces use the same time.now snapshot)."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print JSON payload stats only; do not POST.",
    )
    args = parser.parse_args()

    if args.count < 1:
        print("error: --count must be >= 1", file=sys.stderr)
        return 2

    if not args.api_key:
        print("error: missing API key; set NETRA_API_KEY or pass --api-key", file=sys.stderr)
        return 2

    if not args.endpoint:
        print(
            "error: missing OTLP base URL; set NETRA_OTLP_ENDPOINT or pass --endpoint",
            file=sys.stderr,
        )
        return 2

    stagger_ns = int(args.stagger_ms * 1_000_000)
    inject_unix_nano = time.time_ns()
    body = build_export_request(
        args.count,
        inject_unix_nano=inject_unix_nano,
        service_name=args.service_name,
        deployment_environment=args.environment,
        session_prefix=args.session_prefix,
        stagger_ns=stagger_ns,
    )

    serialized = json.dumps(body, separators=(",", ":")).encode("utf-8")
    url = _traces_url(args.endpoint)
    headers = {
        "Content-Type": "application/json",
        **_auth_headers(args.endpoint, args.api_key),
    }

    if args.dry_run:
        print(f"dry-run: would POST {len(serialized)} bytes to {url}")
        print(f"        traces={args.count}, service.name={args.service_name!r}")
        return 0

    with httpx.Client(timeout=60.0) as client:
        resp = client.post(url, content=serialized, headers=headers)

    if resp.is_success:
        print(f"ok: injected {args.count} trace(s) via {url} (HTTP {resp.status_code})")
        return 0

    print(f"error: HTTP {resp.status_code} from {url}", file=sys.stderr)
    print(resp.text[:2000], file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
