#!/bin/bash
cd "$(dirname "$0")"
source env/bin/activate
cd delft
./manage.py update >> logs/update.log
./manage.py check_alarms >> logs/update.log
