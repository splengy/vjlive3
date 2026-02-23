import re

BOARD_FILE = "/home/happy/Desktop/claude projects/VJLive3_The_Reckoning/BOARD.md"

def get_next_missing():
    with open(BOARD_FILE, "r") as f:
        lines = f.readlines()
        
    found = False
    
    # Starting from P4-COR008 since 001/002 are out of scope and 003-007 are drafted
    for line in lines:
        if "| P4-COR" in line and "⬜ Todo" in line:
            # We want to map the next 5 that are to-do
            print(line.strip())

if __name__ == "__main__":
    get_next_missing()
