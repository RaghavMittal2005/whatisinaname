# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Hoja Traffic Signal Control Environment.

Simulates a 4-way traffic intersection. The agent controls which direction
gets a green signal and for how long. Three difficulty levels:
  - easy:   Off-peak, low traffic, no pedestrians or emergencies
  - medium: Normal traffic with pedestrian crossings
  - hard:   Peak-hour traffic with emergency vehicle priority
"""

import os
import random
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from ..models import HojaAction, HojaObservation, HojaState
except ImportError:
    from models import HojaAction, HojaObservation, HojaState

DIRECTIONS = ["north", "south", "east", "west"]

# Task configurations
TASK_CONFIGS = {
    "easy": {
        "time_of_day": "off_peak",
        "arrival_rate": (0, 3),       # cars arriving per step per direction
        "pedestrians": False,
        "emergencies": False,
        "max_steps": 25,
    },
    "medium": {
        "time_of_day": "normal",
        "arrival_rate": (1, 5),
        "pedestrians": True,
        "emergencies": False,
        "max_steps": 25,
    },
    "hard": {
        "time_of_day": "peak",
        "arrival_rate": (3, 8),
        "pedestrians": True,
        "emergencies": True,
        "max_steps": 25,
    },
}


class HojaEnvironment(Environment):
    """
    Traffic signal control environment for a 4-way intersection.

    The agent must minimise average vehicle wait time, handle pedestrians,
    and give priority to emergency vehicles when present.
    """

    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self):
        self._task = os.getenv("HOJA_TASK", "medium")
        if self._task not in TASK_CONFIGS:
            self._task = "medium"
        self._cfg = TASK_CONFIGS[self._task]
        self._max_steps = self._cfg["max_steps"]
        
        self._total_vehicles_cleared = 0
        self._current_green = "none"
        
        self._state = self._build_state(episode_id=str(uuid4()), step_count=0)

        # Per-direction queues and cumulative wait
        self._queues = {d: 0 for d in DIRECTIONS}
        self._wait_times = {d: 0.0 for d in DIRECTIONS}

        # Pedestrian and emergency state
        self._pedestrian_count = 0
        self._emergency_present = False
        self._emergency_direction = None
        self._emergency_wait = 0  # steps the emergency has been waiting

        self._current_green = "none"

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------
    def reset(self) -> HojaObservation:
        self._total_vehicles_cleared = 0
        self._current_green = "none"
        self._state = self._build_state(episode_id=str(uuid4()), step_count=0)
        self._queues = {d: 0 for d in DIRECTIONS}
        self._wait_times = {d: 0.0 for d in DIRECTIONS}
        self._pedestrian_count = 0
        self._emergency_present = False
        self._emergency_direction = None
        self._emergency_wait = 0
        self._current_green = "none"

        # Seed initial queues so the agent has something to work with
        lo, hi = self._cfg["arrival_rate"]
        for d in DIRECTIONS:
            self._queues[d] = random.randint(lo, hi)

        if self._cfg["pedestrians"]:
            self._pedestrian_count = random.randint(0, 4)

        if self._cfg["emergencies"] and random.random() < 0.3:
            self._emergency_present = True
            self._emergency_direction = random.choice(DIRECTIONS)

        return self._build_observation(
            status_message=f"Traffic intersection ready - task={self._task}",
            reward=0.0,
            done=False,
        )

    # ------------------------------------------------------------------
    # Step
    # ------------------------------------------------------------------
    def step(self, action: HojaAction) -> HojaObservation:
        self._state.step_count += 1
        direction = action.direction.lower().strip()
        duration = max(5, min(60, action.duration_seconds))

        # Validate direction
        if direction not in DIRECTIONS:
            return self._build_observation(
                status_message=f"Invalid direction '{direction}'. Use: {DIRECTIONS}",
                reward=-1.0,
                done=False,
            )

        self._current_green = direction

        # --- 1. Process green direction: drain queue ----------------
        throughput = duration // 5  # ~1 car per 5 seconds
        cleared = min(self._queues[direction], throughput)
        self._queues[direction] -= cleared
        self._total_vehicles_cleared += cleared

        # Update state variable for current green to reflect the action instantly
        self._state.current_green = direction
        self._state.total_vehicles_cleared = self._total_vehicles_cleared

        # --- 2. Arrivals for ALL directions -------------------------
        lo, hi = self._cfg["arrival_rate"]
        for d in DIRECTIONS:
            arrivals = random.randint(lo, hi)
            self._queues[d] += arrivals

        # --- 3. Accumulate wait times for red directions ------------
        for d in DIRECTIONS:
            if d != direction:
                self._wait_times[d] += self._queues[d] * (duration / 60.0)
            else:
                # Green direction wait decreases
                self._wait_times[d] = max(0, self._wait_times[d] - cleared * 0.5)

        # --- 4. Pedestrians ----------------------------------------
        if self._cfg["pedestrians"]:
            # Some pedestrians cross during the signal change gap
            crossed = min(self._pedestrian_count, random.randint(1, 3))
            self._pedestrian_count -= crossed
            # New pedestrians arrive
            self._pedestrian_count += random.randint(0, 3)

        # --- 5. Emergency vehicles ---------------------------------
        emergency_bonus = 0.0
        emergency_penalty = 0.0

        if self._cfg["emergencies"]:
            # Possibly spawn a new emergency
            if not self._emergency_present and random.random() < 0.2:
                self._emergency_present = True
                self._emergency_direction = random.choice(DIRECTIONS)
                self._emergency_wait = 0

            if self._emergency_present:
                if direction == self._emergency_direction:
                    # Agent gave green to the emergency direction - cleared!
                    emergency_bonus = 5.0
                    self._emergency_present = False
                    self._emergency_direction = None
                    self._emergency_wait = 0
                else:
                    self._emergency_wait += 1
                    if self._emergency_wait > 2:
                        emergency_penalty = -3.0

        # --- 6. Compute reward (Normalized to [0.0, 1.0]) -------------
        # Base Reward (60%): Quality of traffic flow
        avg_wait = sum(self._wait_times.values()) / len(DIRECTIONS)
        wait_score = max(0.0, 1.0 - (avg_wait / 40.0))
        
        # Emergency Vehicle logic (30%):
        # 0.3 if no emergency vehicle is waiting.
        # 0.1 if an emergency vehicle is waiting (less than 2 steps).
        # 0.0 if an emergency vehicle has been waiting too long.
        emergency_score = 0.3
        if self._cfg["emergencies"] and self._emergency_present:
            if self._emergency_wait > 2:
                emergency_score = 0.0
            else:
                emergency_score = 0.1
        
        # Pedestrian/Queue Safety (10%):
        max_queue = max(self._queues.values())
        safety_penalty = min(0.1, (max_queue / 20.0) * 0.05 + (self._pedestrian_count / 20.0) * 0.05)
        safety_score = 0.1 - safety_penalty

        reward = (wait_score * 0.6) + emergency_score + safety_score
        reward = max(0.0, min(1.0, reward))

        done = self._state.step_count >= self._max_steps

        status_parts = [f"Green={direction} for {duration}s, cleared {cleared} cars"]
        if emergency_bonus > 0:
            status_parts.append("[EMERGENCY] Vehicle cleared!")
        if emergency_penalty < 0:
            status_parts.append("[WARNING] Emergency vehicle still waiting!")
        status_msg = " | ".join(status_parts)

        return self._build_observation(
            status_message=status_msg,
            reward=round(reward, 2),
            done=done,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _build_observation(self, status_message: str, reward: float, done: bool) -> HojaObservation:
        avg_wait = sum(self._wait_times.values()) / len(DIRECTIONS)
        return HojaObservation(
            status_message=status_message,
            current_green=self._current_green,
            time_of_day=self._cfg["time_of_day"],
            queue_north=self._queues["north"],
            queue_south=self._queues["south"],
            queue_east=self._queues["east"],
            queue_west=self._queues["west"],
            pedestrian_count=self._pedestrian_count,
            emergency_vehicle_present=self._emergency_present,
            emergency_vehicle_direction=self._emergency_direction,
            average_wait_time=round(avg_wait, 2),
            step_number=self._state.step_count,
            max_steps=self._max_steps,
            done=done,
            reward=reward,
            metadata={
                "task": self._task,
                "queues": dict(self._queues),
                "wait_times": {k: round(v, 2) for k, v in self._wait_times.items()},
                "emergency_wait_steps": self._emergency_wait,
            },
        )

    def _build_state(self, episode_id: str, step_count: int) -> HojaState:
        return HojaState(
            episode_id=episode_id,
            step_count=step_count,
            task_difficulty=self._task,
            time_of_day=self._cfg["time_of_day"],
            pedestrians_enabled=self._cfg["pedestrians"],
            emergencies_enabled=self._cfg["emergencies"],
            max_steps=self._max_steps,
            current_green=self._current_green,
            total_vehicles_cleared=self._total_vehicles_cleared
        )

    @property
    def state(self) -> HojaState:
        return self._state
