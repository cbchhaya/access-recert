"""
Setup API Tables
================

Creates additional tables needed for the ARAS API.

Author: Chiradeep Chhaya
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "aras.db")


def setup_tables():
    """Create API-related tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Campaigns table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS campaigns (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            scope_type TEXT NOT NULL,
            scope_filter TEXT,
            auto_approve_threshold REAL DEFAULT 80.0,
            review_threshold REAL DEFAULT 50.0,
            start_date TEXT NOT NULL,
            due_date TEXT NOT NULL,
            status TEXT DEFAULT 'Draft',
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    print("Created campaigns table")

    # Review items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS review_items (
            id TEXT PRIMARY KEY,
            campaign_id TEXT NOT NULL,
            access_grant_id TEXT NOT NULL,
            employee_id TEXT NOT NULL,
            assurance_score REAL NOT NULL,
            classification TEXT NOT NULL,
            auto_certify_eligible INTEGER DEFAULT 0,
            clustering_consensus REAL DEFAULT 1.0,
            needs_clustering_review INTEGER DEFAULT 0,
            clustering_disagreement TEXT,
            status TEXT DEFAULT 'Pending',
            decision TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            FOREIGN KEY (campaign_id) REFERENCES campaigns(id),
            FOREIGN KEY (access_grant_id) REFERENCES access_grants(id),
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        )
    """)
    print("Created review_items table")

    # Audit records table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_records (
            id TEXT PRIMARY KEY,
            review_item_id TEXT NOT NULL,
            action TEXT NOT NULL,
            decision_by TEXT NOT NULL,
            decision_at TEXT NOT NULL,
            rationale TEXT,
            assurance_score REAL,
            auto_certified INTEGER DEFAULT 0,
            campaign_id TEXT NOT NULL,
            FOREIGN KEY (review_item_id) REFERENCES review_items(id),
            FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
        )
    """)
    print("Created audit_records table")

    # Proximity weights table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS proximity_weights (
            id TEXT PRIMARY KEY,
            structural REAL DEFAULT 0.25,
            functional REAL DEFAULT 0.35,
            behavioral REAL DEFAULT 0.30,
            temporal REAL DEFAULT 0.10,
            updated_at TEXT,
            updated_by TEXT
        )
    """)
    print("Created proximity_weights table")

    # Graduation status table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS graduation_status (
            category TEXT PRIMARY KEY,
            status TEXT DEFAULT 'observation',
            metrics TEXT,
            meets_criteria INTEGER DEFAULT 0,
            last_evaluated TEXT NOT NULL,
            graduated_at TEXT,
            approved_by TEXT
        )
    """)
    print("Created graduation_status table")

    # Compliance samples table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS compliance_samples (
            id TEXT PRIMARY KEY,
            campaign_id TEXT NOT NULL,
            sample_size INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            created_by TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            items TEXT,
            FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
        )
    """)
    print("Created compliance_samples table")

    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_review_items_campaign ON review_items(campaign_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_review_items_status ON review_items(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_review_items_employee ON review_items(employee_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_campaign ON audit_records(campaign_id)")
    print("Created indexes")

    # Migration: Add new columns for system recommendation and peer group tracking
    try:
        cursor.execute("ALTER TABLE review_items ADD COLUMN system_recommendation TEXT")
        print("Added system_recommendation column")
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        cursor.execute("ALTER TABLE review_items ADD COLUMN peer_group_size INTEGER")
        print("Added peer_group_size column")
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        cursor.execute("ALTER TABLE review_items ADD COLUMN human_review_reason TEXT")
        print("Added human_review_reason column")
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Insert default proximity weights
    cursor.execute("SELECT COUNT(*) FROM proximity_weights")
    if cursor.fetchone()[0] == 0:
        from datetime import datetime
        cursor.execute("""
            INSERT INTO proximity_weights (id, structural, functional, behavioral, temporal, updated_at, updated_by)
            VALUES ('default', 0.25, 0.35, 0.30, 0.10, ?, 'system')
        """, (datetime.utcnow().isoformat(),))
        print("Inserted default proximity weights")

    conn.commit()
    conn.close()
    print("\nAPI tables setup complete!")


if __name__ == "__main__":
    setup_tables()
