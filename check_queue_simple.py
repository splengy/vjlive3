import json

with open('WORKSPACE/COMMS/QUEUE.json') as f:
    data = json.load(f)

total = len(data)
completed = len([t for t in data if t['status'] == 'completed'])
in_progress = len([t for t in data if t['status'] == 'in_progress'])
queued = len([t for t in data if t['status'] == 'queued'])

print(f'Total tasks: {total}')
print(f'Completed: {completed}')
print(f'In progress: {in_progress}')
print(f'Queued: {queued}')

p3_vd_tasks = [t for t in data if t['task_id'].startswith('P3-VD')]
p3_vd_completed = len([t for t in p3_vd_tasks if t['status'] == 'completed'])
p3_vd_in_progress = len([t for t in p3_vd_tasks if t['status'] == 'in_progress'])
p3_vd_queued = len([t for t in p3_vd_tasks if t['status'] == 'queued'])

print(f'\nP3-VD tasks: {len(p3_vd_tasks)}')
print(f'P3-VD completed: {p3_vd_completed}')
print(f'P3-VD in progress: {p3_vd_in_progress}')
print(f'P3-VD queued: {p3_vd_queued}')
