import json

with open('WORKSPACE/COMMS/QUEUE.json') as f:
    data = json.load(f)

print('Total tasks:', len(data))
print('By status:')
for s in ['queued', 'in_progress', 'completed']:
    count = len([t for t in data if t['status'] == s])
    print(f'  {s}: {count}')

p3_vd_tasks = [t for t in data if t['task_id'].startswith('P3-VD')]
print(f'\nP3-VD tasks: {len(p3_vd_tasks)}')
print('P3-VD by status:')
for s in ['queued', 'in_progress', 'completed']:
    count = len([t for t in p3_vd_tasks if t['status'] == s])
    print(f'  {s}: {count}')

# Show in-progress task details
in_progress = [t for t in data if t['status'] == 'in_progress']
if in_progress:
    print('\nIn-progress tasks:')
    for t in in_progress:
        print(f"  {t['task_id']} (assigned to {t.get('assigned_worker', 'unassigned')})")
