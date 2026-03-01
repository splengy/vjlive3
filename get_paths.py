import re

board_path = "BOARD.md"
targets = ["P3-EXT012", "P3-EXT013", "P3-EXT015", "P3-EXT016", "P3-EXT019"]

with open(board_path, "r") as f:
    for line in f:
        for t in targets:
            if t in line:
                print(line.strip())
