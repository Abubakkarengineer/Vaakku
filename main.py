import pandas as pd
import os
import random
from audit.logger import init_db, log_action, get_event_metrics
from agent.memory import get_customer_memory, update_customer_memory
from agent.diagnose import diagnose_event
from agent.decide import decide_action
from agent.execute import execute_intervention

def simulate_outcome(action):
    """
    Simulates the customer's response based on the action taken.
    Returns: 'kept', 'broken', or 'none' (for no action / escalation)
    """
    if action in ["no_action", "escalate_human"]:
        return "none"
        
    # Simulated probability of keeping a promise based on action intensity
    if action == "discount_nudge":
        prob_kept = 0.90 # Very likely to pay with a discount
    elif action == "firm_reminder":
        prob_kept = 0.60
    else: # soft_reminder
        prob_kept = 0.40
        
    return "kept" if random.random() < prob_kept else "broken"

def run_pipeline():
    print("Initializing Database...")
    init_db()
    
    events_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "events.csv")
    if not os.path.exists(events_file):
        print("Events file not found. Please run data/generate_dataset.py first.")
        return
        
    events_df = pd.read_csv(events_file)
    print(f"Loaded {len(events_df)} events for processing.\n")
    
    for index, event_row in events_df.iterrows():
        event_record = event_row.to_dict()
        event_id = event_record['event_id']
        customer_id = event_record['customer_id']
        
        print(f"Processing {event_id} for {customer_id}...")
        
        # 1. Fetch current memory & metrics
        customer_memory = get_customer_memory(customer_id)
        metrics = get_event_metrics(event_id)
        
        # Pass metrics into memory for decision logic
        customer_memory['has_had_discount'] = metrics['has_had_discount']
        follow_up_count = metrics['follow_up_count']
        
        # 2. Diagnose
        diagnosis_result = diagnose_event(event_record, customer_memory)
        
        # 3. Decide
        action, reasoning = decide_action(event_record, customer_memory, diagnosis_result, follow_up_count)
        
        # 4. Execute
        exec_result = execute_intervention(action, event_record, diagnosis_result)
        
        # 5. Simulate Outcome
        outcome = simulate_outcome(action)
        
        # Log event update if kept
        if outcome == 'kept':
            events_df.at[index, 'status'] = 'recovered'
        elif action == 'escalate_human':
            events_df.at[index, 'status'] = 'escalated'
            
        # 6. Log Action
        log_action(
            event_id=event_id,
            customer_id=customer_id,
            action=action,
            reasoning=reasoning,
            urgency=diagnosis_result.get('recommended_urgency', 'medium'),
            outcome=outcome,
            follow_up_count=follow_up_count + 1
        )
        
        # 7. Update Memory
        update_customer_memory(customer_id, outcome, action)
        
        print(f"  -> Action: {action} | Outcome: {outcome}")
        
    # Save updated events back to reflect new statuses (recovered, escalated)
    events_df.to_csv(events_file, index=False)
    print("\nPipeline run complete.")

if __name__ == "__main__":
    run_pipeline()
