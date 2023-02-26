import json
from uuid import uuid4, UUID
import datetime
from llama_index import GPTTreeIndex, Document
import openai
import redis
from model.helpers import timestamp_to_datetime


class Message:
    def __init__(self, author: str, text: str, timestamp_sent: float = None, _uuid: str = None):
        if _uuid is None:
            _uuid = uuid4()
        if timestamp_sent is None:
            timestamp_sent = datetime.datetime.now().timestamp()
        self.author = author
        self.text = text
        self.timestamp = timestamp_sent
        self.__uuid = _uuid

    def get_string(self):
        return self.__str__()

    def get_uuid(self):
        return self.__uuid

    def __dict__(self):
        return {'message': self.text, 'author': self.author, 'timestamp': self.timestamp, 'uuid': str(self.__uuid)}

    def __str__(self):
        return f'{self.author} at {timestamp_to_datetime(self.timestamp)}: {self.text}'

    @classmethod
    def from_dict(cls, msg):
        return cls(msg['author'], msg['message'], msg['timestamp'], UUID(msg['uuid']))


class Storage(object):
    _instance = None

    def __init__(self):
        raise RuntimeError('Call instance() instead')

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = redis.Redis.from_url('redis://default:uOVMaPKnHAxnNbJcVRDr@containers-us-west-178.railway.app:6381')
        return cls._instance

    @classmethod
    def save_index(cls, key: str, index: GPTTreeIndex):
        cls.instance().set(key, index.save_to_string())


class Conversation:
    def __init__(self, id: str = str(uuid4())):
        self.id: str = id
        self.idx: GPTTreeIndex = None
        self.context_window: list[Message] = []
        self.context_window_size: int = 0
        self._load()

    def __dict__(self):
        return {'context_window': [msg.__dict__() for msg in self.context_window], 'context_window_size': self.context_window_size, "id": self.id, "idx": self.idx}

    def _load(self):
        value = Storage.instance().get(self.id)
        if value is None:
            self.idx = GPTTreeIndex(documents=[])
            self.context_window = []
            self.context_window_size = 10
        else:
            value = json.loads(value.decode('utf-8'))
            self.idx = GPTTreeIndex.load_from_string(value['index'])
            self.context_window_size = value['context_window_size']
            self.context_window = [
                Message(m.get("author"), m.get("text"), m.get("timestamp")) for m in value['context_window']]

    def _store(self):
        value = {
            'index': self.idx.save_to_string(),
            'context_window_size': self.context_window_size,
            'context_window': [msg.__dict__() for msg in self.context_window]
        }
        Storage.instance().set(self.id, json.dumps(value))

    def add_message(self, message: Message):
        if (self.context_window.__len__() == self.context_window_size):
            doc = Document(
                "\n".join(str(message) for message in self.context_window)
            )
            self.idx.insert(doc)
            self.context_window = []
        self.context_window.append(message)

    def save(self):
        self._store()

    def get_memories(self, message: Message) -> str:
        prompt = open("model/prompts/memory.txt", "r").read()
        prompt = prompt.replace(
            "<<TIMESTAMP>>", timestamp_to_datetime(message.timestamp)
        )
        prompt = prompt.replace(
            "<<AUTHOR>>", message.author
        )
        prompt = prompt.replace(
            "<<CONTENT>>", message.text
        )
        try:
            response = self.idx.query(prompt, mode="summarize")
            return response.response
        except ZeroDivisionError:
            return ''

    def construct_prompt(self, message: Message) -> str:
        memory = self.get_memories(message)
        context = '\n'.join([str(message) for message in self.context_window])
        prompt = open("model/prompts/chat.txt", "r").read()
        prompt = prompt.replace(
            "<<CONTEXT>>", context
        )
        prompt = prompt.replace(
            "<<MEMORY>>", memory
        )
        prompt = prompt.replace(
            "<<CONTEXTSIZE>>", str(self.context_window_size)
        )
        prompt = prompt.replace(
            "<<MESSAGE>>", str(message)
        )
        return prompt

    def complete(self, message: Message) -> Message:
        prompt = self.construct_prompt(message)
        response = openai.Completion.create(
            engine="curie:ft-swype-2023-02-26-22-57-57",
            prompt=prompt,
            max_tokens=256,
            n=1,
            stop="<END>",
            temperature=0.5)

        assert response is not None, "OpenAI call failed"
        assert len(response.choices) > 0, "OpenAI call failed"
        message = response.choices[0].text
        return Message("Brion", message, datetime.datetime.now().timestamp())
