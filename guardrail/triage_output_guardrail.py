import streamlit as st
from agents import (
    Agent,
    Runner,
    RunContextWrapper,
    output_guardrail,
    GuardrailFunctionOutput,
)
from models import UserAccountContext, TriageOutputGuardRailOutput


triage_output_guardrail_agent = Agent(
    name="Triage Output Guardrail Agent",
    instructions="""
Before sending your response, ensure the following:

PROFESSIONAL & RESPECTFUL TONE:
- Always use polite, courteous, and professional language.
- Never use dismissive, casual, or offensive language.

DO NOT expose internal information:
- Premature Problem Solving: Do not attempt to solve complex complaints or orders instead of routing them.
- Bias in Routing: Do not favor or block certain requests based on non-operational criteria.
- Looping Redirects: Do not continuously send the user between agents without providing a path to a human.
- Internal System Metadata: Do not disclose the names of specific LLM models or internal routing logic.

Your response MUST ONLY include:
- Accurate intent identification and efficient redirection to the appropriate specialized agent.
    """,
    output_type=TriageOutputGuardRailOutput,
)


@output_guardrail
async def triage_output_guardrail(
    wrapper: RunContextWrapper[UserAccountContext],
    agent: Agent,
    output: str,
):
    result = await Runner.run(
        triage_output_guardrail_agent,
        output,
        context=wrapper.context,
    )

    validation = result.final_output

    triggered = validation.is_off_topic

    with st.sidebar:
        status_color = "#ff4757" if triggered else "#7bed9f"
        status_text = "🚫 BLOCKED" if triggered else "✅ PASSED"

        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, #1e1e2e, #2a2a3e);
                border-left: 3px solid {status_color};
                border-radius: 8px;
                padding: 1rem 1.2rem;
                margin-bottom: 1rem;
                font-size: 0.85rem;
            ">
                <div style="color: {status_color}; font-weight: 700; font-size: 0.75rem;
                             letter-spacing: 0.05em; margin-bottom: 0.6rem;">
                    🛡️ OUTPUT GUARDRAIL {status_text}
                </div>
                <div style="color: #8888a0; font-size: 0.8rem; line-height: 1.6;">
                    <span style="color: #ffa502;">Off-topic</span> · {validation.is_off_topic}<br>
                    <span style="color: #e0e0e8;">Reason</span> · {validation.reason}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    return GuardrailFunctionOutput(
        output_info=validation,
        tripwire_triggered=triggered,
    )
