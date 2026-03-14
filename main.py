import dotenv

dotenv.load_dotenv()
from openai import OpenAI
import asyncio
import streamlit as st
from agents import (
    Runner,
    SQLiteSession,
    InputGuardrailTripwireTriggered,
    OutputGuardrailTripwireTriggered,
    GuardrailFunctionOutput,
)
from models import UserAccountContext
from my_agents.triage_agent import (
    triage_agent,
    off_topic_guardrail,
    input_guardrail_agent,
)

client = OpenAI()

user_account_ctx = UserAccountContext(
    customer_id=1,
    name="andrew",
)


if "session" not in st.session_state:
    st.session_state["session"] = SQLiteSession(
        "chat-history",
        "customer-support-memory.db",
    )
session = st.session_state["session"]

if "agent" not in st.session_state:
    st.session_state["agent"] = triage_agent


async def paint_history():
    messages = await session.get_items()
    for message in messages:
        if "role" in message:
            with st.chat_message(message["role"]):
                if message["role"] == "user":
                    st.write(message["content"])
                else:
                    if message.get("type") and message["type"] == "message":
                        st.write(message["content"][0]["text"].replace("$", "\$"))


asyncio.run(paint_history())


async def run_agent(message):

    with st.chat_message("ai"):
        text_placeholder = st.empty()
        response = ""

        st.session_state["text_placeholder"] = text_placeholder

        try:
            guardrail_result = await Runner.run(
                input_guardrail_agent,
                message,
                context=user_account_ctx,
            )
            validation = guardrail_result.final_output
            triggered = (
                validation.is_off_topic
                or validation.is_abusive
                or validation.contains_pii
            )
            if triggered:
                st.write(
                    "저는 레스토랑 관련 질문에 대해서만 도와드리고 있어요. 메뉴를 확인하거나, 예약하거나, 음식을 주문할 수 있어요."
                )
                text_placeholder = st.empty()
                st.session_state["text_placeholder"] = text_placeholder
                response = ""
                await session.add_items(
                    [
                        {
                            "role": "user",
                            "content": message,
                        },
                        {
                            "role": "assistant",
                            "type": "message",
                            "content": [
                                {
                                    "type": "output_text",
                                    "text": "저는 레스토랑 관련 질문에 대해서만 도와드리고 있어요. 메뉴를 확인하거나, 예약하거나, 음식을 주문할 수 있어요.",
                                }
                            ],
                        },
                    ]
                )
                return
            stream = Runner.run_streamed(
                st.session_state["agent"],
                message,
                session=session,
                context=user_account_ctx,
            )

            async for event in stream.stream_events():
                if event.type == "raw_response_event":

                    if event.data.type == "response.output_text.delta":
                        response += event.data.delta
                        text_placeholder.write(response.replace("$", "\$"))
                elif event.type == "agent_updated_stream_event":

                    if st.session_state["agent"].name != event.new_agent.name:

                        st.write(f"[{event.new_agent.name}에 연결되었습니다.]")

                        st.session_state["agent"] = event.new_agent

                        text_placeholder = st.empty()

                        st.session_state["text_placeholder"] = text_placeholder
                        response = ""

        except InputGuardrailTripwireTriggered:
            st.write("[InputGuardrail 작동!]")
            st.write(
                "저는 레스토랑 관련 질문에 대해서만 도와드리고 있어요. 메뉴를 확인하거나, 예약하거나, 음식을 주문할 수 있어요."
            )
            text_placeholder = st.empty()

            st.session_state["text_placeholder"] = text_placeholder
            response = ""

        except OutputGuardrailTripwireTriggered:
            st.write("[OutputGuardrail 작동!]")
            st.write(
                "저는 레스토랑 관련 질문에 대해서만 도와드리고 있어요. 메뉴를 확인하거나, 예약하거나, 음식을 주문할 수 있어요."
            )


message = st.chat_input(
    "Write a message for your assistant",
)

if message:

    if "text_placeholder" in st.session_state:
        st.session_state["text_placeholder"].empty()

    if message:
        with st.chat_message("human"):
            st.write(message)
        asyncio.run(run_agent(message))


with st.sidebar:

    reset = st.button("Reset memory")
    if reset:
        asyncio.run(session.clear_session())
    st.write(asyncio.run(session.get_items()))
