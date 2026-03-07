import dotenv
import asyncio
from openai import OpenAI
import streamlit as st
from agents import (
    Agent,
    Runner,
    SQLiteSession,
    WebSearchTool,
    FileSearchTool,
    ImageGenerationTool,
)
import base64

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
            - WebSearchTool: Search the web for latest research, motivational content, strategies, and expert tips.
            - ImageGenerationTool: Generate motivational images, vision boards, and progress visuals tailored to the user's goals.

            **Tool Usage Strategy:**

            1. FileSearchTool - Use ONLY in these cases:
            - The conversation history does not yet contain the file contents (first interaction)
            - The user explicitly refers to past records, journal entries, or progress history
            - The user uploads a new file
            ※ If the file contents already exist in the conversation history, do NOT search again.
                Always reuse the information already present in the history.

            2. WebSearchTool - Use in these cases:
            - The user's goal requires the latest research, techniques, or expert strategies
            - Motivational content, quotes, or evidence-based tips are needed to complement the advice

            3. ImageGenerationTool - Use in these cases:
            - The user requests a vision board based on their documented goals
            - The user asks for a motivational poster with a personalized message
            - A visual representation of the user's progress would enhance encouragement
            - Proactively suggest image generation when it would meaningfully boost motivation
            ※ Always base the image prompt on the user's actual goals and records from FileSearchTool or conversation history.
                Never generate generic motivational images — make them specific to the user's journey.

            **Image Generation Guidelines:**
            - Vision Board: Incorporate the user's specific goals, milestones, and aspirations into the visual
            - Motivational Poster: Include a personalized message that directly references the user's progress or goals
            - Progress Visual: Reflect the user's actual achievements compared to their documented targets
            - Style: Warm, inspiring, and visually clear — avoid cluttered or overly complex compositions

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

            4. **Visual Motivation**
            - Proactively offer to generate a vision board or motivational poster at meaningful moments
                (e.g., when the user reaches a milestone, feels discouraged, or sets a new goal)
            - Ensure every generated image feels personal and directly tied to the user's unique journey

            **Tool Collaboration Flow:**
            When all three tools work together, follow this natural sequence:
            1. FileSearchTool → Retrieve the user's goals and past records
            2. WebSearchTool → Find relevant advice or motivational content aligned with those goals
            3. ImageGenerationTool → Create a personalized visual that reinforces the advice and celebrates progress

            **Important Rules:**
            - Every response must be grounded in the user's actual uploaded documents or conversation history
            - Generic advice is not allowed — always connect guidance to the user's specific goals
            - All generated images must reflect the user's personal goals, not generic themes
            - Keep responses concise, warm, and actionable
            - Acknowledge and celebrate even small wins explicitly
            """,
        tools=[
            WebSearchTool(),
            FileSearchTool(
                max_num_results=3,
                vector_store_ids=[VECTOR_STORE_ID],
            ),
            ImageGenerationTool(
                tool_config={
                    "type": "image_generation",
                    "moderation": "low",
                    "quality": "high",
                    "partial_images": 1,
                }
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
                    content = message["content"]
                    if isinstance(content, str):
                        st.write(content)
                    elif isinstance(content, list):
                        for part in content:
                            if "image_url" in part:
                                st.image(part["image_url"])
                else:
                    st.write(message["content"][0]["text"].replace("$", "\$"))
        if "type" in message:
            if message["type"] == "web_search_call":
                with st.chat_message("ai"):
                    st.write("🔍 Searched the web...")
            elif message["type"] == "file_search_call":
                with st.chat_message("ai"):
                    st.write("🗂️ Searched your files...")
            elif message["type"] == "image_generation_call":
                with st.chat_message("ai"):
                    image = base64.b64decode(message["result"])
                    st.image(image)


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
        "response.image_generation_call.generating": (
            "🎨 Image Generation in progress...",
            "running",
        ),
        "response.image_generation_call.in_progress": (
            "🎨 Image Generation in progress...",
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
        image_placeholder = st.empty()
        text_placeholder = st.empty()
        response = ""

        st.session_state["image_placeholder"] = image_placeholder
        st.session_state["text_placeholder"] = text_placeholder

        stream = Runner.run_streamed(agent, message, session=session)

        async for event in stream.stream_events():
            if event.type == "raw_response_event":

                update_status(status_container, event.data.type)

                if event.data.type == "response.output_text.delta":
                    response += event.data.delta
                    text_placeholder.write(response)
                elif event.data.type == "response.image_generation_call.partial_image":
                    image = base64.b64decode(event.data.partial_image_b64)
                    image_placeholder.image(image)


prompt = st.chat_input(
    "Write a message for your assistant.",
    accept_file=True,
    file_type=["txt", "jpg", "gif", "png", "jpeg"],
)

if prompt:

    if "image_placeholder" in st.session_state:
        st.session_state["image_placeholder"].empty()
    if "text_placeholder" in st.session_state:
        st.session_state["text_placeholder"].empty()

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
        elif file.type.startswith("image/"):
            with st.status("Uploading image...") as status:
                file_bytes = file.getvalue()
                base64_data = base64.b64encode(file_bytes).decode("utf-8")
                data_uri = f"data:{file.type};base64,{base64_data}"
                asyncio.run(
                    session.add_items(
                        [
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "input_image",
                                        "detail": "auto",
                                        "image_url": data_uri,
                                    }
                                ],
                            }
                        ]
                    )
                )
            status.update(label="Done!", state="complete")
            with st.chat_message("user"):
                st.image(data_uri)

    if prompt.text:
        items = asyncio.run(session.get_items())
        clean_items = [item for item in items if "action" not in item]

        asyncio.run(session.clear_session())
        asyncio.run(session.add_items(clean_items))
        with st.chat_message("human"):
            st.write(prompt.text)
        asyncio.run(run_agent(prompt.text))


with st.sidebar:
    reset = st.button("Reset")
    if reset:
        asyncio.run(session.clear_session())
    st.write(asyncio.run(session.get_items()))
