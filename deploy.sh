#!/bin/bash

LOG_FILE="/home/jiehoes/geonode-project/deploy.log"

echo "============================" >> $LOG_FILE
echo "DEPLOY START $(date)" >> $LOG_FILE

cd /home/jiehoes/geonode-project || exit

echo "[INFO] Fetch latest code..." >> $LOG_FILE
git fetch origin >> $LOG_FILE 2>&1

echo "[INFO] Reset to origin/master..." >> $LOG_FILE
git reset --hard origin/master >> $LOG_FILE 2>&1

echo "[INFO] Current commit:" >> $LOG_FILE
git log --oneline -1 >> $LOG_FILE

echo "[INFO] WHOAMI: $(whoami)" >> $LOG_FILE

echo "DEPLOY DONE $(date)" >> $LOG_FILE
echo "============================" >> $LOG_FILE