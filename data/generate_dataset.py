import pandas as pd
import numpy as np
import random
import os

def generate_datasets(output_dir="data"):
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Generate Customer Memory
    # 20 Customers with varying histories
    customers = []
    for i in range(1, 21):
        cust_id = f"CUST_{i:03d}"
        history_type = random.choice(["clean", "clean", "mixed", "bad"])
        
        if history_type == "clean":
            promises_made = random.randint(0, 2)
            promises_kept = promises_made
            promises_broken = 0
        elif history_type == "mixed":
            promises_made = random.randint(2, 5)
            promises_broken = random.randint(1, 2)
            promises_kept = promises_made - promises_broken
        else: # bad
            promises_made = random.randint(3, 6)
            promises_broken = random.randint(2, 4)
            promises_kept = promises_made - promises_broken
            
        customers.append({
            "customer_id": cust_id,
            "promises_made": promises_made,
            "promises_kept": promises_kept,
            "promises_broken": promises_broken,
            "last_action_taken": "none"
        })
        
    df_customers = pd.DataFrame(customers)
    df_customers.to_csv(os.path.join(output_dir, "customer_memory.csv"), index=False)
    
    # 2. Generate Events
    # 60 events across the 20 customers
    event_types = ["checkout_abandoned", "subscription_failed", "invoice_overdue"]
    failure_reasons = [None, "insufficient funds", "card expired", "forgot to pay", "technical error", "disputed amount"]
    
    events = []
    for i in range(1, 61):
        event_id = f"EVT_{i:04d}"
        cust_id = random.choice(customers)["customer_id"]
        event_type = random.choice(event_types)
        amount = round(random.uniform(10.0, 500.0), 2)
        days_since_event = random.randint(1, 14)
        failure_reason = random.choice(failure_reasons)
        
        events.append({
            "event_id": event_id,
            "customer_id": cust_id,
            "event_type": event_type,
            "amount": amount,
            "status": "open",
            "days_since_event": days_since_event,
            "failure_reason": failure_reason
        })
        
    df_events = pd.DataFrame(events)
    df_events.to_csv(os.path.join(output_dir, "events.csv"), index=False)
    
    print(f"Generated {len(df_customers)} customers and {len(df_events)} events in '{output_dir}'.")

if __name__ == "__main__":
    generate_datasets()
