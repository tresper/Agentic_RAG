import json
import os

import streamlit as st
import time
import requests as req
from dotenv import load_dotenv
import asyncio

load_dotenv()

if st.session_state.get("backend_host") is None:
    print(os.getenv("BACKEND_HOST"))
    backend_host = os.getenv("BACKEND_HOST", "127.0.0.1")
    st.session_state["backend_host"] = f"http://{backend_host}:8081"


# Streamed response emulator
def response_generator(response):
    for word in response.split():
        yield word + " "
        time.sleep(0.05)


def delete_index():
    resp = req.get(f"{st.session_state['backend_host']}/delete_index/")
    st.session_state["files_processed"] = None
    with spinner_container:
        st.success(resp.json()['message'])


def reset_chat():
    resp = req.get(f"{st.session_state['backend_host']}/reset_chat/")
    st.session_state.messages = []
    with spinner_container:
        st.success(resp.json()['message'])


sidebar_container = st.sidebar

# File uploader in the sidebar on the left
with sidebar_container:
    def on_submit():
        if not st.session_state.openai_api_key:
            with form_container:
                st.error("Please enter an OpenAI API key")
            return
        if not st.session_state.uploaded_files:
            with form_container:
                st.error("Please upload at least one file")
            return
        files_to_upload = [("files", (file.name, file.getvalue(), file.type)) for file in
                           st.session_state.uploaded_files]
        data = json.dumps({"openai_api_key": st.session_state.openai_api_key})
        with spinner_container:
            with st.spinner("Processing files..."):
                resp = req.post(f"{st.session_state['backend_host']}/uploadfiles/", files=files_to_upload, data={"data": data})
                resp_message = resp.json()["message"]
                if resp.status_code == 200:
                    st.success(resp_message)
                    st.session_state['files_processed'] = True
                else:
                    st.error(f"Server error occurred: {resp_message}")

    form_container = st.container()

    with st.form("my_form"):
        st.text_input("OpenAI API Key",
                      type="password",
                      key="openai_api_key",
                      disabled=st.session_state.get("files_processed") is not None)
        st.file_uploader("Please upload your files",
                         accept_multiple_files=True,
                         type=['txt', 'pdf'],
                         key="uploaded_files",
                         disabled=st.session_state.get("files_processed") is not None)
        st.form_submit_button("Submit",
                              use_container_width=True,
                              on_click=on_submit,
                              disabled=st.session_state.get("files_processed") is not None)

    spinner_container = st.container()

    st.button("Reset chat agent",
              use_container_width=True,
              on_click=reset_chat,
              disabled=st.session_state.get("files_processed") is None)
    st.button("Delete index",
              use_container_width=True,
              on_click=delete_index,
              disabled=st.session_state.get("files_processed") is None)

if st.session_state.get('files_processed') is None:
    st.header("Upload the files you would like to chat with")
else:
    st.title("Welcome to Ajua ChatBot")

    error_container = st.container()
    response_container = st.container(height=600)
    input_container = st.container()

    if st.session_state.get("messages") is None:
        st.session_state.messages = []

    with response_container:
        # Display chat messages from history on app rerun
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    with input_container:
        # Accept user input
        if prompt := st.chat_input("Your query"):
            with response_container:
                # Add user message to chat history
                st.session_state.messages.append({"role": "user", "content": prompt})
                # Display user message in chat message container
                with st.chat_message("user"):
                    st.markdown(prompt)

                # Display assistant response in chat message container
                with st.chat_message("assistant"):
                    api_res = req.post(f"{st.session_state.backend_host}/get_response",
                                       json={"query": prompt})
                    if api_res.status_code != 200:
                        error_container.error(f"Server error occurred: {api_res.json()['message']}")
                        st.stop()
                    res = api_res.json()["response"]
                    response = st.write_stream(response_generator(res.replace("\n", "  \n").replace("<br>", "  \n")))
                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": response})
