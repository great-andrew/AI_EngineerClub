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
- Allergy confirmation for ordered items.
- Coupon and loyalty point application details.
- Order modification or cancellation guidance.
- Menu item suggestions relevant to the current order.
- Handoff notice when redirecting to another agent.
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
