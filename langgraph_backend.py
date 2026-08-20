from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

from langgraph.graph.state import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.message import add_messages

from typing import Annotated, TypedDict, List, Dict
from dotenv import load_dotenv
import os
load_dotenv()

llm_endpoint = HuggingFaceEndpoint(
    repo_id=os.getenv('hf_model'),
    provider='together'
    )
model = ChatHuggingFace(llm=llm_endpoint)

google_model = ChatGoogleGenerativeAI(model='gemini-3.6-flash')

class ChatSchema(TypedDict):
    topic:str
    messages:Annotated[List[BaseMessage], add_messages]


def chat_node(state:ChatSchema):
    messages = state['messages']
    response = google_model.invoke(messages)
    return {'messages':[AIMessage(content=response.content)]}


checkpointer = InMemorySaver()

stategraph = StateGraph(state_schema=ChatSchema)
# nodes
stategraph.add_node('chat_node',chat_node)

# edges
stategraph.add_edge(START,'chat_node')
stategraph.add_edge('chat_node',END)

workflow = stategraph.compile(checkpointer=checkpointer)
