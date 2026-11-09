# SPEC-004
"""Bound raw upload storage before the multipart decoder allocates/spools content."""

import asyncio
from tempfile import SpooledTemporaryFile

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class UploadAdmission:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["path"] != "/api/v1/ingest/upload":
            await self.app(scope, receive, send)
            return
        limit = (
            256 * 1024 * 1024 + 65536
        )  # bounded multipart overhead; file has its own exact limit
        headers = dict(scope.get("headers", []))
        length = headers.get(b"content-length", b"0")
        if length.isdigit() and int(length) > limit:
            await JSONResponse(
                {
                    "error": {
                        "code": "upload_too_large",
                        "message": "upload too large",
                        "field": None,
                    }
                },
                413,
            )(scope, receive, send)
            return
        with SpooledTemporaryFile(max_size=1024 * 1024) as spool:
            total = 0
            while True:
                message = await receive()
                if message["type"] == "http.disconnect":
                    return
                block = message.get("body", b"")
                total += len(block)
                if total > limit:
                    await JSONResponse(
                        {
                            "error": {
                                "code": "upload_too_large",
                                "message": "upload too large",
                                "field": None,
                            }
                        },
                        413,
                    )(scope, receive, send)
                    return
                await asyncio.to_thread(spool.write, block)
                if not message.get("more_body", False):
                    break
            spool.seek(0)
            done = False

            async def replay() -> Message:
                nonlocal done
                if done:
                    return await receive()
                chunk = await asyncio.to_thread(spool.read, 65536)
                done = spool.tell() >= total
                return {"type": "http.request", "body": chunk, "more_body": not done}

            await self.app(scope, replay, send)
