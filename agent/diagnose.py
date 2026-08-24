import os
import json
import anthropic
from dotenv import load_dotenv

load_dotenv()

# Initialize Anthropic client
api_key = os.environ.get("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=api_key) if api_key and api_key != "your_anthropic_api_key_here" else None

def diagnose_event(event_record, customer_memory):
    """
    Diagnoses the reason for the revenue-at-risk event and recommends an urgency level.
    Returns a dictionary: {diagnosis, confidence, recommended_urgency}
    """
    
    # MOCK LOGIC FOR DEMO VIDEO (if no API key provided)
    if not client:
        failure_reason = event_record.get('failure_reason')
        event_type = event_record.get('event_type')
        broken_promises = int(customer_memory.get('promises_broken', 0))
        
        if failure_reason == "insufficient funds":
            diag = f"Customer likely experienced a temporary cash flow issue causing the {event_type.replace('_', ' ')}."
            urgency = "low" if broken_promises == 0 else "medium"
        elif failure_reason == "card expired":
            diag = "Customer's payment method has expired and needs to be updated."
            urgency = "medium"
        elif failure_reason == "forgot to pay":
            diag = "Customer simply forgot. A gentle nudge is usually highly effective here."
            urgency = "low"
        elif failure_reason == "disputed amount":
            diag = "Customer is disputing the charge; requires careful handling to prevent churn."
            urgency = "high"
        else:
            diag = f"Unexpected failure during {event_type.replace('_', ' ')}. System anomaly or silent drop-off."
            urgency = "medium" if broken_promises < 2 else "high"
            
        return {
            "diagnosis": diag,
            "confidence": 0.85,
            "recommended_urgency": urgency
        }

    # REAL CLAUDE LOGIC
    system_prompt = """You are Vaakku, an AI-powered revenue-recovery diagnostic agent. 
Your goal is to analyze a revenue-at-risk event (e.g., checkout abandoned, subscription failed, invoice overdue) 
and the customer's historical memory, and provide a diagnosis.

You MUST respond with a valid JSON object containing EXACTLY these keys:
- "diagnosis": A short string explaining why you think the event happened.
- "confidence": A float between 0.0 and 1.0 indicating your confidence in the diagnosis.
- "recommended_urgency": A string, one of ["low", "medium", "high"].

Do not include any other text before or after the JSON.
"""

    user_prompt = f"""
Event Details:
- Event ID: {event_record.get('event_id')}
- Type: {event_record.get('event_type')}
- Amount: {event_record.get('amount')}
- Status: {event_record.get('status')}
- Days Since Event: {event_record.get('days_since_event')}
- Known Failure Reason: {event_record.get('failure_reason')}

Customer History:
- Customer ID: {customer_memory.get('customer_id')}
- Promises Made: {customer_memory.get('promises_made')}
- Promises Kept: {customer_memory.get('promises_kept')}
- Promises Broken: {customer_memory.get('promises_broken')}
- Last Action Taken: {customer_memory.get('last_action_taken')}
"""

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=256,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0
        )
        
        response_text = response.content[0].text
        
        # In case the model returns markdown JSON blocks
        if response_text.startswith("```json"):
            response_text = response_text.strip("```json").strip("```").strip()
            
        result = json.loads(response_text)
        
        # Ensure default keys if missing
        if "diagnosis" not in result:
            result["diagnosis"] = "Unknown"
        if "confidence" not in result:
            result["confidence"] = 0.5
        if "recommended_urgency" not in result:
            result["recommended_urgency"] = "medium"
            
        return result
        
    except Exception as e:
        print(f"Error during diagnosis for event {event_record.get('event_id')}: {e}")
        return {
            "diagnosis": "Error calling diagnostic API",
            "confidence": 0.0,
            "recommended_urgency": "high" # default to high urgency if we can't diagnose
        }
