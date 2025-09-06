"""WebSocket for real-time indexing progress."""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Any
import asyncio
import json
from loguru import logger
from collections import deque
from datetime import datetime

class IndexingProgressManager:
    """Manages indexing progress for multiple clients."""
    
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.progress_data = {
            "status": "idle",
            "current_file": None,
            "processed_files": [],
            "failed_files": [],
            "total_files": 0,
            "completed_files": 0,
            "chunks_created": 0,
            "start_time": None,
            "messages": deque(maxlen=100)  # Keep last 100 messages
        }
        self.lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        # Send current state to new connection (convert deque to list)
        json_data = dict(self.progress_data)
        json_data['messages'] = list(self.progress_data['messages'])
        await websocket.send_json(json_data)
        logger.info(f"WebSocket client connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, data: Dict[str, Any]):
        """Broadcast data to all connected clients."""
        if not self.active_connections:
            logger.warning("No active WebSocket connections to broadcast to")
            return
            
        disconnected = []
        # Convert deque to list for JSON serialization
        json_data = dict(data)
        if 'messages' in json_data:
            json_data['messages'] = list(json_data['messages'])
        
        logger.debug(f"Broadcasting to {len(self.active_connections)} clients: status={json_data.get('status')}, current_file={json_data.get('current_file')}")
        
        for connection in self.active_connections:
            try:
                await connection.send_json(json_data)
            except Exception as e:
                logger.error(f"Error sending to WebSocket: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect(conn)
    
    async def update_progress(self, update: Dict[str, Any]):
        """Update progress and broadcast to clients."""
        async with self.lock:
            # Update progress data
            for key, value in update.items():
                if key == "message":
                    # Add message with timestamp
                    self.progress_data["messages"].append({
                        "time": datetime.now().isoformat(),
                        "text": value
                    })
                else:
                    self.progress_data[key] = value
            
            # Broadcast to all clients
            await self.broadcast(self.progress_data)
    
    async def start_indexing(self, total_files: int):
        """Mark the start of indexing."""
        await self.update_progress({
            "status": "indexing",
            "total_files": total_files,
            "completed_files": 0,
            "processed_files": [],
            "failed_files": [],
            "chunks_created": 0,
            "start_time": datetime.now().isoformat(),
            "message": f"Starting indexing of {total_files} files..."
        })
    
    async def file_processing(self, filename: str):
        """Mark a file as being processed."""
        await self.update_progress({
            "current_file": filename,
            "message": f"Processing: {filename}"
        })
    
    async def file_completed(self, filename: str, chunks: int, success: bool):
        """Mark a file as completed."""
        if success:
            self.progress_data["processed_files"].append(filename)
            self.progress_data["chunks_created"] += chunks
            message = f"✓ Completed: {filename} ({chunks} chunks)"
        else:
            self.progress_data["failed_files"].append(filename)
            message = f"✗ Failed: {filename}"
        
        self.progress_data["completed_files"] += 1
        self.progress_data["current_file"] = None
        
        await self.update_progress({"message": message})
    
    async def finish_indexing(self):
        """Mark the end of indexing."""
        await self.update_progress({
            "status": "completed",
            "current_file": None,
            "message": f"Indexing completed: {len(self.progress_data['processed_files'])} success, {len(self.progress_data['failed_files'])} failed"
        })
    
    def reset(self):
        """Reset progress data."""
        self.progress_data = {
            "status": "idle",
            "current_file": None,
            "processed_files": [],
            "failed_files": [],
            "total_files": 0,
            "completed_files": 0,
            "chunks_created": 0,
            "start_time": None,
            "messages": deque(maxlen=100)
        }

# Global instance
progress_manager = IndexingProgressManager()