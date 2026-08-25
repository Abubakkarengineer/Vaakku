def decide_action(event_record, customer_memory, diagnosis_result, follow_up_count=0):
    """
    Pure rule-based function to decide the next action.
    This must NOT contain any LLM calls to ensure explainability and auditability.
    
    Valid actions: ["soft_reminder", "firm_reminder", "discount_nudge", "escalate_human", "no_action"]
    """
    
    # 1. Enforce hard stopping rules first
    if follow_up_count >= 3:
        return "escalate_human", "Hard limit reached: Max 3 follow-ups."
        
    has_had_discount = customer_memory.get('has_had_discount', False) # passed from main via memory/logger
        
    if event_record.get('status') != 'open':
        return "no_action", f"Event is already {event_record.get('status')}."
        
    amount = float(event_record.get('amount', 0.0))
    if amount <= 0:
        return "no_action", "Amount is zero or negative."

    # Extract customer history
    broken_promises = int(customer_memory.get('promises_broken', 0))
    days_since = int(event_record.get('days_since_event', 0))
    failure_reason = event_record.get('failure_reason')

    # 2. Decision Logic based on History
    if broken_promises >= 2:
        return "escalate_human", f"Customer has {broken_promises} broken promises (2+ limit reached)."
        
    if broken_promises == 1:
        # If they already have a broken promise, we don't offer discounts, we are firm
        return "firm_reminder", "Customer has 1 broken promise; applying firm reminder."
        
    # 3. Clean history (0 broken promises)
    # Consider offering a discount if it's been a while or they had insufficient funds
    if (days_since > 7 or failure_reason == "insufficient funds") and not has_had_discount:
        return "discount_nudge", "Clean history, but overdue > 7 days or insufficient funds; nudging with discount."
    elif (days_since > 7 or failure_reason == "insufficient funds") and has_had_discount:
        return "escalate_human", "Discount already offered once; forcing escalation."
        
    return "soft_reminder", "Clean history; applying soft reminder."
