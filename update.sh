#!/bin/bash
cd "$(dirname "$0")"
source ../env/bin/activate
./manage.py update >> logs/update.log
./manage.py check_alarms --notify >> logs/update.log
