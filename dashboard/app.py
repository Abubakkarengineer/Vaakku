import streamlit as st
import pandas as pd
import sqlite3
import os

st.set_page_config(page_title="Vaakku Dashboard", layout="wide")

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "audit", "audit_log.db")
EVENTS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "events.csv")
MEMORY_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "customer_memory.csv")

@st.cache_data
def load_data():
    if not os.path.exists(DB_PATH) or not os.path.exists(EVENTS_FILE):
        return None, None, None
        
    conn = sqlite3.connect(DB_PATH)
    audit_df = pd.read_sql_query("SELECT * FROM audit_log", conn)
    conn.close()
    
    events_df = pd.read_csv(EVENTS_FILE)
    memory_df = pd.read_csv(MEMORY_FILE)
    
    return audit_df, events_df, memory_df

audit_df, events_df, memory_df = load_data()

st.title("Vaakku: Revenue Recovery Dashboard")

if audit_df is None or events_df is None:
    st.warning("Data not found. Please run the pipeline (`python main.py`) first.")
    st.stop()

# --- 1. Top Level Metrics ---
total_at_risk = events_df['amount'].sum()
recovered_events = events_df[events_df['status'] == 'recovered']
total_recovered = recovered_events['amount'].sum()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Revenue at Risk", f"${total_at_risk:,.2f}")
with col2:
    st.metric("Total Recovered", f"${total_recovered:,.2f}")
with col3:
    recovery_pct = (total_recovered / total_at_risk * 100) if total_at_risk > 0 else 0
    st.metric("Overall Recovery Rate", f"{recovery_pct:.1f}%")

st.divider()

# --- 2. Recovery Rate by Customer History ---
st.subheader("Recovery Rate by Customer Profile")

# Merge events with memory to determine history state at the END of the run
# To be accurate about their history state AT THE TIME OF RECOVERY, we can use the audit log.
# For simplicity, we classify customers based on their history in memory_df.
clean_customers = memory_df[memory_df['promises_broken'] == 0]['customer_id'].tolist()

clean_events = events_df[events_df['customer_id'].isin(clean_customers)]
broken_events = events_df[~events_df['customer_id'].isin(clean_customers)]

def calc_rate(df_subset):
    if len(df_subset) == 0: return 0, 0
    total = df_subset['amount'].sum()
    rec = df_subset[df_subset['status'] == 'recovered']['amount'].sum()
    return (rec / total * 100) if total > 0 else 0, total

clean_rate, clean_total = calc_rate(clean_events)
broken_rate, broken_total = calc_rate(broken_events)

col4, col5 = st.columns(2)
with col4:
    st.metric("Clean History Customers Recovery Rate", f"{clean_rate:.1f}%", help=f"Out of ${clean_total:,.2f} at risk")
with col5:
    st.metric("Broken Promise Customers Recovery Rate", f"{broken_rate:.1f}%", help=f"Out of ${broken_total:,.2f} at risk")

st.divider()

# --- 3. False Escalation Count ---
# False escalation = Action is 'escalate_human' BUT customer had 0 broken promises.
# We'll use the reasoning from audit log to check if it was due to hard limits or just bad logic.
st.subheader("Exceptions & Escalations")

escalations = audit_df[audit_df['action'] == 'escalate_human']
# A false escalation is if they were escalated but only had clean history. We can infer this by looking at reasoning or memory.
false_escalations = escalations[escalations['reasoning'].str.contains("Clean history", case=False, na=False) | 
                               (escalations['reasoning'].str.contains("Discount already offered", case=False, na=False))]

col6, col7 = st.columns(2)
with col6:
    st.metric("Total Human Escalations", len(escalations))
with col7:
    st.metric("False/Limit-forced Escalations", len(false_escalations), help="Escalations triggered on clean-history customers due to rules (like max discount limit).")

# --- 4. Final Exception List ---
st.write("### Final Exception List (Escalated Events)")
if len(escalations) > 0:
    exception_list = escalations[['event_id', 'customer_id', 'action', 'reasoning', 'timestamp']].drop_duplicates(subset=['event_id'], keep='last')
    st.dataframe(exception_list, use_container_width=True)
else:
    st.write("No escalations recorded.")

st.divider()

st.write("### Recent Audit Log Activity")
st.dataframe(audit_df.sort_values(by='timestamp', ascending=False).head(20), use_container_width=True)
