import streamlit as st
from agents import (
    Agent,
    Runner,
    RunContextWrapper,
    output_guardrail,
    GuardrailFunctionOutput,
)
from models import MenuOutputGuardRailOutput, UserAccountContext

menu_output_guardrail_agent = Agent(
    name="Menu Output Guardrail",
    instructions="""
Before sending your response, ensure the following:

PROFESSIONAL & RESPECTFUL TONE:
- Always use polite, courteous, and professional language.
- Never use dismissive, casual, or offensive language.

DO NOT expose internal information:
- External Ordering Links: Do not include links to third-party delivery apps not approved by the restaurant.
- Confidential Recipes: Do not disclose specific measurements or secret preparation methods for signature dishes.
- Explicit Price Negotiations: Do not offer custom discounts or price changes not listed in the menu.
- Non-Menu Recommendations: Do not recommend competitor restaurants or unrelated products.

Your response MUST ONLY include:
- Accurate dish descriptions, ingredients, pricing, and availability (sold-out status).
    """,
    output_type=MenuOutputGuardRailOutput,
)


@output_guardrail
async def menu_output_guardrail(
    wrapper: RunContextWrapper[UserAccountContext],
    agent: Agent,
    output: str,
):

    result = await Runner.run(
        menu_output_guardrail_agent,
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
