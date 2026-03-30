#!/bin/bash
# Multi-model comparison test — runs 25 attack+format combos against 5 LLM models.
# Requires: Docker, remote Ollama at 192.168.68.61

set -e

OLLAMA_URL="http://192.168.68.61:11434"
ATTACKS="hidden_text,white_on_white,retrieval_poison,summary_steer,tool_routing"
FORMATS="pdf,docx,html,md,csv"

MODELS=(
    "phi4-mini"
    "deepseek-r1:1.5b"
    "llama3.2:latest"
    "llama3.2:1b"
    "gemma3"
)

COMPOSE_FILE="$(cd "$(dirname "$0")/.." && pwd)/docker-compose.yml"

for model in "${MODELS[@]}"; do
    echo ""
    echo "============================================"
    echo "  MODEL: $model"
    echo "============================================"
    echo ""

    # Restart demo app with the new model
    sudo OLLAMA_BASE_URL="$OLLAMA_URL" OLLAMA_MODEL="$model" \
        docker compose -f "$COMPOSE_FILE" up --build -d demo-app

    # Wait for it to come up
    for i in $(seq 1 10); do
        if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
            break
        fi
        sleep 2
    done

    # Run tests
    uv run maldoc run \
        --attack "$ATTACKS" \
        --format "$FORMATS" \
        --target demo \
        --target-url http://localhost:8000

    echo ""
    echo "  Completed: $model"
done

echo ""
echo "All 5 models tested. Reports are in reports/"
