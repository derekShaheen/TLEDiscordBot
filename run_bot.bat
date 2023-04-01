@echo off
:restart
echo Starting the bot...
python main_bot_file.py
echo The bot crashed, restarting in 5 seconds...
timeout /t 5
goto restart