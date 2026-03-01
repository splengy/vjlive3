import glob

files = glob.glob('docs/specs/_02_fleshed_out/*.md')
fixed = 0

for f in files:
    with open(f, 'r') as file:
        lines = file.readlines()
        
    needs_research_count = sum(1 for line in lines if '[NEEDS RESEARCH]' in line)
    has_easter_egg = any('Easter Egg Council' in line for line in lines)
    
    if needs_research_count > 20 or (has_easter_egg and len([line for line in lines if 'Easter Egg Council' in line]) > 2):
        # Find exactly where to chop it off
        # Let's find the first Easter Egg Council. If not present, find the first NEEDS RESEARCH that is part of a cluster.
        chop_index = len(lines)
        for i, line in enumerate(lines):
            if 'Easter Egg Council' in line:
                chop_index = i
                break
                
        # If we didn't chop by Easter Egg, let's chop by the first of the many NEEDS RESEARCH lines
        if chop_index == len(lines):
            for i, line in enumerate(lines):
                if '[NEEDS RESEARCH]' in line:
                    chop_index = i
                    break
        
        truncate_index = chop_index
        # Try to catch the '---' divider right before it
        for offset in range(1, 4):
            if chop_index - offset >= 0 and lines[chop_index - offset].strip() == '---':
                truncate_index = chop_index - offset
                break
                
        real_content = lines[:truncate_index]
        
        # Clean up any trailing garbage or repetitive [NEEDS RESEARCH] right at the cut point
        while real_content and (not real_content[-1].strip() or '[NEEDS RESEARCH]' in real_content[-1] or real_content[-1].strip() == '---'):
            real_content.pop()
            
        if len(real_content) > 80:
            with open(f, 'w') as file:
                file.writelines(real_content)
                file.write('\n')
            fixed += 1
            print(f'Salvaged: {f} (chopped {len(lines) - len(real_content)} hallucinated lines)')

print(f'\nTotal files salvaged: {fixed}')
