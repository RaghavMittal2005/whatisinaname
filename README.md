# Hoja — Traffic Signal Control Environment

An OpenEnv reinforcement learning environment that simulates a **4-way traffic intersection**. An LLM agent controls traffic signals to minimise wait times, handle pedestrian crossings, and prioritise emergency vehicles.

## Tasks

| Task | Difficulty | Traffic | Pedestrians | Emergencies |
|------|-----------|---------|-------------|-------------|
| `easy` | Low | Off-peak (0–3 cars/step) | ❌ | ❌ |
| `medium` | Normal | Normal (1–5 cars/step) | ✅ | ❌ |
| `hard` | Peak hour | Heavy (3–8 cars/step) | ✅ | ✅ 🚑 |

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

## Reward Design

- **Base**: `-average_wait_time / 10` (minimise wait)
- **Emergency bonus**: `+5.0` for clearing an emergency vehicle
- **Emergency penalty**: `-3.0` if emergency waits > 2 steps
- **Queue penalty**: `-0.5` per direction with queue > 15
- **Pedestrian penalty**: `-0.3 × count` if pedestrians > 8

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
| `HF_TOKEN` | Hugging Face API token | — |
| `API_BASE_URL` | LLM API endpoint | `https://router.huggingface.co/v1` |
| `MODEL_NAME` | Model to use for inference | `Qwen/Qwen2.5-72B-Instruct` |
