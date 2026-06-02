import asyncio
import logging
import os
import sys

from aiohttp import web

# Ensure project dir is in path
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_bot_app():
    """Create and return the bot dispatcher (lazy import for speed)."""
    from bot import dp, bot, main as bot_main
    return dp, bot


def create_web_app():
    """Create and return the aiohttp web app."""
    from server import create_app
    return create_app()


async def run_bot():
    """Run bot polling."""
    from bot import dp, bot
    logger.info("Starting bot polling...")
    await dp.start_polling(bot)


async def run_server():
    """Run aiohttp web server."""
    app = create_web_app()
    port = int(os.getenv("PORT", "8080"))
    host = os.getenv("HOST", "0.0.0.0")
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    logger.info(f"Web server running on {host}:{port}")
    
    # Keep running
    await asyncio.Event().wait()


async def _detect_public_url() -> str | None:
    """Try to detect ngrok public HTTPS URL from local ngrok API."""
    try:
        from aiohttp import ClientSession
        async with ClientSession() as session:
            async with session.get(
                "http://127.0.0.1:4040/api/tunnels", timeout=2
            ) as resp:
                data = await resp.json()
                for tunnel in data.get("tunnels", []):
                    url = tunnel.get("public_url", "")
                    if url.startswith("https://"):
                        return url
    except Exception:
        pass
    return None


async def main():
    # Auto-detect ngrok public URL for Telegram WebApp button (requires HTTPS)
    ngrok_url = await _detect_public_url()
    if ngrok_url:
        os.environ["WEB_APP_URL"] = ngrok_url
        logger.info(f"Using ngrok public URL: {ngrok_url}")
    else:
        logger.info(f"Using WEB_APP_URL: {os.getenv('WEB_APP_URL', 'http://localhost:8080')}")

    logger.info("Starting Workout Bot + Web Server...")
    await asyncio.gather(run_bot(), run_server())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down...")
