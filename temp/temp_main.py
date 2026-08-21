import streamlit as st
from langgraph_backend import workflow
from langchain_core.messages import HumanMessage, AIMessage
import uuid

st.set_page_config(page_title='Tsuki',page_icon='🍥')

# --------------------------- utilities  -----------------------------
def gen_thread_id():
    thread_id = uuid.uuid4()
    return thread_id

def new_chat():
    new_thread_id = gen_thread_id()
    add_thread_id(new_thread_id)
    st.session_state['thread_id'] = new_thread_id
    st.session_state['chat_messages'] = []

def add_thread_id(thread_id):
    if thread_id not in st.session_state['chat_thread_ids']:
        st.session_state['chat_thread_ids'].append(thread_id)

def load_thread_messages(thread_id):
    return workflow.get_state(config={'configurable':{'thread_id':thread_id}}).values['messages']

#----------------------------- session setup  -----------------------------------
if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = gen_thread_id()
    st.session_state['chat_thread_ids'] = [st.session_state['thread_id']]

if 'chat_messages' not in st.session_state:
    st.session_state['chat_messages'] = []



CONFIG = {'configurable':{'thread_id':st.session_state['thread_id']}}
# ---------------------------- sidebar  -----------------------------------

st.sidebar.title('`Clove 1.1`',width='stretch')

if st.sidebar.button('New Chat'):
    new_chat()

st.sidebar.header('My Chats')

for thread_id in st.session_state['chat_thread_ids']:
    if st.sidebar.button(str(thread_id)):
        st.session_state['thread_id'] = thread_id
        thread_chat_history = load_thread_messages(thread_id)

        temp_chat_history = []
        for msg in thread_chat_history:
            if isinstance(msg, HumanMessage):
                role = 'user'
            else:
                role = 'assistant'
            thread_chat_history.append({'role':role,'content':msg.content})

        st.session_state['chat_messages'] = temp_chat_history
        

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
        response = st.write_stream(
            message_chunk.content[0]['text'] if message_chunk.content else ""
            for message_chunk, metadata in workflow.stream(
                {'messages':[HumanMessage(content=userinput)]},
                config=CONFIG,
                stream_mode='messages'
            )
        )

    st.session_state['chat_messages'].append({'role':'assistant', 'content':response})
