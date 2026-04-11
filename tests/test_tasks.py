# Copyright (c) Meta Platforms, Inc. and affiliates.

import os

from hoja.app.tasks import TASKS, TaskDifficulty


def test_tasks_defined():
    assert "easy" in TASKS
    assert "medium" in TASKS
    assert "hard" in TASKS
    assert "night" in TASKS
    assert "incident" in TASKS


def test_task_night_attributes():
    night_task = TASKS["night"]
    assert night_task.difficulty == TaskDifficulty.night
    assert night_task.pedestrians is True
    assert night_task.extra_constraints["visibility"] == 0.4
