# my_agents/__init__.py

from my_agents.complaints_agent import complaint_agent
from my_agents.reservation_agent import reservation_agent
from my_agents.menu_agent import menu_agent
from my_agents.order_agent import order_agent
from my_agents.triage_agent import triage_agent, make_handoff

# 하위 에이전트 간 handoffs (모두 make_handoff 사용)
complaint_agent.handoffs = [make_handoff(order_agent), make_handoff(reservation_agent)]
reservation_agent.handoffs = [
    make_handoff(order_agent),
    make_handoff(menu_agent),
    make_handoff(complaint_agent),
]
menu_agent.handoffs = [
    make_handoff(order_agent),
    make_handoff(reservation_agent),
    make_handoff(complaint_agent),
]
order_agent.handoffs = [
    make_handoff(menu_agent),
    make_handoff(reservation_agent),
    make_handoff(complaint_agent),
]

# triage_agent
triage_agent.handoffs = [
    make_handoff(order_agent),
    make_handoff(menu_agent),
    make_handoff(complaint_agent),
    make_handoff(reservation_agent),
]
