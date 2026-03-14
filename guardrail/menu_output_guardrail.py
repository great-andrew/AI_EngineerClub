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
- Daily specials and seasonal menu recommendations.
- Allergy information and dietary filtering (vegan, gluten-free, halal, etc.).
- Flavor profiles, spice levels, and ingredient details.
- Portion size guidance and pairing suggestions.
- Handoff notice when redirecting to another agent.
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
