
import redis
from llama_index import GPTListIndex

class Storage(object):
    _instance = None

    def __init__(self):
        raise RuntimeError('Call instance() instead')

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = redis.Redis(
                host='localhost',
                port=6379,
                db=0
            )
        return cls._instance

    @classmethod
    def save_index(cls, key: str, index: GPTListIndex):
        cls.instance().set(key, index.save_to_string())