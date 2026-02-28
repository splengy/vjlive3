#!/bin/bash
pkill -f batch_spec 2>/dev/null
sleep 1
rm -f /home/happy/generated_specs/*.md
nohup python3 /home/happy/batch_spec_gen.py > /home/happy/batch_spec.log 2>&1 &
echo "STARTED PID=$!"
