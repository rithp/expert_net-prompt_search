#!/bin/bash

# Monitor Docker container logs and health
# Usage: ./docker_monitor.sh [container_name]

CONTAINER_NAME=${1:-problemnet-backend}

echo "🔍 Monitoring container: $CONTAINER_NAME"
echo "Press Ctrl+C to exit"

# Check if container exists
if ! docker ps -a --format "{{.Names}}" | grep -q "^$CONTAINER_NAME$"; then
    echo "❌ Container '$CONTAINER_NAME' not found"
    exit 1
fi

# Follow logs
echo "📝 Container logs:"
docker logs -f "$CONTAINER_NAME"
