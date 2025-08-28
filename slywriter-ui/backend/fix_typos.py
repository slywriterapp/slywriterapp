#!/usr/bin/env python3
"""
Script to fix typo settings in existing database profiles
"""

import sqlite3
import os
import json

# Database path
db_path = "./slywriter.db"

if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Update all profiles to enable typos with realistic chances
updates = [
    ("Slow", True, 0.04),     # 4% for slow typing
    ("Medium", True, 0.03),    # 3% for medium typing
    ("Fast", True, 0.02),      # 2% for fast typing
    ("Essay", True, 0.035),    # 3.5% for essay writing
    ("Custom", True, 0.03),    # 3% for custom profiles
]

print("Updating profile typo settings...")
for name, enabled, chance in updates:
    cursor.execute("""
        UPDATE profiles 
        SET typos_enabled = ?, typo_chance = ?
        WHERE name = ?
    """, (enabled, chance, name))
    print(f"  - {name}: typos_enabled={enabled}, typo_chance={chance*100:.1f}%")

# Also update any custom profiles to have typos enabled
cursor.execute("""
    UPDATE profiles 
    SET typos_enabled = 1, typo_chance = 0.03
    WHERE is_builtin = 0 AND typos_enabled = 0
""")

# Get updated profiles to verify
cursor.execute("""
    SELECT name, typos_enabled, typo_chance 
    FROM profiles 
    ORDER BY name
""")

print("\nCurrent profile settings:")
for row in cursor.fetchall():
    name, enabled, chance = row
    status = "ON" if enabled else "OFF"
    print(f"  - {name}: typos={status}, chance={chance*100:.1f}%")

# Commit changes
conn.commit()
conn.close()

print("\n✅ Typo settings updated successfully!")
print("The typo system should now work correctly with realistic mistake rates.")