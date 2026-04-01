"""CLI entry point for Engram.

Usage:
    engram serve                    # stdio mode (default, for MCP clients)
    engram serve --http             # Streamable HTTP on localhost:7474
    engram serve --host 0.0.0.0    # team mode
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

import click

from engram.storage import DEFAULT_DB_PATH


@click.group()
def main() -> None:
    """Engram — Multi-agent memory consistency for engineering teams."""
    pass


@main.command()
@click.option("--http", is_flag=True, help="Use Streamable HTTP transport instead of stdio.")
@click.option("--host", default="127.0.0.1", help="Host to bind (HTTP mode).")
@click.option("--port", default=7474, type=int, help="Port to bind (HTTP mode).")
@click.option("--db", default=str(DEFAULT_DB_PATH), help="Path to SQLite database.")
@click.option("--log-level", default="INFO", help="Logging level.")
def serve(http: bool, host: str, port: int, db: str, log_level: str) -> None:
    """Start the Engram MCP server."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        stream=sys.stderr,
    )
    logger = logging.getLogger("engram")

    asyncio.run(_serve(http=http, host=host, port=port, db_path=db, logger=logger))


async def _serve(
    http: bool, host: str, port: int, db_path: str, logger: logging.Logger
) -> None:
    from engram.engine import EngramEngine
    from engram.server import mcp
    import engram.server as server_module
    from engram.storage import Storage

    # Initialize storage
    storage = Storage(db_path=db_path)
    await storage.connect()
    logger.info("Database: %s", db_path)

    # Initialize engine
    engine = EngramEngine(storage)
    server_module._engine = engine

    # Start detection worker
    await engine.start()
    logger.info("Detection worker started")

    # Run TTL expiry check
    expired = await storage.expire_ttl_facts()
    if expired:
        logger.info("Expired %d TTL facts on startup", expired)

    try:
        if http:
            logger.info("Starting Streamable HTTP server on %s:%d", host, port)
            await mcp.run_streamable_http_async(host=host, port=port)
        else:
            logger.info("Starting stdio server")
            await mcp.run_stdio_async()
    finally:
        await engine.stop()
        await storage.close()


if __name__ == "__main__":
    main()
