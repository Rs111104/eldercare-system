from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import logging
from app.core.redis_client import get_redis
import asyncio

router = APIRouter()
logger = logging.getLogger("app.realtime")


class ConnectionManager:
    def __init__(self):
        self.active: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active.append(websocket)

    def disconnect(self, websocket: WebSocket):
        try:
            self.active.remove(websocket)
        except ValueError:
            pass

    async def broadcast(self, message: str):
        for conn in list(self.active):
            try:
                await conn.send_text(message)
            except Exception:
                self.disconnect(conn)


manager = ConnectionManager()


@router.websocket("/ws/tracking")
async def websocket_tracking(ws: WebSocket):
    await manager.connect(ws)
    r = get_redis()
    pubsub_task = None
    try:
        if r:
            # run redis pubsub listener
            async def _listen():
                try:
                    sub = r.pubsub()
                    await sub.subscribe("tracking:channel")
                    async for item in sub.listen():
                        if item and item.get("type") == "message":
                            data = item.get("data")
                            await manager.broadcast(data)
                except Exception:
                    logger.exception("Redis pubsub listener failed")

            pubsub_task = asyncio.create_task(_listen())

        while True:
            data = await ws.receive_text()
            # echo to all
            await manager.broadcast(data)
    except WebSocketDisconnect:
        manager.disconnect(ws)
    finally:
        if pubsub_task:
            pubsub_task.cancel()
