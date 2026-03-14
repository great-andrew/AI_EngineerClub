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

    triggered = (
        validation.is_off_topic or validation.is_abusive or validation.contains_pii
    )

    with st.sidebar:
        st.write(validation)

    return GuardrailFunctionOutput(
        output_info=validation,
        tripwire_triggered=triggered,
    )
