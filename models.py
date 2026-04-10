# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Data models for the Hoja Traffic Signal Control Environment.

The agent controls a 4-way intersection by choosing which direction
gets a green signal and for how long.
"""

from typing import Optional

from openenv.core.env_server.types import Action, Observation, State
from pydantic import Field


class HojaState(State):
    """Configuration and global state for the Hoja traffic environment."""
    task_difficulty: str = Field(default="easy", description="Current difficulty setting")
    time_of_day: str = Field(default="off_peak", description="off_peak, normal, or peak")
    pedestrians_enabled: bool = Field(default=False, description="Whether pedestrians can appear")
    emergencies_enabled: bool = Field(default=False, description="Whether emergency vehicles can appear")
    max_steps: int = Field(default=25, description="Total steps in the episode")
    current_green: str = Field(default="none", description="Direction currently green")
    total_vehicles_cleared: int = Field(default=0, description="Total vehicles that have passed through the intersection")


class HojaAction(Action):
    """Action for the Hoja traffic environment — change the traffic signal."""

    direction: str = Field(
        ...,
        description="Direction to give green signal: 'north', 'south', 'east', or 'west'",
    )
    duration_seconds: int = Field(
        ...,
        description="How long to keep the signal green (5–60 seconds)",
        ge=5,
        le=60,
    )


class HojaObservation(Observation):
    """Observation from the Hoja traffic environment."""

    status_message: str = Field(default="", description="Human-readable status")
    current_green: str = Field(default="none", description="Direction currently green")
    time_of_day: str = Field(default="off_peak", description="off_peak, normal, or peak")
    queue_north: int = Field(default=0, description="Cars queued going north")
    queue_south: int = Field(default=0, description="Cars queued going south")
    queue_east: int = Field(default=0, description="Cars queued going east")
    queue_west: int = Field(default=0, description="Cars queued going west")
    pedestrian_count: int = Field(default=0, description="Pedestrians waiting to cross")
    emergency_vehicle_present: bool = Field(default=False, description="Emergency vehicle waiting?")
    emergency_vehicle_direction: Optional[str] = Field(default=None, description="Direction of emergency vehicle")
    average_wait_time: float = Field(default=0.0, description="Average wait time across all directions")
    step_number: int = Field(default=0, description="Current step in the episode")
    max_steps: int = Field(default=25, description="Total steps in the episode")
