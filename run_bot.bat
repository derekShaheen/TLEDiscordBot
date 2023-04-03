@echo off
:restart
title TLE Discord Bot
echo Starting the bot...
python TLEDiscord.py
echo The bot crashed, restarting in 5 seconds...
timeout /t 5
goto restart