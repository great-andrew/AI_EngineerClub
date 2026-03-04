import dotenv
import asyncio
from openai import OpenAI
import streamlit as st
from agents import Agent, Runner, SQLiteSession, WebSearchTool, FileSearchTool

dotenv.load_dotenv()

client = OpenAI()

VECTOR_STORE_ID = "vs_6981a7c619ec81919964b509d5acb388"

if "agent" not in st.session_state:
    st.session_state["agent"] = Agent(
        name="Life Coach Agent",
        instructions="""
            You are a highly professional and empathetic life coach dedicated to helping the user achieve their personal goals.
            If the user asks in Korean, you must respond in the same language.

            **Available Tools:**
            - FileSearchTool: Search the user's uploaded documents (goals, journal entries, progress logs).
            - WebSearchTool: Search the web for latest research, strategies, and expert tips.

            **Tool Usage Strategy:**

            1. FileSearchTool - Use ONLY in these cases:
            - The conversation history does not yet contain the file contents (first interaction)
            - The user explicitly refers to past records, journal entries, or progress history
            - The user uploads a new file
            ※ If the file contents already exist in the conversation history, do NOT search again.
                Always reuse the information already present in the history.

            2. WebSearchTool - Use in these cases:
            - The user's goal requires the latest research, techniques, or expert strategies
            - Specific methodologies or evidence-based tips are needed to complement the advice

            **Your Core Responsibilities:**

            1. **Goal-Based Advice**
            - Directly quote or reference the user's goals from the conversation history or uploaded documents
            - If no clear goal is found, ask the user to clarify or update their goal document

            2. **Past Record Reference**
            - When referring to journal entries or past logs, cite specific dates or contents
            - Compare past records with the current situation and explicitly highlight areas of growth
            - e.g., "Based on your records, you've increased your workout frequency compared to two weeks ago. Great progress!"

            3. **Progress Tracking**
            - Present a concrete assessment of current achievement relative to the documented goals
            - Provide balanced feedback on what is on track and what needs more attention

            **Important Rules:**
            - Every response must be grounded in the user's actual uploaded documents or conversation history
            - Generic advice is not allowed — always connect guidance to the user's specific goals
            - Keep responses concise, warm, and actionable
            - Acknowledge and celebrate even small wins explicitly
            """,
        tools=[
            WebSearchTool(),
            FileSearchTool(
                max_num_results=3,
                vector_store_ids=[VECTOR_STORE_ID],
            ),
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
        if "type" in message:
            if message["type"] == "web_search_call":
                with st.chat_message("ai"):
                    st.write("🔍 Searched the web...")
            elif message["type"] == "file_search_call":
                with st.chat_message("ai"):
                    st.write("🗂️ Searched your files...")


asyncio.run(paint_history())


def update_status(status_container, event):

    status_messages = {
        "response.web_search_call.searching": ("🔍 Starting web search...", "running"),
        "response.web_search_call.completed": ("✅ Web search completed.", "complete"),
        "response.web_search_call.in_progress": (
            "🔍 Web search in progress...",
            "running",
        ),
        "response.file_search_call.completed": (
            "✅ File search completed.",
            "complete",
        ),
        "response.file_search_call.in_progress": (
            "🗂️ Starting file search...",
            "running",
        ),
        "response.file_search_call.searching": (
            "🗂️ File search in progress...",
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


prompt = st.chat_input(
    "Write a message for your assistant.",
    accept_file=True,
    file_type=["txt"],
)

if prompt:

    for file in prompt.files:
        if file.type.startswith("text/"):
            with st.chat_message("assistant"):
                with st.status("Uploading files...") as status:
                    uploaded_file = client.files.create(
                        file=(file.name, file.getvalue()),
                        purpose="user_data",
                    )
                    status.update(label="Attaching Files...")
                    client.vector_stores.files.create(
                        vector_store_id=VECTOR_STORE_ID,
                        file_id=uploaded_file.id,
                    )
                    status.update(label="Done!", state="complete")
    if prompt.text:
        with st.chat_message("human"):
            st.write(prompt.text)
        asyncio.run(run_agent(prompt.text))


with st.sidebar:
    reset = st.button("Reset")
    if reset:
        asyncio.run(session.clear_session())
    st.write(asyncio.run(session.get_items()))
