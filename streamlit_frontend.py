import streamlit as st
from langgraph_backend import workflow
from langchain_core.messages import HumanMessage, AIMessage

CONFIG = {'configurable':{'thread_id':'thread-002'}}

if 'chat_messages' not in st.session_state:
    st.session_state['chat_messages'] = []

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
