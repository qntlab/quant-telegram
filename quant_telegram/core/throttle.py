"""Message throttling system for quant-telegram."""

import asyncio
import time
from typing import Dict, Set, Optional
from dataclasses import dataclass, field


@dataclass
class ThrottleState:
    """Tracks throttling state for a specific message type/key."""
    last_sent: float = 0.0
    pending_messages: list = field(default_factory=list)
    task: Optional[asyncio.Task] = None


class MessageThrottle:
    """Manages message throttling and batching."""
    
    def __init__(self):
        self._states: Dict[str, ThrottleState] = {}
        self._lock = asyncio.Lock()
    
    async def should_send_immediately(self, message_type: str, throttle_seconds: int, key: str = "") -> bool:
        """Check if message should be sent immediately (no throttling)."""
        if throttle_seconds == 0:  # Emergency messages
            return True
        
        throttle_key = f"{message_type}:{key}"
        
        async with self._lock:
            state = self._states.get(throttle_key)
            if not state:
                self._states[throttle_key] = ThrottleState(last_sent=time.time())
                return True
            
            elapsed = time.time() - state.last_sent
            if elapsed >= throttle_seconds:
                state.last_sent = time.time()
                return True
            
            return False
    
    async def queue_message(self, message_type: str, throttle_seconds: int, message: str, 
                          send_callback, key: str = "") -> None:
        """Queue a message for batched sending."""
        if throttle_seconds == 0:  # Emergency - send immediately
            await send_callback(message)
            return
        
        throttle_key = f"{message_type}:{key}"
        
        async with self._lock:
            if throttle_key not in self._states:
                self._states[throttle_key] = ThrottleState()
            
            state = self._states[throttle_key]
            state.pending_messages.append(message)
            
            # If no batch task is running, start one
            if state.task is None or state.task.done():
                state.task = asyncio.create_task(
                    self._batch_sender(throttle_key, throttle_seconds, send_callback)
                )
    
    async def _batch_sender(self, throttle_key: str, throttle_seconds: int, send_callback) -> None:
        """Handle batched message sending."""
        await asyncio.sleep(throttle_seconds)
        
        async with self._lock:
            state = self._states.get(throttle_key)
            if not state or not state.pending_messages:
                return
            
            messages = state.pending_messages.copy()
            state.pending_messages.clear()
            state.last_sent = time.time()
        
        # Send batched messages
        if len(messages) == 1:
            await send_callback(messages[0])
        else:
            # Combine multiple messages with separators
            batched_message = "\n---\n".join(messages)
            await send_callback(f"📊 <b>Batched Updates ({len(messages)})</b>\n\n{batched_message}")
    
    async def cleanup(self) -> None:
        """Cancel all pending tasks."""
        async with self._lock:
            for state in self._states.values():
                if state.task and not state.task.done():
                    state.task.cancel()
            self._states.clear()