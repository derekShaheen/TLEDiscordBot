#!/bin/bash

cd /home/derek/TLEDiscordBot

while true; do
  echo "Attempting to update..."
  sudo /usr/bin/git reset --hard
  sudo /usr/bin/git pull
  echo "Starting the bot..."
  python3 TLEDiscord.py
  echo "The bot crashed, restarting in 5 seconds..."
  sleep 5
done
