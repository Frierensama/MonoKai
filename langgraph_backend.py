from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun

from langgraph.graph.state import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3

from typing import Annotated, TypedDict, List, Literal
from dotenv import load_dotenv
import os

load_dotenv()


# TOOLS
search_tool = DuckDuckGoSearchRun()

@tool
def calculator(first_num:float, second_num:float,operation:str)->dict:
    """
    perform basic arithemic operations
    supported operations : add, sub, mul, div
    """
    result = 0.0
    if operation == 'add':
        result = first_num + second_num
    elif operation == 'sub':
        result = first_num - second_num
    elif operation == 'mul':
        result = first_num * second_num
    elif operation == 'div':
        if second_num == 0:
            return {'error':'cannot divide with zero'}
        else:
            result = first_num / second_num
    else:
        return {'error':f'unsupported operation {operation}'}

    return {'first_num':first_num,'second_num':second_num,'operation':operation,'result':result}


tools = [calculator, search_tool]

# LLM
llm_endpoint = HuggingFaceEndpoint(
    repo_id=os.getenv('hf_model'),
    provider='together'
    )
model = ChatHuggingFace(llm=llm_endpoint)

google_model = ChatGoogleGenerativeAI(model='gemini-3.1-flash-lite')

google_model_with_tools = google_model.bind_tools(tools=tools)


# STATE GRAPH -- WORKFLOW
class ChatSchema(TypedDict):
    topic:str
    messages:Annotated[List[BaseMessage], add_messages]


def chat_node(state:ChatSchema):
    messages = state['messages']
    response = google_model_with_tools.invoke(messages) 
    # response itself is Ai message, so, when i comeback again, dont need to extract content and send as AImessage
    return {'messages':[response]}


conn = sqlite3.connect(database='Akai.db',check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)

stategraph = StateGraph(state_schema=ChatSchema)


stategraph.add_node('chat_node',chat_node)
stategraph.add_node('tools',ToolNode(tools))

stategraph.add_edge(START,'chat_node')
stategraph.add_conditional_edges('chat_node',tools_condition)
stategraph.add_edge('tools','chat_node')


workflow = stategraph.compile(checkpointer=checkpointer)

# UTILITY FUNCS
def get_all_thread_ids():
    thread_ids = set()
    for checkpoint in checkpointer.list(None):
        thread_ids.add(checkpoint.config['configurable']['thread_id'])

    return list(thread_ids)

def get_title(thread_id)->str:

    state = workflow.get_state(config={'configurable':{'thread_id':thread_id}})
    first_message_content =  state.values['messages'][0].content if 'messages' in state.values else thread_id

    title = ''
    if len(first_message_content) < 32:
        title = first_message_content
    else:
        title = first_message_content[:32]

    return title