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
    - Refund policy information and general refund process guidance.
    - Payment dispute acknowledgment and next steps.
    - Compensation options within policy limits (e.g., digital vouchers, partial refunds).
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
