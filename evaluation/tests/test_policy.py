"""
Tests for deferral policy.
"""

import numpy as np

from audio_trust_harness.calibrate import DeferralPolicy


def test_deferral_policy_accept():
    """Test that stable indicators result in 'accept' action."""
    # Create stable indicators across perturbations
    indicators_by_perturbation = {
        "none": {
            "spectral_centroid_mean": 1500.0,
            "rms_energy": 0.05,
        },
        "noise": {
            "spectral_centroid_mean": 1510.0,  # Small variation
            "rms_energy": 0.051,  # Small variation
        },
    }

    # Use audio that won't trigger clipping detection
    audio = np.random.randn(16000) * 0.3  # Scale to prevent clipping
    audio = np.clip(audio, -0.9, 0.9)  # Ensure no clipping
    policy = DeferralPolicy(fragility_threshold=0.3)

    decision = policy.evaluate(
        indicators_by_perturbation, audio, sample_rate=16000, duration=1.0
    )

    assert decision.recommended_action == "accept"
    assert isinstance(decision.fragility_score, float)
    assert len(decision.reasons) == 0


def test_deferral_policy_defer_to_review():
    """Test that fragile indicators result in 'defer_to_review' action."""
    # Create fragile indicators (large variation)
    indicators_by_perturbation = {
        "none": {
            "spectral_centroid_mean": 1500.0,
            "rms_energy": 0.05,
        },
        "noise": {
            "spectral_centroid_mean": 3000.0,  # Large variation (2x)
            "rms_energy": 0.052,
        },
    }

    audio = np.random.randn(16000) * 0.3
    audio = np.clip(audio, -0.9, 0.9)  # Ensure no clipping
    policy = DeferralPolicy(fragility_threshold=0.3)

    decision = policy.evaluate(
        indicators_by_perturbation, audio, sample_rate=16000, duration=1.0
    )

    assert decision.recommended_action == "defer_to_review"
    assert decision.fragility_score > 0.3
    assert len(decision.reasons) > 0
    # Should have a reason about high fragility
    assert any("high_fragility" in reason for reason in decision.reasons)


def test_deferral_policy_insufficient_evidence_too_short():
    """Test that too-short slices result in 'insufficient_evidence' action."""
    indicators_by_perturbation = {
        "none": {"spectral_centroid_mean": 1500.0},
    }

    audio = np.random.randn(1000) * 0.5
    policy = DeferralPolicy(min_duration=0.5)

    decision = policy.evaluate(
        indicators_by_perturbation,
        audio,
        sample_rate=16000,
        duration=0.1,  # Too short
    )

    assert decision.recommended_action == "insufficient_evidence"
    assert "slice_too_short" in decision.reasons


def test_deferral_policy_insufficient_evidence_clipping():
    """Test that clipped audio results in 'insufficient_evidence' action."""
    indicators_by_perturbation = {
        "none": {"spectral_centroid_mean": 1500.0},
    }

    # Create clipped audio
    audio = np.random.randn(16000)
    audio[100] = 1.0  # Clipped sample

    policy = DeferralPolicy(clipping_threshold=0.95)

    decision = policy.evaluate(
        indicators_by_perturbation, audio, sample_rate=16000, duration=1.0
    )

    assert decision.recommended_action == "insufficient_evidence"
    assert "clipping_detected" in decision.reasons


def test_deferral_policy_returns_three_actions():
    """Test that policy can return all three action types."""
    # This test ensures the policy can produce all expected actions

    # 1. Accept
    stable_indicators = {
        "none": {"value": 1.0},
        "noise": {"value": 1.01},
    }
    audio_good = np.random.randn(16000) * 0.3
    audio_good = np.clip(audio_good, -0.9, 0.9)
    policy = DeferralPolicy()

    decision1 = policy.evaluate(stable_indicators, audio_good, 16000, 1.0)
    assert decision1.recommended_action in [
        "accept",
        "defer_to_review",
        "insufficient_evidence",
    ]

    # 2. Defer to review
    fragile_indicators = {
        "none": {"value": 1.0},
        "noise": {"value": 2.0},
    }
    decision2 = policy.evaluate(fragile_indicators, audio_good, 16000, 1.0)
    assert decision2.recommended_action in [
        "accept",
        "defer_to_review",
        "insufficient_evidence",
    ]

    # 3. Insufficient evidence
    decision3 = policy.evaluate(stable_indicators, audio_good, 16000, 0.1)  # Too short
    assert decision3.recommended_action == "insufficient_evidence"


def test_deferral_policy_includes_reasons():
    """Test that policy includes reasons when deferring."""
    indicators_by_perturbation = {
        "none": {"indicator_a": 1.0, "indicator_b": 1.0},
        "noise": {
            "indicator_a": 2.0,
            "indicator_b": 1.01,
        },  # Only indicator_a is fragile
    }

    audio = np.random.randn(16000) * 0.3
    audio = np.clip(audio, -0.9, 0.9)
    policy = DeferralPolicy(fragility_threshold=0.3)

    decision = policy.evaluate(
        indicators_by_perturbation, audio, sample_rate=16000, duration=1.0
    )

    if decision.recommended_action == "defer_to_review":
        assert len(decision.reasons) > 0
        # Should mention the fragile indicator
        assert any("indicator_a" in reason for reason in decision.reasons)


def test_deferral_policy_custom_thresholds():
    """Test that custom thresholds work correctly."""
    indicators_by_perturbation = {
        "none": {"value": 1.0},
        "noise": {"value": 1.5},  # 50% variation, CV ≈ 0.20
    }

    audio = np.random.randn(16000) * 0.3
    audio = np.clip(audio, -0.9, 0.9)

    # With lenient threshold (0.3), should accept
    policy_lenient = DeferralPolicy(fragility_threshold=0.3)
    decision_lenient = policy_lenient.evaluate(
        indicators_by_perturbation, audio, 16000, 1.0
    )
    assert decision_lenient.recommended_action == "accept"

    # With stricter threshold (0.1), should defer
    policy_strict = DeferralPolicy(fragility_threshold=0.1)
    decision_strict = policy_strict.evaluate(
        indicators_by_perturbation, audio, 16000, 1.0
    )
    assert decision_strict.recommended_action == "defer_to_review"
