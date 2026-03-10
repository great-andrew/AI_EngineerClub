import streamlit as st
from agents import AgentHooks, RunContextWrapper


class StreamlitAgentHooks(AgentHooks):
    async def on_handoff(self, context: RunContextWrapper, agent, source):
        # handoff_msg = f"[{agent.name}로 Handoff 되었습니다.]"

        if agent.name != "Triage Agent":
            msg = f"[{agent.name}에 연결되었습니다.]"
            await st.session_state["session"].add_items(
                [{"role": "assistant", "content": [{"text": msg}], "type": "message"}]
            )

            with st.chat_message("assistant"):
                st.session_state["handoff_placeholder"].write(msg)
