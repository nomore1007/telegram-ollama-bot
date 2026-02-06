#!/bin/bash
set -e

# Use the new paths from the latest commit
CONFIG_DIR="/app/data"
EXAMPLE_CONFIG="/app/config.example.py"
USER_CONFIG="${CONFIG_DIR}/config.py"

# Get the UID/GID of the 'app' user from the Dockerfile
APP_UID=$(id -u app)
APP_GID=$(id -g app)

echo "Running entrypoint script..."

chown -R "${APP_UID}:${APP_GID}" "${CONFIG_DIR}"



if [ ! -f "$USER_CONFIG" ]; then
    echo "No config.py found in persistent storage. Attempting to copy example config..."
    if [ -f "$EXAMPLE_CONFIG" ]; then
        if cp "$EXAMPLE_CONFIG" "$USER_CONFIG"; then
            chown "${APP_UID}:${APP_GID}" "$USER_CONFIG"
            chmod 664 "$USER_CONFIG"
        else
            echo "Error: Failed to copy ${EXAMPLE_CONFIG} to ${USER_CONFIG}. Check permissions of ${CONFIG_DIR} on host."
            exit 1
        fi
    else
        echo "Error: ${EXAMPLE_CONFIG} not found inside container."
        exit 1
    fi
else
    # Ensure existing config.py is owned by app user
    chown "${APP_UID}:${APP_GID}" "$USER_CONFIG"
fi



# Execute the main command
exec "$@"
