
from enum import Enum
from llama_index import GPTTreeIndex, GPTVectorStoreIndex, GPTListIndex, GPTKeywordIndex, playground

import openai
import asyncio


class IndexType(Enum):
    TREE = 1
    LIST = 2
    VECTOR = 3
    KEYWORD = 4
    CUSTOM = 5


class Indexer:
    def __init__(self, index=None, type=None):
        self.index = index
        self.type = type

    def _synthesize_responses(
        self,
        dataset: str
    ) -> dict[IndexType: str]:
        model_engine = "davinci-003"
        prompt = f'''
        Construct a query in natural language for the following dataset: 
        {dataset}

        Your query should be in the form of a question, and should be able to be answered by the dataset. Ensure that the query
        is not too specific on literal values, but rather focuses on the general structure of the dataset. For example, if the
        dataset is a list of chat messages, a good query would be another chat message, and a bad query would be a a specific question
        such as: "what is the most common greeting in the dataset?"

        Response: 
        '''
        response = openai.Completion.create(
            engine=model_engine,
            prompt=prompt,
            max_tokens=256,
            n=1,
            stop=None,
            temperature=0.5,
        )
        message = response.choices[0].text
        return message

    async def _example_index_types(self, query: str, dataset: str) -> dict[IndexType: str]:
        def get_chunks(l, n):
            for i in range(0, len(l), n):
                yield l[i:i + n]
        indices_promises = [
            GPTTreeIndex(documents=get_chunks(dataset, 2048)),
            GPTVectorStoreIndex(documents=get_chunks(dataset, 2048)),
            GPTListIndex(documents=get_chunks(dataset, 2048)),
            GPTKeywordIndex(documents=get_chunks(dataset, 2048)),
        ]
        indices = await asyncio.gather(*indices_promises)
        sandbox = playground.Playground(
            indices=indices,
        )
        responses = sandbox.compare(query)
        print(responses)
        return responses

    def index_file(self, file_path):
        with open(file_path, 'r') as f:
            for line in f:
                for word in line.split():
                    self.index.add(word)
