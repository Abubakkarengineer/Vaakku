import pandas as pd
import os

MEMORY_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "customer_memory.csv")

def load_all_memory():
    """Loads the entire customer memory dataset."""
    if not os.path.exists(MEMORY_FILE):
        return pd.DataFrame(columns=["customer_id", "promises_made", "promises_kept", "promises_broken", "last_action_taken"])
    return pd.read_csv(MEMORY_FILE)

def get_customer_memory(customer_id):
    """Retrieves the memory record for a specific customer."""
    df = load_all_memory()
    customer_data = df[df["customer_id"] == customer_id]
    
    if customer_data.empty:
        # Return default if not found
        return {
            "customer_id": customer_id,
            "promises_made": 0,
            "promises_kept": 0,
            "promises_broken": 0,
            "last_action_taken": "none"
        }
    
    return customer_data.iloc[0].to_dict()

def update_customer_memory(customer_id, outcome, last_action_taken):
    """
    Updates a customer's memory record based on the outcome of an intervention.
    outcome: 'kept', 'broken', or 'none'
    """
    df = load_all_memory()
    
    idx = df.index[df["customer_id"] == customer_id].tolist()
    
    if idx:
        i = idx[0]
        if outcome in ["kept", "broken"]:
            df.at[i, "promises_made"] = int(df.at[i, "promises_made"]) + 1
            if outcome == "kept":
                df.at[i, "promises_kept"] = int(df.at[i, "promises_kept"]) + 1
            elif outcome == "broken":
                df.at[i, "promises_broken"] = int(df.at[i, "promises_broken"]) + 1
                
        df.at[i, "last_action_taken"] = last_action_taken
    else:
        # Add new customer if they didn't exist
        promises_made = 1 if outcome in ["kept", "broken"] else 0
        promises_kept = 1 if outcome == "kept" else 0
        promises_broken = 1 if outcome == "broken" else 0
        
        new_row = pd.DataFrame([{
            "customer_id": customer_id,
            "promises_made": promises_made,
            "promises_kept": promises_kept,
            "promises_broken": promises_broken,
            "last_action_taken": last_action_taken
        }])
        df = pd.concat([df, new_row], ignore_index=True)
        
    df.to_csv(MEMORY_FILE, index=False)
