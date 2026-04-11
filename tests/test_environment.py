# Copyright (c) Meta Platforms, Inc. and affiliates.

import pytest

from hoja.app.models import HojaAction
from hoja.app.environment import HojaEnvironment


def test_reset(env):
    obs = env.reset()
    assert obs.status_message.startswith("Traffic intersection ready")
    assert obs.reward == 0.0
    assert not obs.done
    assert env._total_vehicles_cleared == 0


def test_step_valid_direction(env):
    env.reset()
    action = HojaAction(direction="north", duration_seconds=10)
    obs = env.step(action)
    assert obs.current_green == "north"
    assert env._total_vehicles_cleared >= 0
    assert not obs.done


def test_step_invalid_direction(env):
    env.reset()
    action = HojaAction(direction="invalid", duration_seconds=10)
    obs = env.step(action)
    assert "Invalid direction" in obs.status_message
    assert obs.reward == -1.0


def test_episode_done(env):
    env.reset()
    action = HojaAction(direction="north", duration_seconds=5)
    
    # Run to max_steps
    for _ in range(env._max_steps - 1):
        obs = env.step(action)
        assert not obs.done
        
    obs = env.step(action)
    assert obs.done
    
    # Metadata should contain grader payload at done=True
    assert "grader_report" in obs.metadata
    assert "total_score" in obs.metadata["grader_report"]
