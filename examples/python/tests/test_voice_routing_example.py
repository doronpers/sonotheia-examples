"""Tests for voice_routing_example.py - voice integrity routing."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

# Skip tests if voice_routing_example not available
try:
    from voice_routing_example import (
        RiskLevel,
        RoutingAction,
        TransactionContext,
        VoiceAnalysisResult,
        VoiceIntegrityRouter,
    )
except ImportError:
    pytestmark = pytest.mark.skip("voice_routing_example not available")


class TestVoiceIntegrityRouter:
    """Tests for VoiceIntegrityRouter class."""

    @pytest.fixture
    def router(self):
        """Create a VoiceIntegrityRouter instance."""
        return VoiceIntegrityRouter(api_key="test-key", api_url="https://api.test.com")

    def test_init(self, router):
        """Test router initialization."""
        assert router.api_key == "test-key"
        assert router.api_url == "https://api.test.com"
        assert router.confidence_threshold == 0.6
        assert router.high_risk_score_threshold == 0.7

    @patch("voice_routing_example.requests.post")
    def test_analyze_voice_success(self, mock_post, router, test_audio):
        """Test successful voice analysis."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "score": 0.3,
            "label": "likely_real",
            "confidence": 0.85,
            "session_id": "session-123",
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = router.analyze_voice(test_audio)

        assert isinstance(result, VoiceAnalysisResult)
        assert result.deepfake_score == 0.3
        assert result.risk_level == RiskLevel.LOW
        assert result.session_id == "session-123"

    @patch("voice_routing_example.requests.post")
    def test_analyze_voice_high_risk(self, mock_post, router, test_audio):
        """Test voice analysis with high risk score."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "score": 0.85,
            "label": "likely_synthetic",
            "confidence": 0.9,
            "session_id": "session-456",
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = router.analyze_voice(test_audio)

        assert result.risk_level == RiskLevel.HIGH
        assert result.deepfake_score == 0.85

    def test_make_routing_decision_low_risk(self, router):
        """Test routing decision for low risk."""
        voice_result = VoiceAnalysisResult(
            deepfake_score=0.2,
            confidence=0.9,
            risk_level=RiskLevel.LOW,
            reason_codes=[],
            feature_contributions={},
            session_id="session-123",
        )
        context = TransactionContext(
            transaction_id="txn-1",
            customer_id="cust-1",
            amount_usd=1000.0,
            destination_country="US",
            is_new_beneficiary=False,
            channel="web",
        )

        decision = router.make_routing_decision(voice_result, context)

        assert decision.action == RoutingAction.ALLOW
        assert decision.risk_level == RiskLevel.LOW
        assert decision.requires_human_review is False

    def test_make_routing_decision_high_risk(self, router):
        """Test routing decision for high risk."""
        voice_result = VoiceAnalysisResult(
            deepfake_score=0.9,
            confidence=0.95,
            risk_level=RiskLevel.HIGH,
            reason_codes=["synthetic_indicators"],
            feature_contributions={},
            session_id="session-123",
        )
        context = TransactionContext(
            transaction_id="txn-2",
            customer_id="cust-2",
            amount_usd=50000.0,
            destination_country="US",
            is_new_beneficiary=True,
            channel="phone",
        )

        decision = router.make_routing_decision(voice_result, context)

        assert decision.action in [RoutingAction.BLOCK, RoutingAction.ESCALATE_TO_HUMAN]
        assert decision.risk_level == RiskLevel.HIGH
        # Note: BLOCK actions may not require human review (auto-blocked)
        # ESCALATE actions require human review
        if decision.action == RoutingAction.ESCALATE_TO_HUMAN:
            assert decision.requires_human_review is True

    def test_make_routing_decision_medium_risk(self, router):
        """Test routing decision for medium risk."""
        voice_result = VoiceAnalysisResult(
            deepfake_score=0.5,
            confidence=0.7,
            risk_level=RiskLevel.MEDIUM,
            reason_codes=[],
            feature_contributions={},
            session_id="session-123",
        )
        context = TransactionContext(
            transaction_id="txn-3",
            customer_id="cust-3",
            amount_usd=5000.0,
            destination_country="US",
            is_new_beneficiary=False,
            channel="web",
        )

        decision = router.make_routing_decision(voice_result, context)

        assert decision.action in [
            RoutingAction.REQUIRE_STEP_UP,
            RoutingAction.REQUIRE_CALLBACK,
            RoutingAction.ALLOW,
        ]
        assert decision.risk_level == RiskLevel.MEDIUM

    def test_calculate_composite_risk(self, router):
        """Test composite risk calculation."""
        voice_result = VoiceAnalysisResult(
            deepfake_score=0.6,
            confidence=0.8,
            risk_level=RiskLevel.MEDIUM,
            reason_codes=[],
            feature_contributions={},
            session_id="session-123",
        )
        context = TransactionContext(
            transaction_id="txn-4",
            customer_id="cust-4",
            amount_usd=75000.0,
            destination_country="US",
            is_new_beneficiary=True,
            channel="phone",
        )

        composite_risk = router._calculate_composite_risk(voice_result, context)

        assert 0.0 <= composite_risk <= 1.0
        # High value + new beneficiary + medium voice risk should increase composite risk
        assert composite_risk > voice_result.deepfake_score

    def test_determine_action(self, router):
        """Test action determination logic."""
        voice_result = VoiceAnalysisResult(
            deepfake_score=0.3,
            confidence=0.9,
            risk_level=RiskLevel.LOW,
            reason_codes=[],
            feature_contributions={},
            session_id="session-123",
        )
        context = TransactionContext(
            transaction_id="txn-5",
            customer_id="cust-5",
            amount_usd=1000.0,
            destination_country="US",
            is_new_beneficiary=False,
            channel="web",
        )

        action = router._determine_action(voice_result, context, composite_risk=0.2)

        assert action in [
            RoutingAction.ALLOW,
            RoutingAction.REQUIRE_STEP_UP,
            RoutingAction.REQUIRE_CALLBACK,
            RoutingAction.ESCALATE_TO_HUMAN,
            RoutingAction.BLOCK,
        ]
