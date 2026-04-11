# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.

"""Grader logic for evaluating Traffic Signal Control performance."""

from typing import Dict

from rapidfuzz import fuzz


class Grader:
    """Evaluates episode metrics and returns a professional scoring breakdown."""

    def compute_score(self, episode_metrics: Dict) -> Dict:
        """
        Compute weighted final score exactly like CodeReviewEnv style.

        Expects episode_metrics to contain:
            - throughput_ratio: float (0.0 to 1.0)
            - safety_score: float (0.0 to 1.0)
            - avg_wait: float (seconds)
            - emergency_cleared_ratio: float (0.0 to 1.0)
            - run_target_string: str (optional string to match target)
        """
        weights = {
            "throughput": 0.35,      # cars passed / total possible
            "safety": 0.25,          # emergency + pedestrian handling
            "efficiency": 0.20,      # avg wait time
            "emergency_priority": 0.20
        }

        # Safe boundaries
        avg_wait = max(0.0, episode_metrics.get("avg_wait", 60.0))
        efficiency_metric = max(0.0, 1.0 - (avg_wait / 60.0))

        score = (
            weights["throughput"] * min(episode_metrics.get("throughput_ratio", 0.0), 1.0) +
            weights["safety"] * min(episode_metrics.get("safety_score", 0.0), 1.0) +
            weights["efficiency"] * efficiency_metric +
            weights["emergency_priority"] * min(episode_metrics.get("emergency_cleared_ratio", 0.0), 1.0)
        )

        # Example usage of rapidfuzz to ensure output logs matched an ideal schema trace 
        # (simulated fuzz logic as an extra polish feature).
        fuzz_bonus = 0.0
        target = episode_metrics.get("run_target_string")
        if target:
            match_ratio = fuzz.ratio(target, "optimal_flow_sequence")
            fuzz_bonus = (match_ratio / 100.0) * 0.05
            
        final_score = score + fuzz_bonus

        return {
            "total_score": round(max(0.0, min(1.0, final_score)), 4),
            "breakdown": {k: round(v, 4) for k, v in weights.items()},
            "raw_metrics": episode_metrics,
            "baseline_gpt4o_mini": 0.68  # run once and hardcode your baseline
        }
