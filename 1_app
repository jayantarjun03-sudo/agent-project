import sys
import streamlit as st

class StreamlitLogger:
    def write(self, text):
        st.text(text)

    def flush(self):
        pass

sys.stdout = StreamlitLogger()

import streamlit as st
from sla_agent import AI_SLA_Agent

st.set_page_config(page_title="AI SLA Monitoring Agent", layout="wide")

st.title("🤖 AI SLA Monitoring Agent")
st.caption("Daily SLA analysis, reasoning, and escalation dashboard")

# Sidebar controls
st.sidebar.header("Controls")

action = st.sidebar.selectbox(
    "Select action",
    ["Daily Analysis", "Escalation Test", "Context Test", "Reasoning Test"]
)

run_button = st.sidebar.button("Run")

if run_button:
    agent = AI_SLA_Agent()

    with st.spinner("Running analysis..."):
        if action == "Daily Analysis":
            agent.run_daily_analysis()

        elif action == "Escalation Test":
            agent.run_specific_test("escalation")

        elif action == "Context Test":
            agent.run_specific_test("context")

        elif action == "Reasoning Test":
            agent.run_specific_test("reasoning")

    st.success("Execution complete")
