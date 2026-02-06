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
echo "Current user: $(whoami)"
echo "App user UID: ${APP_UID}, GID: ${APP_GID}"

# Ensure the config directory is owned by the 'app' user for proper permissions
echo "Ensuring ownership of ${CONFIG_DIR} is set to app user (${APP_UID}:${APP_GID})..."
chown -R "${APP_UID}:${APP_GID}" "${CONFIG_DIR}"
echo "New permissions for target config directory on host (bind mount source):"
ls -ld "${CONFIG_DIR}"

echo "Checking for user config file in ${CONFIG_DIR}..."

if [ ! -f "$USER_CONFIG" ]; then
    echo "No config.py found in persistent storage. Attempting to copy example config..."
    if [ -f "$EXAMPLE_CONFIG" ]; then
        if cp "$EXAMPLE_CONFIG" "$USER_CONFIG"; then
            echo "Successfully copied ${EXAMPLE_CONFIG} to ${USER_CONFIG}."
            # Ensure file is owned by app user and has correct permissions
            chown "${APP_UID}:${APP_GID}" "$USER_CONFIG"
            chmod 664 "$USER_CONFIG"
            echo "Set permissions for ${USER_CONFIG}."
            ls -l "$USER_CONFIG"
        else
            echo "Error: Failed to copy ${EXAMPLE_CONFIG} to ${USER_CONFIG}. Check permissions of ${CONFIG_DIR} on host."
            exit 1
        fi
    else
        echo "Error: ${EXAMPLE_CONFIG} not found inside container."
        exit 1
    fi
else
    echo "config.py found in persistent storage. Using existing configuration."
    # Ensure existing config.py is owned by app user
    chown "${APP_UID}:${APP_GID}" "$USER_CONFIG"
    ls -l "$USER_CONFIG"
fi



# Execute the main command
exec "$@"
