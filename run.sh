source .venv/bin/activate
# loop to restart
while true; do
    uv sync --upgrade
    nb run
    sleep 5
done
