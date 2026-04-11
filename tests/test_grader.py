# Copyright (c) Meta Platforms, Inc. and affiliates.

import pytest

from hoja.app.grader import Grader


def test_grader_perfect_episode():
    metrics = {
        "throughput_ratio": 1.0,
        "safety_score": 1.0,
        "avg_wait": 0.0,
        "emergency_cleared_ratio": 1.0
    }
    result = Grader().compute_score(metrics)
    assert result["total_score"] == 1.0
    assert result["breakdown"]["throughput"] == 0.35
    assert result["breakdown"]["safety"] == 0.25
    assert result["breakdown"]["efficiency"] == 0.20
    assert result["breakdown"]["emergency_priority"] == 0.20


def test_grader_worst_episode():
    metrics = {
        "throughput_ratio": 0.0,
        "safety_score": 0.0,
        "avg_wait": 60.0,
        "emergency_cleared_ratio": 0.0
    }
    result = Grader().compute_score(metrics)
    assert result["total_score"] == 0.0


@pytest.mark.parametrize("throughput,safety,wait,emergency,expected", [
    (1.0, 0.0, 60.0, 0.0, 0.35),
    (0.0, 1.0, 60.0, 0.0, 0.25),
    (0.0, 0.0, 0.0, 0.0, 0.20),
    (0.0, 0.0, 60.0, 1.0, 0.20),
    (0.5, 0.5, 30.0, 0.5, 0.50),
])
def test_grader_partial_scores(throughput, safety, wait, emergency, expected):
    metrics = {
        "throughput_ratio": throughput,
        "safety_score": safety,
        "avg_wait": wait,
        "emergency_cleared_ratio": emergency
    }
    result = Grader().compute_score(metrics)
    assert abs(result["total_score"] - expected) < 0.01


def test_grader_fuzz_bonus():
    metrics = {
        "throughput_ratio": 1.0,
        "safety_score": 1.0,
        "avg_wait": 0.0,
        "emergency_cleared_ratio": 1.0,
        "run_target_string": "optimal_flow_sequence"
    }
    result = Grader().compute_score(metrics)
    # The bonus allows score to naturally cap or slightly elevate before clamping
    assert result["total_score"] == 1.0
