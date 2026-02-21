"""
vjlive3.api
===========
FastAPI REST + WebSocket server for VJLive3.

Sub-modules (added as Phase 7 tasks complete):
    routes     — REST endpoints (plugin control, node graph, presets)
    ws         — WebSocket handlers (real-time node graph updates at 60fps)
    models     — Pydantic v2 request/response models
    auth       — RBAC + rate limiting (SAFETY_RAILS.md Rail 10)

Framework rules:
    FastAPI ONLY — no Flask imports anywhere in this package.
    All route handlers must be async.
    All request/response bodies validated by Pydantic v2 models.
    Use httpx.AsyncClient for inter-service HTTP calls (not requests).
    Rate limiting: 100 req/min authenticated, 10 req/min unauthenticated.

Reference: VJlive-2/core/api/, admin_api.py, websocket_brush_handler.py
"""
