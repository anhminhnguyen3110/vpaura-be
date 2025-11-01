from typing import AsyncGenerator
import asyncio


class StreamingResponse:
    @staticmethod
    async def stream_generator(
        content: AsyncGenerator[str, None]
    ) -> AsyncGenerator[str, None]:
        async for chunk in content:
            yield f"data: {chunk}\n\n"
            await asyncio.sleep(0)
        
        yield "data: [DONE]\n\n"
