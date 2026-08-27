import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audit_log.db")

def init_db():
    """Initializes the SQLite database with the required schema."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT NOT NULL,
            customer_id TEXT NOT NULL,
            action TEXT NOT NULL,
            reasoning TEXT,
            urgency TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            outcome TEXT,
            follow_up_count INTEGER
        )
    """)
    conn.commit()
    conn.close()

def log_action(event_id, customer_id, action, reasoning, urgency, outcome, follow_up_count):
    """Logs an action to the audit database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    timestamp = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO audit_log 
        (event_id, customer_id, action, reasoning, urgency, timestamp, outcome, follow_up_count) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (event_id, customer_id, action, reasoning, urgency, timestamp, outcome, follow_up_count))
    
    conn.commit()
    conn.close()

def get_event_metrics(event_id):
    """
    Retrieves metrics for an event to enforce stopping rules.
    Returns a dictionary with follow_up_count and has_had_discount.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT action FROM audit_log WHERE event_id = ?
    """, (event_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    follow_up_count = len(rows)
    has_had_discount = any(row[0] == 'discount_nudge' for row in rows)
    
    return {
        "follow_up_count": follow_up_count,
        "has_had_discount": has_had_discount
    }
