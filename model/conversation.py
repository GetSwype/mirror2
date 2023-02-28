from llama_index import GPTListIndex

from uuid import uuid4
import json

from model.message import Message
from model.storage import Storage


class Conversation:
    def __init__(self, id: str = str(uuid4()), context_window_size: int = 10, bot_name: str="AI"):
        self.id: str = id
        self.idx: GPTListIndex = None
        self.context_window: list[Message] = []
        self.context_window_size: int = context_window_size
        self.bot_name = bot_name
        self._load()

    def _load(self):
        value = Storage.instance().get(self.id)
        if value is None:
            self.idx = GPTListIndex(documents=[])
            self.context_window = []
        else:
            value = json.loads(value.decode('utf-8'))
            self.idx = GPTListIndex.load_from_string(value['index'])
            self.context_window_size = value['context_window_size']
            self.context_window = [
                Message(m["author"], m["message"], m["timestamp"]) for m in value['context_window']
            ]

    def _store(self):
        value = {
            'index': self.idx.save_to_string(),
            'context_window_size': self.context_window_size,
            'context_window': [msg.__dict__() for msg in self.context_window]
        }
        Storage.instance().set(self.id, json.dumps(value))

    def add_message(self, message: Message):
        self.context_window.append(message)
        if (self.context_window.__len__() == self.context_window_size):
            self.context_window.pop(0)

    def save(self):
        self._store()