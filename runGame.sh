#!/bin/bash

if hash python3 2>/dev/null; then
    ./halite -q -d "50 50" "python3 MyBot.py" "python3 testBots/V2_LowDashBot.py"
else
    ./halite -d "30 30" "python MyBot.py" "python RandomBot.py"
fi
