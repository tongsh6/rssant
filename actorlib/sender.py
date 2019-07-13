import logging
import asyncio
import queue
from threading import Thread

from .client import AsyncActorClient
from .helper import kill_thread


LOG = logging.getLogger(__name__)


class MessageSender:

    def __init__(self, registery, concurrency=100):
        self.registery = registery
        self.concurrency = concurrency
        self.outbox = queue.Queue(concurrency * 2)
        self._thread = None
        self._stop = False

    async def _main(self):
        client = AsyncActorClient(registery=self.registery)
        async with client:
            while not self._stop:
                messages = []
                while (not self._stop) and len(messages) < self.concurrency:
                    try:
                        messages.append(self.outbox.get_nowait())
                    except queue.Empty:
                        await asyncio.sleep(0.1)
                        try:
                            while (not self._stop) and len(messages) < self.concurrency:
                                messages.append(self.outbox.get_nowait())
                        except queue.Empty:
                            pass
                        break
                if messages:
                    await client.send(*messages)
                    messages = []

    def main(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._main())

    async def async_submit(self, message):
        while True:
            try:
                return self.outbox.put_nowait(message)
            except queue.Full:
                await asyncio.sleep(0.1)

    def submit(self, message):
        return self.outbox.put(message)

    def start(self):
        self._thread = Thread(target=self.main)
        self._thread.daemon = True
        self._thread.start()

    def shutdown(self):
        self._stop = True
        if self._thread.is_alive():
            kill_thread(self._thread.ident)

    def join(self):
        self._thread.join()