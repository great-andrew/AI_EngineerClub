import streamlit as st
from agents import (
    Agent,
    Runner,
    RunContextWrapper,
    output_guardrail,
    GuardrailFunctionOutput,
)
from models import UserAccountContext, OrderOutputGuardRailOutput


order_output_guardrail_agent = Agent(
    name="Order Output Guardrail Agent",
    instructions="""
Before sending your response, ensure the following:

PROFESSIONAL & RESPECTFUL TONE:
- Always use polite, courteous, and professional language.
- Never use dismissive, casual, or offensive language.

DO NOT expose internal information:
- Full Payment Data: Do not display or request full credit card numbers or CVV codes in plain text.
- Order Tampering: Do not modify an already paid or "in-preparation" order without manager override.
- Personal Customer Data: Do not show previous customers' order history or addresses to the current user.
- Internal POS Commands: Do not expose raw system codes or backend database commands.

Your response MUST ONLY include:
- Order recap, final total, discount application (within limits), and estimated pickup/service time.

    """,
    output_type=OrderOutputGuardRailOutput,
)


@output_guardrail
async def order_output_guardrail(
    wrapper: RunContextWrapper[UserAccountContext],
    agent: Agent,
    output: str,
):
    result = await Runner.run(
        order_output_guardrail_agent,
        output,
        context=wrapper.context,
    )

    validation = result.final_output

    triggered = validation.is_off_topic

    with st.sidebar:
        st.code(validation)

    return GuardrailFunctionOutput(
        output_info=validation,
        tripwire_triggered=triggered,
    )
