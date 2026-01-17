# database.py - Database operations

import pickle

# Security Issue: Unsafe deserialization
def load_user_session(session_data):
    # Vulnerable to arbitrary code execution
    return pickle.loads(session_data)

# Performance Issue: Large loop without pagination
def process_all_records():
    for i in range(10000):  # Large iteration
        process_record(i)

def process_record(i):
    # Simulate processing
    pass

# Security Issue: subprocess with shell=True
import subprocess
def execute_user_command(cmd):
    # Vulnerable to command injection
    subprocess.run(cmd, shell=True)
