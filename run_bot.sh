#!/bin/bash

while true; do
  git reset --hard
  git pull
  echo "Starting the bot..."
  python3 TLEDiscordBot.py
  echo "The bot crashed, restarting in 5 seconds..."
  sleep 5
done
