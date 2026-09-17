#!/usr/bin/env bash
# k9x_enterprise_repository — build and run helper (single container, no pod needed)
# Run from any directory on the Podman host (no sudo needed — script handles it).
#
# Commands:
#   build   — build the k9x-enterprise-repository container image
#   start   — start the container (port 8088, matches the cloudflared
#             ingress rule: repo.k9x.ai -> http://localhost:8088)
#   stop    — stop the container
#   logs    — tail logs
#   all     — build + start

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
IMAGE="k9x-enterprise-repository:latest"
CONTAINER="k9x-enterprise-repository"
PORT=8088

cmd="${1:-help}"

case "$cmd" in

  build)
    echo "Building $IMAGE ..."
    cd "$PROJECT_DIR"
    sudo podman build -t "$IMAGE" -f ubuntu/Containerfile .
    echo "Build complete: $IMAGE"
    ;;

  start)
    ENV_FILE="$PROJECT_DIR/.env"
    [[ -f "$ENV_FILE" ]] || { echo "Error: $ENV_FILE not found."; exit 1; }
    echo "Starting $CONTAINER on port $PORT ..."
    sudo podman rm -f "$CONTAINER" 2>/dev/null || true
    sudo podman run -d \
      --name "$CONTAINER" \
      --restart=always \
      -p "$PORT:$PORT" \
      --env-file "$ENV_FILE" \
      "$IMAGE"
    echo ""
    HOST_IP=$(hostname -I | awk '{print $1}')
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  k9x_enterprise_repository"
    echo "  Web UI:  http://${HOST_IP}:${PORT}/"
    echo "  Health:  http://${HOST_IP}:${PORT}/health"
    echo "  Public:  https://repo.k9x.ai (via cloudflared)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    ;;

  stop)
    echo "Stopping $CONTAINER ..."
    sudo podman stop "$CONTAINER" 2>/dev/null || true
    echo "Stopped."
    ;;

  logs)
    sudo podman logs -f "$CONTAINER"
    ;;

  all)
    "$0" build
    "$0" start
    ;;

  help|*)
    echo "Usage: $0 <command>"
    echo ""
    echo "Commands:"
    echo "  build   — build the Podman image ($IMAGE)"
    echo "  start   — start the container (port $PORT)"
    echo "  stop    — stop the container"
    echo "  logs    — tail logs"
    echo "  all     — build + start"
    ;;

esac
