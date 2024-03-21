if [ ! -d env-104-bot ]; then
    python -m venv env-104-bot
    source env-104-bot/bin/activate
    pip install pycryptodome firebase_admin selenium
fi

echo "Python venv prepare done. You can run 'source env-104-bot/bin/activate' to start dev"

if [ -f ~/Library/LaunchAgents/com.workfunction.104clockin.plist ]; then
    launchctl unload ~/Library/LaunchAgents/com.workfunction.104clockin.plist
fi

cp com.workfunction.104clockin.plist ~/Library/LaunchAgents/
launchctl load -w ~/Library/LaunchAgents/com.workfunction.104clockin.plist

echo "Autostart installed."
