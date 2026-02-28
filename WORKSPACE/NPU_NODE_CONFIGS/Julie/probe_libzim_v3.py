import sys
try:
    from libzim.reader import Archive
except ImportError:
    from libzim import Archive

zim_path = "/home/happy/ai_library_stable/wikipedia/wikipedia_en_all_maxi.zim"

try:
    zim = Archive(zim_path)
    print("--- Inspecting Entry 0 ---")
    entry = zim._get_entry_by_id(0)
    print(f"Entry Type: {type(entry)}")
    print(f"Dir(Entry): {dir(entry)}")
    
    # Try accessing basic props
    try: print(f"Title: {entry.title}") 
    except: pass
    try: print(f"Path: {entry.path}") 
    except: pass
    try: print(f"Namespace: {entry.namespace}") 
    except: pass
    try: print(f"Redirect: {entry.is_redirect}")
    except: pass

except Exception as e:
    print(f"Error: {e}")
