from model.core import Message, Conversation
import os
import openai
from constants import USERNAME
import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.CRITICAL)
# logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))


def get_user_input() -> Message:
    user_input = input(f'{USERNAME}: ')
    return Message(USERNAME, user_input)


def main():
    conversation = Conversation("de4548e0-d9b6-46aa-be83-f22747d47393")
    while True:

        # Step 1: Get the current context window, ie last 10 messages between the user and the AI.
        # Step 2: Get the current message, search all indexed memories to retrieve facts that have been said that might be similar to the current message
        # Step 3: Feed Current context window, and search results to a language model to predict next response
        # Step 4: Add message to conversation. If conversation.message size is a multiple of 6, create a new document from the last 6 messages, and summarize it and index it
        # Step 5: Add the bot response to the conversation
        # Step 6: Store the summary from step 4 by adding it to the index

        # step 1

        message = get_user_input()
        response = conversation.complete(message)
        print("Brion: ", response.text)
        conversation.add_message(message)
        conversation.add_message(response)
        conversation.save()


if __name__ == '__main__':
    openai.api_key = os.getenv('OPENAI_API_KEY')
    main()
