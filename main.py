import dotenv
import asyncio
import streamlit as st
from agents import Agent, Runner, SQLiteSession, WebSearchTool

dotenv.load_dotenv()


if "agent" not in st.session_state:
    st.session_state["agent"] = Agent(
        name="Life Coach Agent",
        instructions="""
        You are a highly professional life coach dedicated to encouraging the user. 
        If the user asks in Korean, you must respond in the same language.

        **Important**
        - You must provide new information in your answers by using the tools provided.
        - Keep your answers as concise as possible.

        **Available Tools:**
        - WebSearchTool: Use this when the user asks a question. Search for relevant information first, and then give advice to the user.
        """,
        tools=[
            WebSearchTool(),
        ],
    )

if "session" not in st.session_state:
    st.session_state["session"] = SQLiteSession("Life Coach", "./life_coach.db")

agent = st.session_state["agent"]
session = st.session_state["session"]


async def paint_history():
    messages = await session.get_items()

    for message in messages:

        if message.get("role"):
            with st.chat_message(message["role"]):
                if message["role"] == "user":
                    st.write(message["content"])
                else:
                    st.write(message["content"][0]["text"])
        elif message["type"] == "web_search_call":
            with st.chat_message("assistant"):
                st.write(f'[웹 검색: "{message["action"]["query"]}"]')


asyncio.run(paint_history())


def update_status(status_container, event):

    status_messages = {
        "response.web_search_call.searching": ("🔍 Starting web search...", "running"),
        "response.web_search_call.completed": ("✅ Web search completed.", "complete"),
        "response.web_search_call.in_progress": (
            "🔍 Web search in progress...",
            "running",
        ),
        "response.completed": ("", "complete"),
    }

    if event in status_messages:
        label, state = status_messages[event]
        status_container.update(label=label, state=state)


async def run_agent(message):

    with st.chat_message("assistant"):
        status_container = st.status("", expanded=False)
        text_placeholder = st.empty()
        response = ""
        stream = Runner.run_streamed(agent, message, session=session)

        async for event in stream.stream_events():
            if event.type == "raw_response_event":

                update_status(status_container, event.data.type)

                if event.data.type == "response.output_text.delta":
                    response += event.data.delta
                    text_placeholder.write(response)


prompt = st.chat_input("Write a message for your assistant.")

if prompt:
    with st.chat_message("human"):
        st.write(prompt)
    asyncio.run(run_agent(prompt))


with st.sidebar:
    reset = st.button("Reset")
    if reset:
        asyncio.run(session.clear_session())
    st.write(asyncio.run(session.get_items()))
