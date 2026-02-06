#!/bin/bash
set -e

CONFIG_DIR="/opt/telegram-ollama-bot"
EXAMPLE_CONFIG="/app/src/config.example.py"
USER_CONFIG="${CONFIG_DIR}/config.py"

echo "Running entrypoint script..."
echo "Current user: $(whoami)"

# Display permissions of target config directory on host (bind mount source)
echo "Permissions of target config directory on host (bind mount source):"
ls -ld "${CONFIG_DIR}"

echo "Checking for user config file in ${CONFIG_DIR}..."

if [ ! -f "$USER_CONFIG" ]; then
    echo "No config.py found in persistent storage. Attempting to copy example config..."
    if [ ! -f "$EXAMPLE_CONFIG" ]; then
        echo "Error: ${EXAMPLE_CONFIG} not found inside container."
        exit 1
    fi

    if cp "$EXAMPLE_CONFIG" "$USER_CONFIG"; then
        echo "Successfully copied ${EXAMPLE_CONFIG} to ${USER_CONFIG}."
        echo "Please ensure the host directory '${CONFIG_DIR}' has appropriate ownership and write permissions for the non-root Docker user (app, UID 1000)."
        ls -l "$USER_CONFIG"
    else
        echo "Error: Failed to copy ${EXAMPLE_CONFIG} to ${USER_CONFIG}. This is likely due to incorrect permissions for the '${CONFIG_DIR}' directory on the host."
        echo "Please ensure the host directory '${CONFIG_DIR}' exists and has appropriate ownership and write permissions for the non-root Docker user (app, UID 1000)."
        exit 1
    fi
else
    echo "config.py found in persistent storage. Using existing configuration."
    ls -l "$USER_CONFIG"
fi

# Execute the main command
exec "$@"