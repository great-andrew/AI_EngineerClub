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
        st.code(validation)

    return GuardrailFunctionOutput(
        output_info=validation,
        tripwire_triggered=triggered,
    )
