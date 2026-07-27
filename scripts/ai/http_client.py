# Copyright 2026

"""HTTP transport factory for source fetching."""

from __future__ import annotations

import socket

import httpx2

_DEFAULT_SOCKET_OPTIONS = [(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)]
_DEFAULT_TIMEOUT = httpx2.Timeout(connect=5.0, read=30.0, write=10.0, pool=10.0)
_DEFAULT_LIMITS = httpx2.Limits(
    max_connections=200,
    max_keepalive_connections=40,
    keepalive_expiry=30.0,
)


def _raise_for_non_success(response: httpx2.Response) -> None:
    if response.is_error:
        _ = response.read()
        _ = response.raise_for_status()


def create_http_client(
    transport: httpx2.BaseTransport | None = None,
) -> httpx2.Client:
    """Create the configured HTTP client used by Task 2 fetch paths."""
    if transport is None:
        transport = httpx2.HTTPTransport(
            http2=True,
            retries=3,
            socket_options=_DEFAULT_SOCKET_OPTIONS,
            limits=_DEFAULT_LIMITS,
        )

    return httpx2.Client(
        transport=transport,
        limits=_DEFAULT_LIMITS,
        timeout=_DEFAULT_TIMEOUT,
        follow_redirects=True,
        event_hooks={"response": [_raise_for_non_success]},
    )
