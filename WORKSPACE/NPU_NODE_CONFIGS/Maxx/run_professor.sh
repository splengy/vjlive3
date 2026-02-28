#!/bin/bash
echo Cleaning up old NPU processes...
pkill -9 -f professor.py 2>/dev/null || true
sleep 2

echo Starting Professor...
export PYTHONPATH=:/home/happy
python3 ./outback/professor.py
