from model.core import Message
from model.messageparser import MessageParser
import datetime
import pprint


def test_imessage():
    print("parsing...")
    parser = MessageParser("imessage", "chat.txt")
    messages = parser.parse()
    # pprint.pprint(messages)

    # messages should be an array
    assert isinstance(messages, list)

    # message should be Message object
    for message in messages:
        assert isinstance(message, Message)

    # messages date should be in ascending order
    prev_date = datetime.datetime(2000, 1, 1).timestamp()
    for message in messages:
        assert message.timestamp >= prev_date
        prev_date = message.timestamp

    # combining consecutive messages from the same sender
    prev_author = None
    for message in messages:
        assert message.author != prev_author
        prev_author = message.author
