import streamlit as st
from langgraph_backend import workflow, get_all_thread_ids, get_title
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
import uuid

st.set_page_config(page_title='𝙰𝚔𝚊𝚒',page_icon='🍥')

# --------------------------- utilities  -----------------------------
def gen_thread_id():
    thread_id = uuid.uuid4()
    return str(thread_id)

def new_chat():
    new_thread_id = gen_thread_id()
    add_thread_id(new_thread_id)
    st.session_state['thread_id'] = new_thread_id
    st.session_state['chat_messages'] = []

def add_thread_id(thread_id):
    if thread_id not in st.session_state['chat_thread_ids']:
        st.session_state['chat_thread_ids'].append(thread_id)

def load_thread_messages(thread_id):
    thread_chat_history = workflow.get_state(config={'configurable':{'thread_id':thread_id}}).values['messages'] if 'messages' in workflow.get_state(config={'configurable':{'thread_id':thread_id}}).values else []

    temp_chat_history = []
    for msg in thread_chat_history:
        if isinstance(msg, HumanMessage):
            role = 'user'
        elif isinstance(msg, AIMessage):
            role = 'assistant'
        else:
            continue
        if (extract_text(msg) != '') and (extract_text(msg) != None):
            temp_chat_history.append({'role':role, 'content':extract_text(msg)})

    return temp_chat_history

def extract_text(message_chunk):

    content = message_chunk.content

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text = ""

        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    text += block.get("text", "")
                elif "text" in block:
                    text += block["text"]

        return text

    return ""
    
#----------------------------- session setup  -----------------------------------
if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = gen_thread_id()

if 'chat_messages' not in st.session_state:
    st.session_state['chat_messages'] = []

if 'chat_thread_ids' not in st.session_state:
    st.session_state['chat_thread_ids'] = get_all_thread_ids()

add_thread_id(st.session_state['thread_id'])

CONFIG = {
    'configurable':{'thread_id':st.session_state['thread_id']},
    'metadata': {'thread_id':st.session_state['thread_id']},
    'run_name' : 'mercury'
    }
# ---------------------------- sidebar  -----------------------------------

st.sidebar.title('**ＡＫＡＩ－２.９**',width='content')

if st.sidebar.button('New Chat'):
    new_chat()

st.sidebar.header('My Chats')

for thread_id in st.session_state['chat_thread_ids'][::-1]:

    if st.sidebar.button(label=get_title(thread_id), key=thread_id):
        st.session_state['thread_id'] = thread_id
        st.session_state['chat_messages'] = load_thread_messages(thread_id=thread_id)
        

# --------------------------- User Interaction ------------------------------------

for message in st.session_state['chat_messages']:
    with st.chat_message(message['role']):
        st.text(message['content'])


userinput = st.chat_input('Type Here..')

if userinput:

    st.session_state['chat_messages'].append({'role':'user','content':userinput})
    with st.chat_message('user'):
        st.text(userinput)
    

    with st.chat_message('assistant'):

        status_holder = {'box':None}

        def ai_message_only(): 
            for message_chunk, metadata in workflow.stream({'messages':[HumanMessage(content=userinput)]},config=CONFIG,stream_mode='messages'):
                if isinstance(message_chunk, ToolMessage):
                    tool_name = getattr(message_chunk, "name", "tool")
                    if status_holder["box"] is None:
                        status_holder["box"] = st.status(
                            f"Using `{tool_name}` …", expanded=True
                        )
                    else:
                        status_holder["box"].update(
                            label=f"Using `{tool_name}` …",
                            state="running",
                            expanded=True,
                        )

                if isinstance(message_chunk,AIMessage):
                    yield extract_text(message_chunk)

        ai_message = st.write_stream(ai_message_only())

        if status_holder["box"] is not None:
            status_holder["box"].update(
                label="🍥Tool finished", state="complete", expanded=False
            )
    st.session_state['chat_messages'].append({'role':'assistant', 'content':ai_message})
