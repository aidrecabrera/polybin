#!/bin/bash

cd /home/admin/polybin
source venv/bin/activate
python server.py &

cd app
pnpm run dev --host &
wait