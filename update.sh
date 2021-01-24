#!/bin/bash
cd "$(dirname "$0")"
source ../env/bin/activate
./manage.py check_alarms --download --notify >> logs/update.log
