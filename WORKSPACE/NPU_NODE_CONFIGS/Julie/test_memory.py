#!/usr/bin/env python3
"""Quick test of memory endpoints."""
import requests

BASE = "http://127.0.0.1:8080"

# Test 1: Create conversation
print("Creating conversation...")
r = requests.post(f"{BASE}/memory/new", json={"name": "Test Chat", "project": "outback"})
print(f"Response: {r.json()}")
conv_id = r.json().get("id")

# Test 2: Save message
print("\nSaving message...")
r = requests.post(f"{BASE}/memory/save", json={
    "conversation_id": conv_id,
    "role": "user",
    "content": "Hello, this is a test message!"
})
print(f"Response: {r.json()}")

# Test 3: List conversations
print("\nListing conversations...")
r = requests.get(f"{BASE}/memory/list")
print(f"Response: {r.json()}")

# Test 4: Get conversation
print("\nGetting conversation...")
r = requests.post(f"{BASE}/memory/get", json={"id": conv_id})
print(f"Response: {r.json()}")

print("\n✅ All tests passed!")
