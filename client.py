# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""Hoja Traffic Signal Control Environment Client."""

from typing import Dict

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

from .app.models import HojaAction, HojaObservation, HojaState


class HojaEnv(
    EnvClient[HojaAction, HojaObservation, HojaState]
):
    """
    Client for the Hoja Traffic Signal Control Environment.

    Example with Docker:
        >>> client = HojaEnv.from_docker_image("hoja-app:latest")
        >>> try:
        ...     result = client.reset()
        ...     result = client.step(HojaAction(direction="north", duration_seconds=30))
        ... finally:
        ...     client.close()
    """

    def _step_payload(self, action: HojaAction) -> Dict:
        return {
            "direction": action.direction,
            "duration_seconds": action.duration_seconds,
        }

    def _parse_result(self, payload: Dict) -> StepResult[HojaObservation]:
        obs_data = payload.get("observation", {})
        observation = HojaObservation(
            status_message=obs_data.get("status_message", ""),
            current_green=obs_data.get("current_green", "none"),
            time_of_day=obs_data.get("time_of_day", "off_peak"),
            queue_north=obs_data.get("queue_north", 0),
            queue_south=obs_data.get("queue_south", 0),
            queue_east=obs_data.get("queue_east", 0),
            queue_west=obs_data.get("queue_west", 0),
            pedestrian_count=obs_data.get("pedestrian_count", 0),
            emergency_vehicle_present=obs_data.get("emergency_vehicle_present", False),
            emergency_vehicle_direction=obs_data.get("emergency_vehicle_direction"),
            average_wait_time=obs_data.get("average_wait_time", 0.0),
            step_number=obs_data.get("step_number", 0),
            max_steps=obs_data.get("max_steps", 25),
            done=payload.get("done", False),
            reward=payload.get("reward"),
            metadata=obs_data.get("metadata", {}),
        )

        return StepResult(
            observation=observation,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> State:
        return State(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
        )
