# nexus-market

AI Marketplace — Python backend with AI Agent, evaluation pipelines, and simulation.

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (fast Python package & project manager)

## Setup

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync project dependencies
uv sync

# Copy the environment template and fill in your keys
cp .env.example .env
```

## Running

```bash
# Start the backend server
uv run python server/app.py

# Or via uvicorn directly
uv run uvicorn server.app:app --host 0.0.0.0 --port 3001
```

## Scripts

```bash
# Run evaluation pipeline
uv run python src/evaluation_pipeline.py

# Run simulation pipeline
uv run python src/simulation_pipeline.py

# Generate traces
uv run python generate_traces.py
```

## Adding Dependencies

```bash
uv add <package-name>
```
