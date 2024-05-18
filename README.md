# Server Monitor Discord Bot

This Discord bot is designed to monitor server activity, particularly focusing on voice channel usage. It provides daily insights into user activities, like joining or leaving channels, and generates daily graphs depicting voice channel usage over time.

## Features

- **Real-time Monitoring:** Tracks when users join or leave voice channels.
- **Daily Graphs:** Generates a graph daily to show voice channel usage.
- **Activity Logs:** Logs server events such as users joining or leaving.
- **Server Commands:** Includes commands to manage logging settings and more.

## Commands

- `!move`: Manually move users between voice channels.
- `!set_log_channel`: Set the logging channel for server events.
- `!toggle_logging`: Enable or disable logging.
- `!allowed_roles`: Set which roles can use the bot commands.
- `!heartbeat`: Display current bot status and server metrics.
- `!exit`: Safely shut down the bot.

## Events Monitored

- Users joining or leaving the server.
- Changes in voice channel states.
- Daily activity reports and automated user movements based on predefined schedules.

![Image](https://i.imgur.com/d5wyY5u.png)
![Image2](https://i.imgur.com/A2JScAh.png)

## Development

This bot uses Python 3.8+ and the following major libraries:
- `discord.py`: For interacting with the Discord API.
- `asyncio`: For asynchronous operations.
- `rich`: For generating rich text outputs and tables in the terminal.

---

For more information on setting up and running the bot, refer to the official `discord.py` documentation.
