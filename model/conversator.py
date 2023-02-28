from model.conversation import Conversation
from model.conversation import Message
from model.bloom import CustomLLM

from langchain.agents import ConversationalAgent, Tool, AgentExecutor
from langchain import OpenAI, LLMChain, HuggingFaceHub

from llama_index import Document

from datetime import datetime


class Conversator:
    def __init__(self, conversation: Conversation):
        self.conversation = conversation
        prefix = open("model/prompts/prefix.txt", "r").read()
        tools = [
            Tool(
                name = "Memory Recall",
                func=lambda q: str(self.conversation.idx.query(q)),
                description="Useful when you want to recall a fact. The input should be a question about a fact that might have been mentioned before."
            ),
            Tool(
                name = "Memory Storage",
                func=lambda q: self.conversation.idx.insert(Document(q)),
                description="Useful when you want to store a new fact. The input should be a fact that you want to store."
            )
        ]
        prompt = ConversationalAgent.create_prompt(
            tools, 
            prefix=prefix,
            input_variables=["input", "agent_scratchpad", "chat_history"]
        )
        print(prompt.template)
        llm_chain = LLMChain(llm=CustomLLM(n=10), prompt=prompt)
        tool_names = [tool.name for tool in tools]
        agent = ConversationalAgent(llm_chain=llm_chain, allowed_tools=tool_names)
        self.agent_executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, verbose=True)

    def conversate(self, message: Message, custom_response: Message=None, save=True) -> str:
        self.conversation.add_message(message)
        if custom_response is None:
            window = "\n".join([str(m) for m in self.conversation.context_window])
            response = self.agent_executor.run(input=str(message), chat_history=window)
            response = Message(self.conversation.bot_name, response, datetime.now().timestamp())
            self.conversation.add_message(response)
            self.conversation.save() if save else None
            return response.text
        else:
            self.conversation.add_message(custom_response)
            self.conversation.save() if save else None
            return custom_response.text
            