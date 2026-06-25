"""
Streaming Response Utilities for Large Datasets

Provides memory-efficient streaming for large API responses.
"""

import asyncio
import json
import logging
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional

from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core.performance_monitor import get_monitor

logger = logging.getLogger(__name__)


async def stream_jsonl(
    data_generator: AsyncGenerator[Dict[str, Any], None],
    buffer_size: int = 100,
) -> StreamingResponse:
    """
    Stream data as JSON Lines (ndjson) format.

    Each line is a complete JSON object, allowing clients to
    process data incrementally without loading everything into memory.

    Args:
        data_generator: Async generator yielding dict objects
        buffer_size: Number of items to buffer before yielding

    Returns:
        StreamingResponse with application/x-ndjson content type
    """

    async def generate():
        buffer = []

        async for item in data_generator:
            buffer.append(item)

            if len(buffer) >= buffer_size:
                for buffered_item in buffer:
                    yield json.dumps(buffered_item, default=str).encode() + b"\n"
                buffer = []

        # Yield remaining items
        for item in buffer:
            yield json.dumps(item, default=str).encode() + b"\n"

    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson",
        headers={
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "no-cache",
        },
    )


async def stream_paginated(
    fetch_page: Callable[[int, int], List[Dict[str, Any]]],
    page_size: int = 100,
    max_pages: Optional[int] = None,
) -> StreamingResponse:
    """
    Stream paginated data efficiently.

    Args:
        fetch_page: Function(page_number, page_size) -> list of items
        page_size: Number of items per page
        max_pages: Maximum number of pages to fetch (None for all)

    Returns:
        StreamingResponse with JSONL format
    """
    monitor = get_monitor()

    async def generate():
        page = 0
        total_items = 0

        with monitor.timer("streaming.paginated", track_memory=False):
            while True:
                if max_pages and page >= max_pages:
                    break

                items = fetch_page(page, page_size)
                if not items:
                    break

                for item in items:
                    yield json.dumps(item, default=str).encode() + b"\n"

                total_items += len(items)
                page += 1

                # Small yield to allow other tasks
                if page % 10 == 0:
                    await asyncio.sleep(0)

        logger.debug(f"Streamed {total_items} items in {page} pages")

    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson",
    )


class LazyDataLoader:
    """
    Lazy loader for large datasets with pagination support.

    Loads data on-demand in chunks to minimize memory usage.
    """

    def __init__(
        self,
        fetch_chunk: Callable[[int, int], List[Dict[str, Any]]],
        chunk_size: int = 100,
        prefetch_chunks: int = 1,
    ):
        self.fetch_chunk = fetch_chunk
        self.chunk_size = chunk_size
        self.prefetch_chunks = prefetch_chunks
        self._buffer: List[Dict[str, Any]] = []
        self._current_chunk = 0
        self._exhausted = False
        self._total_loaded = 0

    async def __aiter__(self):
        """Make async iterable"""
        return self

    async def __anext__(self) -> Dict[str, Any]:
        """Get next item"""
        # Refill buffer if needed
        while not self._buffer and not self._exhausted:
            await self._load_next_chunk()

        if self._buffer:
            self._total_loaded += 1
            return self._buffer.pop(0)

        raise StopAsyncIteration

    async def _load_next_chunk(self):
        """Load next chunk of data"""
        if self._exhausted:
            return

        chunk = self.fetch_chunk(self._current_chunk, self.chunk_size)

        if chunk:
            self._buffer.extend(chunk)
            self._current_chunk += 1
        else:
            self._exhausted = True

    def get_stats(self) -> Dict[str, Any]:
        """Get loader statistics"""
        return {
            "total_loaded": self._total_loaded,
            "current_chunk": self._current_chunk,
            "buffer_size": len(self._buffer),
            "exhausted": self._exhausted,
        }


async def stream_large_query(
    db_session,
    query,
    batch_size: int = 1000,
    transform: Optional[Callable[[Any], Dict[str, Any]]] = None,
) -> StreamingResponse:
    """
    Stream results from a large database query.

    Args:
        db_session: Database session
        query: SQLAlchemy query object
        batch_size: Number of rows per batch
        transform: Optional function to transform each row

    Returns:
        StreamingResponse
    """
    monitor = get_monitor()

    async def generate():
        with monitor.timer("streaming.database_query", track_memory=False):
            offset = 0
            total_rows = 0

            while True:
                # Fetch batch
                batch = query.offset(offset).limit(batch_size).all()

                if not batch:
                    break

                for row in batch:
                    # Transform row if needed
                    if transform:
                        data = transform(row)
                    else:
                        # Default: convert to dict
                        data = {column.name: getattr(row, column.name) for column in row.__table__.columns}

                    yield json.dumps(data, default=str).encode() + b"\n"

                total_rows += len(batch)
                offset += batch_size

                # Yield control periodically
                if offset % (batch_size * 10) == 0:
                    await asyncio.sleep(0)

            logger.debug(f"Streamed {total_rows} database rows")

    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson",
    )


async def stream_text_chunks(
    text_generator: AsyncGenerator[str, None],
    chunk_prefix: str = "data: ",
    chunk_suffix: str = "\n\n",
) -> StreamingResponse:
    """
    Stream text data in SSE (Server-Sent Events) format.

    Useful for streaming LLM responses or real-time updates.

    Args:
        text_generator: Async generator yielding text chunks
        chunk_prefix: Prefix for each chunk (default: SSE format)
        chunk_suffix: Suffix for each chunk

    Returns:
        StreamingResponse with text/event-stream content type
    """

    async def generate():
        async for chunk in text_generator:
            yield f"{chunk_prefix}{chunk}{chunk_suffix}".encode()

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


class PaginatedResponse(BaseModel):
    """Standard paginated response model"""

    items: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    has_more: bool


def create_paginated_response(
    items: List[Dict[str, Any]],
    total: int,
    page: int,
    page_size: int,
) -> Dict[str, Any]:
    """Create standard paginated response"""
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_more": (page + 1) * page_size < total,
    }


async def paginated_streaming_response(
    total_count: int,
    fetch_page: Callable[[int, int], List[Dict[str, Any]]],
    page_size: int = 100,
) -> StreamingResponse:
    """
    Stream paginated data with metadata.

    First line contains metadata, subsequent lines contain items.
    """

    async def generate():
        # First line: metadata
        metadata = {
            "type": "metadata",
            "total": total_count,
            "page_size": page_size,
            "estimated_pages": (total_count + page_size - 1) // page_size,
        }
        yield json.dumps(metadata).encode() + b"\n"

        # Stream items
        page = 0
        while True:
            items = fetch_page(page, page_size)
            if not items:
                break

            for item in items:
                wrapped = {"type": "item", "data": item}
                yield json.dumps(wrapped).encode() + b"\n"

            page += 1

        # End marker
        yield json.dumps({"type": "complete"}).encode() + b"\n"

    return StreamingResponse(
        generate(),
        media_type="application/x-ndjson",
    )


__all__ = [
    "stream_jsonl",
    "stream_paginated",
    "stream_large_query",
    "stream_text_chunks",
    "LazyDataLoader",
    "PaginatedResponse",
    "create_paginated_response",
    "paginated_streaming_response",
]
