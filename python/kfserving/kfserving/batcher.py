import asyncio
from functools import wraps
from inspect import iscoroutinefunction
import time
from typing import Any, Callable, List, Optional, overload, Tuple, TypeVar
import logging


class BatchQueue:
    def __init__(self,
                 max_batch_size: int = 1,
                 timeout_s: float = 0) -> None:
        """Async queue that accepts individual items and returns batches.
        Respects max_batch_size and timeout_s; a batch will be returned when
        max_batch_size elements are available or the timeout has passed since
        the previous get.
        If handle_batch_func is passed in, a background coroutine will run to
        poll from the queue and call handle_batch_func on the results.
        Arguments:
            max_batch_size (int): max number of elements to return in a batch.
            timeout_s (float): time to wait before returning an incomplete
                batch.
        """
        self.queue = asyncio.Queue()
        self.full_batch_event = asyncio.Event()
        self.max_batch_size = max_batch_size
        self.timeout_s = timeout_s

    def set_config(self, max_batch_size: int, timeout_s: float) -> None:
        self.max_batch_size = max_batch_size
        self.timeout_s = timeout_s

    def put(self, request: Any) -> None:
        self.queue.put_nowait(request)
        # Signal when the full batch is ready. The event will be reset
        # in wait_for_batch.
        if self.queue.qsize() == self.max_batch_size:
            self.full_batch_event.set()

    def qsize(self) -> int:
        return self.queue.qsize()

    async def wait_for_batch(self) -> List[Any]:
        """Wait for batch respecting self.max_batch_size and self.timeout_s.
        Returns a batch of up to self.max_batch_size items, waiting for up
        to self.timeout_s for a full batch. After the timeout, returns as many
        items as are ready.
        Always returns a batch with at least one item - will block
        indefinitely until an item comes in.
        """
        curr_timeout = self.timeout_s
        batch = []
        while len(batch) == 0:
            loop_start = time.time()

            # If the timeout is 0, wait for any item to be available on the
            # queue.
            if curr_timeout == 0:
                print("asyncio wait 0")
                logging.info(f"awaiting message in queue {self.qsize()}")
                batch.append(await self.queue.get())
                logging.info(f"batch size {len(batch)}")
            # If the timeout is nonzero, wait for either the timeout to occur
            # or the max batch size to be ready.
            else:
                try:
                    print("asyncio wait")
                    await asyncio.wait_for(self.full_batch_event.wait(),
                                           curr_timeout)
                except asyncio.TimeoutError:
                    pass

            # Pull up to the max_batch_size requests off the queue.
            while len(batch) < self.max_batch_size and not self.queue.empty():
                batch.append(self.queue.get_nowait())

            # Reset the event if there are fewer than max_batch_size requests
            # in the queue.
            if (self.queue.qsize() < self.max_batch_size
                    and self.full_batch_event.is_set()):
                self.full_batch_event.clear()

            # Adjust the timeout based on the time spent in this iteration.
            curr_timeout = max(0, curr_timeout - (time.time() - loop_start))

        return batch
