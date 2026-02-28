#!/usr/bin/env python3
"""Patch the RKLLM API to capture response text."""

import re

# Read original file
with open('/home/happy/rkllm/api.py', 'r') as f:
    content = f.read()

# Patch 1: Add response buffer to __init__
old_init = "self.param = None"
new_init = """self.param = None
        self._response_buffer = []
        self._last_response = \"\""""
content = content.replace(old_init, new_init, 1)

# Patch 2: Accumulate text in _callback
old_callback = """print(text_bytes.decode('utf-8', errors='replace'), end='', flush=True)"""
new_callback = """text = text_bytes.decode('utf-8', errors='replace')
                print(text, end='', flush=True)
                self._response_buffer.append(text)"""
content = content.replace(old_callback, new_callback, 1)

# Patch 3: Store complete response at finish
old_finish = """if state == RKLLM_RUN_FINISH:
            print("") # Newline at end"""
new_finish = """if state == RKLLM_RUN_FINISH:
            print("")  # Newline at end
            self._last_response = "".join(self._response_buffer)"""
content = content.replace(old_finish, new_finish, 1)

# Patch 4: Clear buffer and return response in run()
old_run_start = """def run(self, prompt, params=None):
        if params is None:
            params = {}"""
new_run_start = """def run(self, prompt, params=None):
        if params is None:
            params = {}
        
        # Clear buffer for new response
        self._response_buffer = []
        self._last_response = \"\""""
content = content.replace(old_run_start, new_run_start, 1)

# Patch 5: Return response instead of ret code
old_run_end = """ret = rkllm_lib.rkllm_run(self.handle, ctypes.byref(input_struct), ctypes.byref(infer_param), None)
        return ret"""
new_run_end = """ret = rkllm_lib.rkllm_run(self.handle, ctypes.byref(input_struct), ctypes.byref(infer_param), None)
        return self._last_response"""
content = content.replace(old_run_end, new_run_end, 1)

# Write patched file
with open('/home/happy/rkllm/api.py', 'w') as f:
    f.write(content)

print("Patched successfully!")
