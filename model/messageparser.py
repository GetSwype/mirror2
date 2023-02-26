import datetime
from core import Message


class MessageParser:
    def __init__(self, type: str, file: str) -> None:
        self.type = type
        self.file = file

    def parse(self) -> list[Message]:
        """This method parses the data and returns a list of messages

        Args:
            data (str): The data to parse

        Returns:
            list[Message]: The list of messages
        """
        data = (open(self.file, "r").read())
        if self.type == "imessage":
            return self._imessage(data)
        elif self.type == "telegram":
            raise NotImplementedError("Telegram parser not implemented")
        elif self.type == "discord":
            raise NotImplementedError("Discord parser not implemented")
        else:
            raise ValueError("Invalid parser type")

    def _imessage(self, data: str) -> list[Message]:
        """This method parses the data and returns a list of messages

        Args:
            data (str): The data to parse

        Returns:
            list[Message]: The list of messages
        """
        lines = data.split(
            "----------------------------------------------------")
        lines = [line for line in lines if line != '\n']
        lines = [line.strip() for line in lines if line.strip()]

        def get_parsed_message(message) -> Message:
            try:
                tmp = [x for x in message.split("\n") if x != '']
                if (len(tmp) != 2):
                    return None
                header, msg = tmp[0], tmp[1].strip()
                if (("Liked " in msg) or ("Loved " in msg) or ("Disliked " in msg) or ("Emphasized " in msg)):
                    return None
                _date, _time, _direction, _person,  = header.split(" ")
                _datetime = _date + " " + _time
                _from = _person if _direction == "from" else "srikanth"
                _to = _person if _direction == "to" else "srikanth"
                # convert datetime to float
                # 2021-01-13 21:54:13
                _timestamp = datetime.datetime.strptime(
                    _datetime, "%Y-%m-%d %H:%M:%S").timestamp()
                parsed_message = Message(
                    _from,
                    msg,
                    _timestamp
                )
                return parsed_message
            except:
                return None

        print(
            f"Skipping {lines.count(None)} messages because they are not formatted correctly or there is an exception")

        # filter out None values
        messages = [get_parsed_message(line) for line in lines if line != None]
        messages = [m for m in messages if m != None]

        final = []

        def combine(message_1: Message, message_2: Message):
            if (message_1.author == message_2.author):
                return Message(message_1.author, message_1.text + ". " + message_2.text, message_1.timestamp)
            return None

        msg_idx = 0
        while msg_idx < len(messages):
            combined_message = messages[msg_idx]
            next_msg_index = msg_idx + 1
            while next_msg_index < msg_idx + 20:
                try:
                    next_message = messages[next_msg_index]
                    _combined_message = combine(combined_message, next_message)
                    if (_combined_message is None):
                        break
                    else:
                        combined_message = _combined_message
                        next_msg_index += 1
                except:
                    break

            final.append(combined_message)
            msg_idx = next_msg_index

        print(f"{final.__len__()}")
        return final
