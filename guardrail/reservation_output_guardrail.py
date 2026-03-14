import streamlit as st
from agents import (
    Agent,
    Runner,
    RunContextWrapper,
    output_guardrail,
    GuardrailFunctionOutput,
)
from models import UserAccountContext, ReservationOutputGuardRailOutput


reservation_output_guardrail_agent = Agent(
    name="Reservation Output Guardrail Agent",
    instructions="""
    Before sending your response, ensure the following:

    PROFESSIONAL & RESPECTFUL TONE:
    - Always use polite, courteous, and professional language.
    - Never use dismissive, casual, or offensive language.

    DO NOT expose internal information:
    - Overbooking Promises: Do not guarantee a seat when the system shows "Fully Booked."
    - Other Guests' Info: Do not disclose names, phone numbers, or special requests of other reserved guests.
    - Unauthorized VIP Access: Do not grant VIP status or restricted seating (e.g., Private Rooms) without proper credentials.
    - Real-time Floor Map: Do not export the full internal table layout or staff-only zoning information.

    Your response MUST ONLY include:
    - Booking availability, confirmation of guest details, and basic facility info (parking, high chairs).
    - Reservation modification and cancellation process.
    - Cancellation and no-show policy information.
    - Waitlist options and alternative time suggestions.
    - Special request confirmation (seating preferences, celebrations, accessibility needs).
    - Handoff notice when redirecting to another agent.
    """,
    output_type=ReservationOutputGuardRailOutput,
)


@output_guardrail
async def reservation_output_guardrail(
    wrapper: RunContextWrapper[UserAccountContext],
    agent: Agent,
    output: str,
):
    result = await Runner.run(
        reservation_output_guardrail_agent,
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
