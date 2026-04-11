---
title: Hoja Traffic Signal Control
emoji: 🚦
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 8000
---
# Hoja - Traffic Signal Control Environment

[![Pytest Coverage](https://img.shields.io/badge/coverage-80%25-green)](tests/)

An OpenEnv reinforcement learning environment that simulates a **4-way traffic intersection**. An LLM agent controls traffic signals to minimise wait times, handle pedestrian crossings, and prioritise emergency vehicles.

## Tasks

| Task | Difficulty | Traffic | Pedestrians | Emergencies | Description |
|------|-----------|---------|-------------|-------------|-------------|
| `easy` | Low | Off-peak (0-3 cars/step) | No | No | Basic flow control |
| `medium` | Normal | Normal (1-5 cars/step) | Yes | No | Adds pedestrian gaps |
| `hard` | Peak hour | Heavy (3-8 cars/step) | Yes | Yes | Peak hour + Ambulances |
| `night` | Visibility | Low (0-4 cars/step) | High Risk | 0.3 | Low visibility condition |
| `incident`| Chaos | Blocked (2-9 cars/step)| Yes | High | East bound blockage |

## Action

```json
{"direction": "north|south|east|west", "duration_seconds": 5-60}
```

The agent chooses which direction gets a green signal and for how long.

## Observation

| Field | Description |
|-------|-------------|
| `queue_north/south/east/west` | Cars queued in each direction |
| `time_of_day` | `off_peak`, `normal`, or `peak` |
| `pedestrian_count` | Pedestrians waiting to cross |
| `emergency_vehicle_present` | Whether an emergency vehicle is waiting |
| `emergency_vehicle_direction` | Which direction the emergency vehicle is in |
| `average_wait_time` | Average wait time across all directions |

## Grader scoring metric formula

A custom Professional Grader (`app/grader.py`) outputs a cumulative scalar `[0.0, 1.0]` per episode:
- **Throughput [0.35]:** Total vehicles passed intersection
- **Safety [0.25]:** Penalty for pedestrians or queued vehicles violation
- **Efficiency [0.20]:** Scaling factor of minimized wait times
- **Emergency Priority [0.20]:** Number of emergency vehicles effectively passed

## Quick Start

```bash
# Install dependencies
uv sync

# Run locally
uv run server

# Build Docker image
docker build -t hoja-app .

# Run in Docker
docker run -p 8000:8000 hoja-app

# Deploy to HF Spaces
openenv push --repo-id your-username/your-space
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `HOJA_TASK` | Task difficulty: `easy`, `medium`, `hard` | `easy` |
| `HF_TOKEN` | Hugging Face API token | - |
| `API_BASE_URL` | LLM API endpoint | `https://router.huggingface.co/v1` |
| `MODEL_NAME` | Model to use for inference | `Qwen/Qwen2.5-72B-Instruct` |
