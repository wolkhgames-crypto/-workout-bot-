import os
import sys
import json
import logging

from aiohttp import web

# Add project dir to path
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from storage import get_user_stats, get_user_data

logger = logging.getLogger(__name__)

# For Bothost: will be https://botXXXX.bothost.tech
# For local dev: http://localhost:8080
# Override via env var WEB_APP_URL
WEB_APP_URL = os.getenv("WEB_APP_URL", "http://localhost:8080")


async def handle_index(request):
    """Serve Mini App frontend."""
    static_path = os.path.join(PROJECT_DIR, "static", "index.html")
    if not os.path.exists(static_path):
        return web.Response(text="Mini App not found", status=404)
    with open(static_path, "r", encoding="utf-8") as f:
        content = f.read()
    return web.Response(text=content, content_type="text/html", charset="utf-8")


async def handle_stats(request):
    """API: Get user stats for Mini App."""
    user_id = request.query.get("user_id")
    if not user_id:
        return web.json_response({"error": "user_id required"}, status=400)
    try:
        uid = int(user_id)
    except ValueError:
        return web.json_response({"error": "invalid user_id"}, status=400)
    
    stats = get_user_stats(uid)
    return web.json_response(stats)


async def handle_complete(request):
    """API: Record workout completion from Mini App."""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "invalid JSON"}, status=400)
    
    user_id = body.get("user_id")
    day_number = body.get("day_number")
    if not user_id or not day_number:
        return web.json_response({"error": "user_id and day_number required"}, status=400)
    
    from storage import record_completion, advance_user_day
    record_completion(int(user_id), int(day_number))
    advance_user_day(int(user_id))
    
    return web.json_response({"status": "ok"})


async def handle_health(request):
    return web.json_response({"status": "ok"})


def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/", handle_index)
    app.router.add_get("/api/stats", handle_stats)
    app.router.add_post("/api/complete", handle_complete)
    app.router.add_get("/health", handle_health)
    return app

