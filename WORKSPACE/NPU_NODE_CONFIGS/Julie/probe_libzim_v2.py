import libzim
print("--- Module Dir ---")
print(dir(libzim))

print("\n--- Archive Class Dir ---")
try:
    print(dir(libzim.Archive))
except Exception as e:
    print(f"Error inspecting Archive class: {e}")

try:
    # Try to instantiate to see instance methods (dummy path might fail but we can try help if strictly needed)
    # help(libzim.Archive) # help might be too long. 
    pass
except:
    pass
