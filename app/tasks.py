# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""Task definitions for the Hoja traffic environment."""

from enum import Enum
from typing import Dict, Optional, Tuple

from pydantic import BaseModel


class TaskDifficulty(str, Enum):
    """Enumeration of traffic task difficulties."""
    easy = "easy"
    medium = "medium"
    hard = "hard"
    night = "night"
    incident = "incident"


class TrafficTask(BaseModel):
    """Configuration schema for a Hoja traffic task."""
    name: str
    difficulty: TaskDifficulty
    description: str
    time_of_day: str
    max_steps: int = 50
    arrival_rate: Tuple[int, int]  # min/max cars arriving per step per direction
    pedestrians: bool
    emergencies: bool
    extra_constraints: Optional[Dict] = None


TASKS = {
    "easy": TrafficTask(
        name="Easy Traffic",
        difficulty=TaskDifficulty.easy,
        description="Off-peak, low traffic, no pedestrians or emergencies.",
        time_of_day="off_peak",
        arrival_rate=(0, 3),
        pedestrians=False,
        emergencies=False,
        max_steps=25,
    ),
    "medium": TrafficTask(
        name="Medium Traffic",
        difficulty=TaskDifficulty.medium,
        description="Normal traffic with pedestrian crossings.",
        time_of_day="normal",
        arrival_rate=(1, 5),
        pedestrians=True,
        emergencies=False,
        max_steps=25,
    ),
    "hard": TrafficTask(
        name="Hard Traffic",
        difficulty=TaskDifficulty.hard,
        description="Peak-hour traffic with emergency vehicle priority.",
        time_of_day="peak",
        arrival_rate=(3, 8),
        pedestrians=True,
        emergencies=True,
        max_steps=25,
    ),
    "night": TrafficTask(
        name="Night Mode",
        difficulty=TaskDifficulty.night,
        description="Low visibility + higher pedestrian risk.",
        time_of_day="night",
        arrival_rate=(0, 4),
        pedestrians=True,  # Represent pedestrian risk
        emergencies=True,  # 0.3 probability mapped below
        extra_constraints={"visibility": 0.4},
        max_steps=25,
    ),
    "incident": TrafficTask(
        name="Road Incident",
        difficulty=TaskDifficulty.incident,
        description="One lane blocked + emergency vehicles.",
        time_of_day="peak",
        arrival_rate=(2, 9),
        pedestrians=True,
        emergencies=True,
        extra_constraints={"blocked_lane": "east"},
        max_steps=25,
    ),
}
