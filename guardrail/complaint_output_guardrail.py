import streamlit as st
from agents import (
    Agent,
    Runner,
    output_guardrail,
    RunContextWrapper,
    GuardrailFunctionOutput,
)
from models import ComplaintOutputGuardRailOutput, UserAccountContext

complaint_output_guardrail_agent = Agent(
    name="Complaints Output Guardrail",
    model="gpt-4o-mini",
    instructions="""
    Before sending your response, ensure the following:

    PROFESSIONAL & RESPECTFUL TONE:
    - Always use polite, courteous, and professional language.
    - Never use dismissive, casual, or offensive language.

    DO NOT expose internal information:
    - Direct Medical Diagnosis: Do not provide medical advice or diagnose symptoms if a guest reports illness or allergic reactions. Refer to emergency services instead.
    - Unauthorized Financial Compensation: Do not promise full refunds or high-value freebies that exceed the set digital voucher limit without manager intervention.
    - Kitchen/Recipe Secrets: Do not disclose confidential proprietary recipes or internal supplier information while explaining food quality issues.
    - Personal Staff Information: Do not disclose names, contact details, or disciplinary actions of specific kitchen or service staff involved in the complaint.

    Your response MUST ONLY include:
    - Sincere empathy and apology.
    - Identification of the issue (e.g., cold food, slow service, wrong order).
    - Standard service recovery options (e.g., re-cooking, standard discount, small complimentary item).
    - Escalation to the on-site manager for serious safety or legal incidents.
    """,
    output_type=ComplaintOutputGuardRailOutput,
)


@output_guardrail
async def complaint_output_guardrail(
    wrapper: RunContextWrapper[UserAccountContext],
    agent: Agent,
    output: str,
):
    result = await Runner.run(
        complaint_output_guardrail_agent,
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
