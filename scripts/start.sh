#!/bin/bash

# Set PATH to include the directory where pnpm is installed

# activate
source /home/admin/trashscan/venv/bin/activate

# start server
python /home/admin/trashscan/raspi/server.py &

# start app
cd /home/admin/trashscan/app/
npm run dev -- --host &

sleep 5

xdg-open 'http://localhost:5173' &
wmctrl -r 'http://localhost:5173' -b add,fullscreen
read -p "Press enter to exit"