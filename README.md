# Vaakku - AI Revenue Recovery Agent

"Vaakku" means "promise" in Tamil. It is an AI-powered revenue-recovery agent that detects revenue at risk (abandoned checkouts, failed subscription payments, overdue invoices), diagnoses why, decides a bounded intervention, executes it, and tracks the outcome — while remembering each customer's payment-promise history so it treats repeat offenders differently from reliable customers.

## Pipeline Stages

1.  **Generate Dataset:** Generates synthetic events and customer memory.
2.  **Diagnose:** Uses Claude API to determine why the failure happened.
3.  **Decide:** Rule-based logic to select the appropriate action based on diagnosis and customer history.
4.  **Execute:** Claude drafts a message; a test Razorpay payment link is generated.
5.  **Log + Stopping Rules:** All actions are written to a SQLite audit log. Stops runaway interventions.
6.  **Update Memory:** Updates customer history for future decisions.
7.  **Dashboard:** Streamlit app to view recovery metrics.

## Setup Instructions

1.  Clone this repository.
2.  Install dependencies: `pip install -r requirements.txt`
3.  Copy `.env.example` to `.env` and fill in your test API keys.
4.  Run the pipeline: `python main.py`
5.  View the dashboard: `streamlit run dashboard/app.py`

## Hackathon Note
Built for the Razorpay AI Buildathon.

Track 3: AI Revenue Recovery
