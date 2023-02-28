from uuid import uuid4
from datetime import datetime

from model.helpers import timestamp_to_datetime


class Message:
    def __init__(self, author: str, text: str, timestamp_sent: float = None, _uuid: str = None):
        if _uuid is None:
            _uuid = uuid4()
        if timestamp_sent is None:
            timestamp_sent = datetime.now().timestamp()
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