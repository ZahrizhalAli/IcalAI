import assemblyai as aai
from elevenlabs import play
from dotenv import load_dotenv
import elevenlabs
import os
from elevenlabs import stream
from elevenlabs.client import ElevenLabs
from openai import OpenAI
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import HumanMessage
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

load_dotenv()

from langchain_openai import ChatOpenAI

model = ChatOpenAI(
    model="gpt-4o",
    streaming=True,
    # callbacks=[StreamingStdOutCallbackHandler()]
)

store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

with_message_history = RunnableWithMessageHistory(model, get_session_history)

# create a config that we pass into the runnable every time. This config contains information that is not part of the input directly, but is still useful.
config = {"configurable": {"session_id": "124"}} # change session_id will refresh the memory

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are Ical. You are very tough and rude. Begin by introducing yourself"""
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

chain = prompt | model

with_message_history = RunnableWithMessageHistory(chain, get_session_history)

response = with_message_history.invoke(
    [HumanMessage(content="hello!")],
    config=config,
)

print(response.content)
# client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))
#
# audio = client.generate(
#   text=response.content,
#   voice="NMAZvPhCudGzyCDh9Ku4",
#   model="eleven_multilingual_v2"
# )

# play(audio)

while True:
    input_message = input("You: ")

    # response = with_message_history.invoke(
    #     [HumanMessage(content=input_message)],
    #     config=config,
    # )
    # print(response.content)
    messages = ""
    print("Ical AI: ")
    for msg in with_message_history.stream(
            [HumanMessage(content=input_message)],
            config=config,
    ):
        print(msg.content, end="")
        messages += msg.content


    # audio = client.generate(
    #     text=messages,
    #     voice="NMAZvPhCudGzyCDh9Ku4",
    #     model="eleven_multilingual_v2"
    # )
    #
    # play(audio)
    print("\n")