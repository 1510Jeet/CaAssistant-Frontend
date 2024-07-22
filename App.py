import streamlit as st
import requests
from gtts import gTTS
from io import BytesIO
from streamlit_mic_recorder import speech_to_text
import json
from streamlit.runtime.scriptrunner import get_script_run_ctx
session_id = get_script_run_ctx().session_id
import speech_recognition as sr


# Initialize recognizer class                                       
r = sr.Recognizer()


if "chat_uids" not in st.session_state:


    #chat_uids is a list of active chat_ids
    st.session_state.chat_uids = []

    #messages is a dictionary structure storing list of messages with chat_uid as the key
    st.session_state.messages = {}

    # curr_uid is the current chat_uid 
    st.session_state.curr_uid = 1

    #total_ids -> total ids generated, as we add new chat total_id is incremented,
    # used to assign unique chat_uid 
    st.session_state.total_ids=1

def delete_chat(id):
    # to delete a chat from backend
    delete_chat_url = "http://127.0.0.1:8000/deleteChat/"
    data = {
        "session_id": session_id+str(id)
    }
    response = requests.post(delete_chat_url, json=data)

    if response.status_code == 200:
        st.success("New chat ")
    else:
        pass

    # to delete the chats in the front-end ie streamlit 
    if id in st.session_state.messages:
        del st.session_state.messages[id]

    # to delete the chat_uid of the chat from chat_uids list.
    if id in st.session_state.chat_uids:
        st.session_state.chat_uids.remove(id)

    # to update the screen once the chat is deleted
    st.rerun()

# text to voice function using gTTS library
def text_to_speech_and_display(text):
    tts = gTTS(text=text, lang='en')
    audio_fp = BytesIO()
    tts.write_to_fp(audio_fp)
    audio_fp.seek(0)
    st.audio(audio_fp, format="audio/mp3")


def display_chat():
    
    # getting the messages only from the current chat id.
    msg=st.session_state.messages.get(st.session_state.curr_uid, [])

    # displaying the messages in latest to oldest message order
    for i in range(len(msg)-1,-1,-1):
        if msg[i]["content"] != "":
            if msg[i]["role"]=="assistant":
                with st.chat_message(msg[i-1]["role"]):
                    st.markdown(msg[i-1]["content"])
                with st.chat_message(msg[i]["role"]):
                    #displaying audio of the result
                    st.markdown(msg[i]["content"])
                    text_to_speech_and_display(msg[i]["content"])


#Side Bar
st.sidebar.title("")
if st.sidebar.button("New Chat ➕"):
    # to increment total ids
    st.session_state.total_ids += 1

    #initialising the current chat id 
    st.session_state.curr_uid=st.session_state.total_ids


# To display the recent chats with their first user message and delete btn.
for i in reversed(st.session_state.chat_uids):
    with st.sidebar.container():
        col1, col2 = st.columns([4, 1])

    # to get the first user prompt from the chat
    firstQuestion=st.session_state.messages.get(i,[])[0]["content"]

    #to limit the character limit of the chat title to 15 characters only.
    if len(firstQuestion)>15:
        firstQuestion=firstQuestion[0:15]+".."

    # every button is recognised by the chat id and their column no.
    #Chat Button
    if (col1.button(firstQuestion,key=str(i)+"c1")):
        st.session_state.curr_uid=i

    #Delete chat Button
    if col2.button("🗑",key=str(i)+"c2"):
        delete_chat(i)



st.title("CA Assistant")



# Calling the caBuddy endpoint of API to get LLM response by session_id + current chat
# using session_id + current chat id to keep each chat unique
def llm_call(prompt):
    url = "http://127.0.0.1:8000/caBuddy/"
    request_params = {
        "message": prompt,
        "session_id": session_id+str(st.session_state.curr_uid)
    }
    response = requests.post(url=url, json=request_params)
    return response

#initialising transcribed_text string
transcribed_text=""

# Layout for text input and microphone
text_input_col, mic_col = st.columns([4, 1])  # Adjust proportions as needed

# voice input column
with mic_col:
    # to take speech input and transcribe it using speech recognition library
    text = speech_to_text(language='en', just_once=True, key='STT',start_prompt="🎙️", stop_prompt="🎙️")
    transcribed_text=text

#text input column
with text_input_col:
    prompt = st.chat_input("Ask your CA Buddy")


if prompt:
    #Initialising a new chat
    if st.session_state.curr_uid not in st.session_state.messages:
        st.session_state.messages[st.session_state.curr_uid] = []
        st.session_state.chat_uids.append(st.session_state.curr_uid)

    # appeding user messages
    st.session_state.messages[st.session_state.curr_uid].append({"role": "user", "content": prompt})
    
    #using llm_call function to get response to user prompt
    response = llm_call(prompt)

    # if response status code is 200 then it's succesful else it's an error
    if response.status_code == 200:
        st.session_state.messages[st.session_state.curr_uid].append({"role": "assistant", "content": response.text})
    else:
        st.write("Error:", response)


if transcribed_text:
    #Initialising a new chat
    if st.session_state.curr_uid not in st.session_state.messages:
        st.session_state.messages[st.session_state.curr_uid] = []
        st.session_state.chat_uids.append(st.session_state.curr_uid)

    # appending user messages
    st.session_state.messages[st.session_state.curr_uid].append({"role": "user", "content": transcribed_text})
  
    #using llm_call function to get response to user prompt
 
    response = llm_call(transcribed_text)
    transcribed_text = ""

    # if response status code is 200 then it's succesful else it's an error
    if response.status_code == 200:
        st.session_state.messages[st.session_state.curr_uid].append({"role": "assistant", "content": response.text})
    else:
        st.write("Error:", response)

# to display chats
display_chat()

