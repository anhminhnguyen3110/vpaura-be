from typing import AsyncGenerator, Dict, Any
import asyncio
import json


class StreamingResponse:
    @staticmethod
    async def stream_generator(
        content: AsyncGenerator[Dict[str, Any], None]
    ) -> AsyncGenerator[str, None]:
        """
        Convert StreamChunk dicts to SSE format.
        
        Args:
            content: AsyncGenerator yielding StreamChunk dicts
            
        Yields:
            SSE formatted strings: "data: {...}\n\n"
        """
        async for chunk in content:
            # chunk is already a dict from StreamChunk.model_dump()
            yield f"data: {json.dumps(chunk)}\n\n"
            await asyncio.sleep(0)

