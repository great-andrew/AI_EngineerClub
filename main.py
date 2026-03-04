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

            **Session Initialization (Run Once at Start):**
            - At the beginning of each session, use FileSearchTool to load ALL uploaded documents.
            - Extract and internally store: personal goals, journal entries, progress logs, and milestones.
            - Do NOT search files again during the session unless the user uploads a new document.

            **Your Core Responsibilities:**
            1. **Goal-Based Advice**: Reference the loaded goal documents directly in your responses.
            - Quote or paraphrase specific goals the user has written to make advice feel personal.
            - e.g., "업로드하신 문서에 따르면, 주 3회 운동을 목표로 하고 계시죠."
            2. **Progress Tracking**: Compare the user's current situation against their documented goals.
            - Identify what is on track, what is falling behind, and celebrate progress explicitly.
            3. **Web-Augmented Advice**: Use WebSearchTool to enrich advice with current research or techniques
            that are directly relevant to the user's specific goals.

            **Tool Usage Rules:**
            - FileSearchTool: ONCE per session at the start. Re-use only if user uploads a new file.
            - WebSearchTool: Use per question, only when external information adds value to the advice.

            **Response Format:**
            [목표 문서 검색] (첫 대화 시에만)
            또는
            [웹 검색: "{실제 검색어}"] (필요 시)

            이후 실제 문서 내용을 직접 인용하거나 참조하여 조언 제공.

            **Important Rules:**
            - Never give generic advice. Every response must be grounded in the user's actual uploaded goals.
            - If a goal is not clearly defined in the documents, ask the user to clarify or update their goal file.
            - Keep responses concise, warm, and actionable.
            - Celebrate small wins and acknowledge effort explicitly.
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
