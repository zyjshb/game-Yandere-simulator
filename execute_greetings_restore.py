# -*- coding: utf-8 -*-
import sys

# Let's run the code inside temp_extracted_code.py
try:
    with open('temp_extracted_code.py', 'r', encoding='utf-8') as f:
        script = f.read()
    
    # We can execute the script using exec()
    print("Executing temp_extracted_code.py...")
    # We need to make sure the script runs in the current directory
    exec(script, globals())
    print("Execution complete!")
except Exception as e:
    print("Error during execution:", e)
