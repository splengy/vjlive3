import sys
try:
    from libzim.reader import Archive
except ImportError:
    from libzim import Archive

zim_path = "/home/happy/ai_library_stable/wikipedia/wikipedia_en_all_maxi.zim"
zim = Archive(zim_path)

idx = 25000
entry = zim._get_entry_by_id(idx)
print(f"Index: {idx}")
print(f"Title: {entry.title}")
print(f"Path: {entry.path}")

try:
    item = entry.get_item()
    print(f"Item Type: {type(item)}")
    print(f"Item Dir: {dir(item)}")
    try: print(f"Mimetype: {item.mimetype}")
    except: pass
    try: print(f"Size: {item.size}")
    except: pass
except Exception as e:
    print(f"Error getting item: {e}")
