# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
FastAPI application for the Hoja Traffic Signal Control Environment.

This module creates an HTTP server that exposes the HojaEnvironment
over HTTP and WebSocket endpoints, compatible with EnvClient.

Endpoints:
    - POST /reset: Reset the environment
    - POST /step: Execute a traffic signal change action
    - GET /state: Get current environment state
    - GET /schema: Get action/observation schemas
    - WS /ws: WebSocket endpoint for persistent sessions

Usage:
    # Development (with auto-reload):
    uvicorn server.app:app --reload --host 0.0.0.0 --port 8000

    # Production:
    uvicorn server.app:app --host 0.0.0.0 --port 8000 --workers 4

    # Or run directly:
    python -m server.app
"""

try:
    from openenv.core.env_server.http_server import create_app
except Exception as e:  # pragma: no cover
    raise ImportError(
        "openenv is required for the web interface. Install dependencies with '\n    uv sync\n'"
    ) from e

try:
    from hoja.app.models import HojaAction, HojaObservation
    from hoja.app.environment import HojaEnvironment
except ImportError:
    try:
        from ..app.models import HojaAction, HojaObservation
        from ..app.environment import HojaEnvironment
    except ImportError:
        from app.models import HojaAction, HojaObservation
        from app.environment import HojaEnvironment


# Create the app with web interface and README integration
app = create_app(
    HojaEnvironment,
    HojaAction,
    HojaObservation,
    env_name="hoja",
    max_concurrent_envs=1,  # increase this number to allow more concurrent WebSocket sessions
)

@app.get("/dashboard")
async def dashboard():
    """Simple dashboard endpoint returning metrics format suitable for frontend visualization."""
    return {
        "status": "online",
        "description": "Hoja Traffic Control Dashboard API endpoint.",
        "metrics_visualization": "Add canvas traffic viz here"
    }

def main(host: str = "0.0.0.0", port: int = 8000):
    """
    Entry point for direct execution via uv run or python -m.

    This function enables running the server without Docker:
        uv run --project . server
        uv run --project . server --port 8001
        python -m hoja.server.app

    Args:
        host: Host address to bind to (default: "0.0.0.0")
        port: Port number to listen on (default: 8000)

    For production deployments, consider using uvicorn directly with
    multiple workers:
        uvicorn hoja.server.app:app --workers 4
    """
    import uvicorn

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
