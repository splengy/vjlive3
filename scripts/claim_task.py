import os
import sys
import fcntl
import glob
import time

def claim_task(worker_name):
    worker_dirs = {
        'julie': 'docs/specs/_02_active_julie',
        'maxx': 'docs/specs/_03_active_maxx',
        'desktop': 'docs/specs/_05_active_desktop'
    }
    
    worker_key = worker_name.lower().replace('-roo', '')
    if worker_key not in worker_dirs:
        active_dir = f'docs/specs/_active_{worker_key}'
    else:
        active_dir = worker_dirs[worker_key]
        
    os.makedirs(active_dir, exist_ok=True)
    os.makedirs('WORKSPACE/COMMS', exist_ok=True)

    lock_file_path = 'WORKSPACE/COMMS/.queue.lock'
    board_path = 'BOARD.md'
    skeletons_dir = 'docs/specs/_01_skeletons'
    
    with open(lock_file_path, 'w') as lock_file:
        try:
            # Atomic non-blocking lock
            fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("QUEUE_LOCKED: Another agent is currently claiming a task. Please try again in 5 seconds.")
            sys.exit(1)

        skeletons = sorted(glob.glob(os.path.join(skeletons_dir, '*.md')))
        if not skeletons:
            print("QUEUE_EMPTY: No skeleton specs available to claim.")
            fcntl.flock(lock_file, fcntl.LOCK_UN)
            sys.exit(0)

        with open(board_path, 'r') as f:
            board_lines = f.readlines()

        claimed_file = None
        claimed_id = None
        board_line_index = -1

        # Match highest priority pending task in BOARD.md
        for i, line in enumerate(board_lines):
            if '⬜ PENDING SKELETON' in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) > 2:
                    task_id = parts[1]
                    for skel in skeletons:
                        filename = os.path.basename(skel)
                        # Match ID prefix to file name
                        if filename.startswith(task_id):
                            claimed_file = skel
                            claimed_id = task_id
                            board_line_index = i
                            break
            if claimed_file:
                break
        
        # Fallback: if BOARD matching didn't trigger, just take the first skeleton
        if not claimed_file:
            claimed_file = skeletons[0]
            filename = os.path.basename(claimed_file)
            claimed_id = filename.split('_')[0] if '_' in filename else filename.replace('.md', '')
            
            for i, line in enumerate(board_lines):
                if claimed_id in line and 'PENDING SKELETON' in line:
                    board_line_index = i
                    break

        if board_line_index != -1:
            line = board_lines[board_line_index]
            # Replace pending status with in-progress
            line = line.replace('⬜ PENDING SKELETON (Pass 1)', f'🟦 IN PROGRESS ({worker_name})')
            line = line.replace('⬜ PENDING SKELETON', f'🟦 IN PROGRESS ({worker_name})')
            board_lines[board_line_index] = line
            
            with open(board_path, 'w') as f:
                f.writelines(board_lines)

        dest_path = os.path.join(active_dir, os.path.basename(claimed_file))
        os.rename(claimed_file, dest_path)

        fcntl.flock(lock_file, fcntl.LOCK_UN)
        
        print(f"SUCCESS: Claimed Task {claimed_id}")
        print(f"FILE: {dest_path}")
        print("BOARD.md has been atomically updated to IN PROGRESS.")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/claim_task.py <agent_name>")
        print("Example: python3 scripts/claim_task.py julie")
        sys.exit(1)
    claim_task(sys.argv[1])
