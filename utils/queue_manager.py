import asyncio
from collections import deque

class QueueManager:
    def __init__(self, max_concurrent=3):
        self.queue = deque()
        self.active_tasks = set()
        self.max_concurrent = max_concurrent

    async def add_to_queue(self, coro):
        await self.queue.append(coro)
        await self.process_queue()

    async def process_queue(self):
        while self.queue and len(self.active_tasks) < self.max_concurrent:
            coro = self.queue.popleft()
            task = asyncio.create_task(coro)
            self.active_tasks.add(task)
            task.add_done_callback(self.task_done)

    def task_done(self, task):
        self.active_tasks.remove(task)
        asyncio.create_task(self.process_queue())

    async def wait_until_complete(self):
        while self.queue or self.active_tasks:
            await asyncio.sleep(0.1)
