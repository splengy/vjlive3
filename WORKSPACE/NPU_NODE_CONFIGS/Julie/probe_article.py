import sys
try:
    from libzim.reader import Archive
except ImportError:
    from libzim import Archive

zim_path = "/home/happy/ai_library_stable/wikipedia/wikipedia_en_all_maxi.zim"

zim = Archive(zim_path)
print(f"Total: {zim.entry_count}")

for i in range(50000):
    try:
        entry = zim._get_entry_by_id(i)
        if entry.path.startswith('A/') and not entry.is_redirect:
            print(f"FOUND ARTICLE at {i}!")
            print(f"Title: {entry.title}")
            print(f"Path: {entry.path}")
            break
        if i % 1000 == 0:
            print(f"Checked {i} ({entry.path})")
    except:
        pass
