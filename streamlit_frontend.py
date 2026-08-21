import streamlit as st
from langgraph_backend import workflow, get_all_thread_ids, get_title
from langchain_core.messages import HumanMessage, AIMessage
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
    fetched_messages = workflow.get_state(config={'configurable':{'thread_id':thread_id}}).values['messages'] if 'messages' in workflow.get_state(config={'configurable':{'thread_id':thread_id}}).values else []

    # The **IF** is for - when a new chat is created[Thread], for that thread the STATE[messages is still None. When fetched values from STATE, `messages` key doesn't exist. So send [] if empty chat instead of None ]
    return fetched_messages

#----------------------------- session setup  -----------------------------------
if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = gen_thread_id()

if 'chat_messages' not in st.session_state:
    st.session_state['chat_messages'] = []

if 'chat_thread_ids' not in st.session_state:
    st.session_state['chat_thread_ids'] = get_all_thread_ids()

add_thread_id(st.session_state['thread_id'])

CONFIG = {'configurable':{'thread_id':st.session_state['thread_id']}}
# ---------------------------- sidebar  -----------------------------------

st.sidebar.title('**ＡＫＡＩ－２.９**',width='content')

if st.sidebar.button('New Chat'):
    new_chat()

st.sidebar.header('My Chats')

for thread_id in st.session_state['chat_thread_ids'][::-1]:

    if st.sidebar.button(label=get_title(thread_id), key=thread_id):

        st.session_state['thread_id'] = thread_id
        thread_chat_history = load_thread_messages(thread_id)

        temp_chat_history = []
        for msg in thread_chat_history:
            if isinstance(msg, HumanMessage):
                role = 'user'
            else:
                role = 'assistant'
            temp_chat_history.append({'role':role,'content':msg.content if role == 'user' else msg.content[0]['text']})


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
