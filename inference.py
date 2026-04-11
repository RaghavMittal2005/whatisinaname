"""
Inference Script - Hoja Traffic Signal Control
===============================================
MANDATORY
- Before submitting, ensure the following variables are defined in your environment configuration:
    API_BASE_URL   The API endpoint for the LLM.
    MODEL_NAME     The model identifier to use for inference.
    HF_TOKEN       Your Hugging Face / API key.
    LOCAL_IMAGE_NAME The name of the local image to use for the environment if you are using from_docker_image()
                     method

- Defaults are set only for API_BASE_URL and MODEL_NAME
    (and should reflect your active inference setup):
    API_BASE_URL = os.getenv("API_BASE_URL", "<your-active-endpoint>")
    MODEL_NAME = os.getenv("MODEL_NAME", "<your-active-model>")

- The inference script must be named `inference.py` and placed in the root directory of the project
- Participants must use OpenAI Client for all LLM calls using above variables

STDOUT FORMAT
- The script must emit exactly three line types to stdout, in this order:

    [START] task=<task_name> env=<benchmark> model=<model_name>
    [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
    [END]   success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>

  Rules:
    - One [START] line at episode begin.
    - One [STEP] line per step, immediately after env.step() returns.
    - One [END] line after env.close(), always emitted (even on exception).
    - reward and rewards are formatted to 2 decimal places.
    - done and success are lowercase booleans: true or false.
    - error is the raw last_action_error string, or null if none.
    - All fields on a single line with no newlines within a line.
    - Each tasks should return score in [0, 1]

  Example:
    [START] task=easy env=hoja model=Qwen/Qwen2.5-72B-Instruct
    [STEP] step=1 action=change_signal(north,30) reward=-0.10 done=false error=null
    [STEP] step=2 action=change_signal(east,20) reward=0.05 done=false error=null
    [END] success=true steps=25 score=0.72 rewards=-0.10,0.05,...
"""
from dotenv import load_dotenv
load_dotenv()
import asyncio
import json
import os
import re
import textwrap
from typing import List, Optional

from openai import OpenAI

from hoja import HojaAction, HojaEnv

IMAGE_NAME = os.getenv("IMAGE_NAME") or "hoja-app"
API_KEY = os.getenv("HF_TOKEN")

API_BASE_URL = os.getenv("API_BASE_URL") or "https://router.huggingface.co/v1"
MODEL_NAME = os.getenv("MODEL_NAME") or "Qwen/Qwen2.5-72B-Instruct"
BENCHMARK = "hoja"
MAX_STEPS = 25
TEMPERATURE = 0.7
MAX_TOKENS = 200

SYSTEM_PROMPT = textwrap.dedent("""\
You are an AI traffic signal controller for a 4-way intersection.

Each turn you receive the current traffic state and must decide which direction
to give a green signal and for how long.

ACTIONS - reply with EXACTLY this JSON format (nothing else):
{"direction": "<north|south|east|west>", "duration_seconds": <5-60>}

STRATEGY TIPS:
- Give green to the direction with the longest queue
- If an emergency vehicle is present, IMMEDIATELY give green to its direction
- Use shorter durations (10-20s) when traffic is balanced
- Use longer durations (30-60s) when one direction is heavily congested
- Consider pedestrian count - they cross during signal changes

Your goal: minimise average wait time, clear emergency vehicles fast, avoid long queues.
""").strip()


def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)


def build_user_prompt(obs, last_reward: float, history: List[str]) -> str:
    history_block = "\n".join(history[-5:]) if history else "None"
    parts = [
        f"Step: {obs.step_number}/{obs.max_steps}",
        f"Status: {obs.status_message}",
        f"Current green: {obs.current_green}",
        f"Time of day: {obs.time_of_day}",
        f"Queues - N:{obs.queue_north}  S:{obs.queue_south}  E:{obs.queue_east}  W:{obs.queue_west}",
        f"Average wait time: {obs.average_wait_time:.2f}",
        f"Pedestrians waiting: {obs.pedestrian_count}",
    ]
    if obs.emergency_vehicle_present:
        parts.append(f"EMERGENCY VEHICLE in {obs.emergency_vehicle_direction} direction - prioritise!")
    parts.append(f"Last reward: {last_reward:.2f}")
    parts.append(f"Recent history:\n{history_block}")
    parts.append('Reply with JSON: {"direction": "...", "duration_seconds": ...}')
    return "\n".join(parts)


def parse_action(text: str) -> tuple:
    """Parse LLM output into (direction, duration_seconds)."""
    # Try JSON parse first
    try:
        data = json.loads(text)
        return data["direction"], int(data["duration_seconds"])
    except (json.JSONDecodeError, KeyError, ValueError):
        pass

    # Fallback: regex
    dir_match = re.search(r'"direction"\s*:\s*"(\w+)"', text)
    dur_match = re.search(r'"duration_seconds"\s*:\s*(\d+)', text)
    if dir_match and dur_match:
        return dir_match.group(1), int(dur_match.group(1))

    # Last resort: pick the first direction word found
    for d in ["north", "south", "east", "west"]:
        if d in text.lower():
            return d, 20
    return "north", 20


def get_model_action(client: OpenAI, obs, last_reward: float, history: List[str]) -> tuple:
    user_prompt = build_user_prompt(obs, last_reward, history)
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            stream=False,
        )
        text = (completion.choices[0].message.content or "").strip()
        return parse_action(text)
    except Exception as exc:
        print(f"[DEBUG] Model request failed: {exc}", flush=True)
        return "north", 20


async def run_task(task_name: str) -> None:
    """Run a single episode for the given task."""
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    env = await HojaEnv.from_docker_image(
        IMAGE_NAME,
        env_vars={"HOJA_TASK": task_name},
    )

    history: List[str] = []
    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)

    try:
        result = await env.reset()
        obs = result.observation
        last_reward = 0.0

        for step in range(1, MAX_STEPS + 1):
            if result.done:
                break

            direction, duration = get_model_action(client, obs, last_reward, history)

            result = await env.step(HojaAction(direction=direction, duration_seconds=duration))
            obs = result.observation

            reward = result.reward or 0.0
            done = result.done
            error = None

            rewards.append(reward)
            steps_taken = step
            last_reward = reward

            action_str = f"change_signal({direction},{duration})"
            log_step(step=step, action=action_str, reward=reward, done=done, error=error)

            history.append(
                f"Step {step}: {action_str} -> reward {reward:+.2f} "
                f"(queues N:{obs.queue_north} S:{obs.queue_south} E:{obs.queue_east} W:{obs.queue_west})"
            )

            if done:
                # Replace primitive score calculation with the detailed Grader output
                if obs.metadata and "grader_report" in obs.metadata:
                    score = obs.metadata["grader_report"].get("total_score", 0.0)
                    # Baseline example parsing
                    baseline = obs.metadata["grader_report"].get("baseline_gpt4o_mini", 0.0)
                    print(f"[DEBUG] Final Grader Score: {score:.2f} (Baseline: {baseline:.2f})", flush=True)
                break

        # Fallback if grader fails or completes early
        if score == 0.0 and rewards:
            score = sum(rewards) / len(rewards)
        
        score = min(max(score, 0.0), 1.0)
        success = score >= 0.5

    finally:
        try:
            await env.close()
        except Exception as e:
            print(f"[DEBUG] env.close() error: {e}", flush=True)
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)


async def main() -> None:
    tasks = os.getenv("HOJA_TASKS", "easy,medium,hard,night,incident").split(",")
    for task in tasks:
        task = task.strip()
        if task:
            await run_task(task)


if __name__ == "__main__":
    asyncio.run(main())