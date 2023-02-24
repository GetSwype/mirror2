from time import time
from typing import List
from uuid import uuid4
import os

import openai

from constants import USERNAME, BOT_NAME
from gpt3_helpers import vector_similarity, gpt3_embedding, gpt3_completion
from models import Message, Conversation, Note
from utils import open_file, save_json, timestamp_to_datetime
from llama_index import GPTTreeIndex, Document


def fetch_memories(vector, logs, count):
    scores = list()
    for i in logs:
        if vector == i['vector']:
            # skip this one because it is the same message
            continue
        score = vector_similarity(i['vector'], vector)
        i['score'] = score
        scores.append(i)
    ordered = sorted(scores, key=lambda d: d['score'], reverse=True)
    # TODO - pick more memories temporally nearby the top most relevant memories
    try:
        ordered = ordered[0:count]
        return ordered
    except:
        return ordered


def summarize_memories(memories):  # summarize a block of memories into one payload
    memories = sorted(memories, key=lambda d: d['time'], reverse=False)  # sort them chronologically
    block = ''
    identifiers = list()
    timestamps = list()
    for mem in memories:
        block += mem['message'] + '\n\n'
        identifiers.append(mem['uuid'])
        timestamps.append(mem['time'])
    block = block.strip()
    prompt = open_file('prompt_notes.txt').replace('<<INPUT>>', block)
    # TODO - do this in the background over time to handle huge amounts of memories
    notes = gpt3_completion(prompt)
    return notes
    # notes.split('\n')
    # vector = gpt3_embedding(block)
    # info = {'notes': notes, 'uuids': identifiers, 'times': timestamps, 'uuid': str(uuid4()), 'vector': vector}
    # filename = 'notes_%s.json' % time()
    # save_json('notes/%s' % filename, info)
    # return notes


def get_last_messages(conversation, limit):
    try:
        short = conversation[-limit:]
    except:
        short = conversation
    output = ''
    for i in short:
        output += '%s\n\n' % i['message']
    output = output.strip()
    return output


def get_user_input() -> Message:
    user_input = input(f'{USERNAME}: ')
    return Message(USERNAME, user_input)


def search_conversation(conversation: Conversation, message: Message) -> List[Message]:
    """
    Search the conversation for messages that are related to the given message

    :param conversation: Conversation object, the conversation to search
    :param message: Message object, that we want to find related messages for
    :return: List of messages that are related to the given message
    """
    message_list = conversation.get_messages()
    query_vector = gpt3_embedding(message.text)
    similarities = {}
    for message in message_list:
        # TODO: don't store the entire message in memory, just the vector/uuid
        similarities[message] = vector_similarity(query_vector, message.vector)
        # get the top 3 most similar messages
    ordered = [i[0] for i in sorted(similarities.items(), key=lambda x: x[1], reverse=True)[:6]]
    return ordered


def summarize_notes(notes):
    prompt = open_file('prompts/compress_notes.txt').replace('<<NOTES>>', '\n- '.join([note.note_text for note in notes]))
    result = gpt3_completion(prompt)
    return [Note(i.strip()) for i in result.split('- ')]

def open_index_file():
    file_name = 'index.json'
    try:
        # Open the file for reading
        with open(file_name, 'r') as file:
            # Read the contents of the file
            index = GPTTreeIndex.load_from_disk(file_name)
            print('Loaded index from: ', file_name)
            return index
    except FileNotFoundError:
        # If the file does not exist, create it and write some default text
        with open(file_name, 'w') as file:
            tree_index = GPTTreeIndex([])
            tree_index.save_to_disk(file_name)
            print('No index file found. Created: ', file_name)
            return tree_index

def main():
    conversation = Conversation.load()
    index = open_index_file()
    while True:

        # Step 1: Get the current context window, ie last 12 messages.
        # Step 2: Get the current message, search all indexed memories to retrieve facts that have been said
        # Step 3: Feed Current context window, and search results to a language model to predict next response
        # Step 4: Add message to conversation. If conversation.message size is a multiple of 12, create a new document from the last 12 messages, and summarize it and index it
        # Step 5: Store this new memory by adding it to the index

        # step 1
        message = get_user_input()
        context_window = conversation.get_last_messages_in_string(12)

        # step 2
        index_search_prompt = (
            open_file('prompts/prompt_index_search.txt')
            .replace('<<CURRENT QUERY>>', message.get_string())
        )
        last_6_messages = conversation.get_last_messages_in_string(12)  # get last 6 messages as a string
        search_results = index.query(index_search_prompt)

        # step 3
        response_prompt = (
            open_file('prompts/prompt_response.txt')
            .replace('<<CONVERSATION>>', last_6_messages)
            .replace('<<MEMORIES>>', search_results)
            .replace('<<CHAT>>', message.get_string())
        )
        response = gpt3_completion(response_prompt)
        print("Liza: %s" % response)

        # step 4
        
        if len(conversation.get_messages()) % 12 == 0:
            # create a new memory
            new_memory = summarize_memories(conversation.get_last_messages(12))
            index.insert(Document(new_memory))
        conversation.add_message(message)
        # # step 3
        # search_queries = [i.strip() for i in gpt3_completion(gather_info_prompt).split('- ') if i.strip() != '']
        # # step 4
        # related_messages = search_conversation(conversation, message)
        # # facts = [f"Question: {i}; Answer: {input(i)}" for i in search_queries] # lmao
        # # step 5
        # if len(related_messages) > 10:
        #     answer_prompt = (
        #         open_file('prompts/prompt_response.txt')
        #         .replace('<<CONVERSATION>>', last_6_messages)
        #         .replace('<<NOTES>>', notes)
        #         .replace('<<MESSAGES_RELATED>>', '\n'.join([i.get_string() for i in related_messages]))
        #         # .replace('<<FACTS>>', '\n'.join(facts))
        #     )
        # else:
        #     answer_prompt = (
        #         open_file('prompts/prompt_response_in_new_conversation.txt').replace('<<CONVERSATION>>', last_6_messages)
        #     )
        # # step 6
        # answer = gpt3_completion(answer_prompt)
        # print(f'{BOT_NAME}: {answer}')
        # conversation.add_message(Message(BOT_NAME, answer))
        # # step 7
        # notes_prompt = open_file('prompts/prompt_notes.txt').replace('<<INPUT>>', last_6_messages)
        # notes = [i.strip() for i in gpt3_completion(notes_prompt).split('- ')]

        # [conversation.add_note(Note(note)) for note in notes]
        # if len(conversation.get_notes()) > 10:
        #     # compress notes
        #     notes = conversation.get_notes()
        #     notes = summarize_notes(notes)
        #     conversation.set_notes(notes)
        # # step 8
        conversation.save()


if __name__ == '__main__':
    openai.api_key = os.getenv('OPENAI_API_KEY')
    main()
