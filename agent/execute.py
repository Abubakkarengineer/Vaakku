import os
import razorpay
import anthropic
from dotenv import load_dotenv

load_dotenv()

# Initialize Anthropic and Razorpay clients
api_key = os.environ.get("ANTHROPIC_API_KEY")
anthropic_client = anthropic.Anthropic(api_key=api_key) if api_key and api_key != "your_anthropic_api_key_here" else None

RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET")

if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET and RAZORPAY_KEY_ID != "your_razorpay_test_key_id_here":
    rzp_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
else:
    rzp_client = None

def generate_payment_link(amount, event_type, customer_id):
    """
    Calls Razorpay API to generate a test-mode payment link.
    """
    if not rzp_client:
        return "https://test.razorpay.com/pl_fallback"

    try:
        # amount must be in the smallest currency unit (e.g., paise for INR)
        # assuming amount is in INR for this test
        amount_in_paise = int(float(amount) * 100)
        
        # apply minimum amount requirement for Razorpay (must be at least 1 INR)
        if amount_in_paise < 100:
            amount_in_paise = 100

        data = {
            "amount": amount_in_paise,
            "currency": "INR",
            "accept_partial": False,
            "description": f"Recovery for {event_type}",
            "customer": {
                "name": customer_id,
                "email": f"{customer_id.lower()}@example.com",
            },
            "notify": {
                "sms": False,
                "email": False
            },
            "reminder_enable": False,
            "expire_by": 0 # no expiry for test
        }
        
        payment_link = rzp_client.payment_link.create(data)
        return payment_link.get('short_url', "https://test.razorpay.com/pl_unknown")
    except Exception as e:
        print(f"Razorpay API error: {e}")
        return "https://test.razorpay.com/pl_error_fallback"

def draft_message(action, diagnosis_result, event_record, payment_link):
    """
    Uses Claude to draft a customer message whose tone matches the decided action and urgency.
    """
    if action == "escalate_human":
        return "[Internal Note] Escalated to human agent. No automated message sent."
    elif action == "no_action":
        return "[Internal Note] No action required."

    if not anthropic_client:
        if action == "soft_reminder":
            return f"Hi there! It looks like there was an issue with your recent payment of ${event_record.get('amount')}. You can securely complete your payment here: {payment_link}"
        elif action == "firm_reminder":
            return f"Action Required: Your payment of ${event_record.get('amount')} is past due. To prevent service interruption, please complete your payment immediately using this link: {payment_link}"
        elif action == "discount_nudge":
            return f"Good news! We're offering a special discount to help you complete your transaction. You can pay the reduced amount here: {payment_link}"

    system_prompt = """You are Vaakku, a revenue-recovery agent. 
Draft a short, polite but appropriately-toned message to the customer about their outstanding balance.
- If the action is 'soft_reminder', be very gentle and helpful.
- If the action is 'firm_reminder', be direct and clear about the consequences.
- If the action is 'discount_nudge', highlight that a discount is available if they pay now.

Keep the message under 3 sentences. You must include the provided Payment Link in the message."""

    user_prompt = f"""
Action to take: {action}
Event Type: {event_record.get('event_type')}
Amount Owed: ${event_record.get('amount')}
Diagnosis: {diagnosis_result.get('diagnosis')}
Urgency: {diagnosis_result.get('recommended_urgency')}
Payment Link: {payment_link}
"""

    try:
        response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=150,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        return response.content[0].text.strip()
    except Exception as e:
        print(f"Error drafting message with Claude: {e}")
        return f"Please pay your outstanding balance of ${event_record.get('amount')} here: {payment_link}"

def execute_intervention(action, event_record, diagnosis_result):
    """
    Orchestrates the execution stage: creating a payment link and drafting the message.
    """
    payment_link = None
    message = None
    
    if action not in ["escalate_human", "no_action"]:
        # We might offer a discount if the action is 'discount_nudge'
        amount = float(event_record.get('amount', 0))
        if action == "discount_nudge":
            amount = amount * 0.90 # 10% discount
            
        payment_link = generate_payment_link(amount, event_record.get('event_type'), event_record.get('customer_id'))
        
    message = draft_message(action, diagnosis_result, event_record, payment_link)
    
    return {
        "action_taken": action,
        "payment_link": payment_link,
        "drafted_message": message
    }
