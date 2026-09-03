
from fastapi import WebSocket
from typing import Dict, List

class ConnectionManager:
    def __init__(self):
        # map list_code -> list of active websockets
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, list_code: str, max_connections: int = 50):
        await websocket.accept()
        if list_code not in self.active_connections:
            self.active_connections[list_code] = []
        
        # Previne DoS por exaustão de conexões na mesma lista
        if len(self.active_connections[list_code]) >= max_connections:
            await websocket.close(code=1008)
            return

        self.active_connections[list_code].append(websocket)

    def disconnect(self, websocket: WebSocket, list_code: str):
        if list_code in self.active_connections:
            if websocket in self.active_connections[list_code]:
                self.active_connections[list_code].remove(websocket)
            if len(self.active_connections[list_code]) == 0:
                del self.active_connections[list_code]

    async def broadcast_refresh(self, list_code: str):
        if list_code in self.active_connections:
            for connection in self.active_connections[list_code]:
                try:
                    await connection.send_text('refresh')
                except:
                    pass

manager = ConnectionManager()

