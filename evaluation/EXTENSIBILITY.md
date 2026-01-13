# Extensibility Guide

This guide explains how to extend the Audio Trust Harness framework with custom indicators, perturbations, and evaluation policies.

## Philosophy

The Audio Trust Harness is designed as a **methodology framework**, not a complete detection system. The core framework provides:

- **Evaluation pipeline**: Loading, slicing, perturbing, analyzing, and auditing audio
- **Plugin interfaces**: Well-defined interfaces for custom components
- **Configuration system**: External YAML files for parameter tuning
- **Audit trail generation**: Reproducible, versioned output

**You provide:**
- **Custom indicators**: Your proprietary acoustic features and analysis algorithms
- **Custom perturbations**: Domain-specific stress tests and transformations
- **Tuned parameters**: Thresholds and configurations optimized for your use case
- **Domain logic**: Specialized deferral policies for your application

## Quick Start: Customizing Existing Components

### 1. Customize Parameters via Configuration

The easiest way to customize behavior is through YAML configuration files in `config/`:

```yaml
# config/perturbations.yaml
noise:
  snr_db: 15.0  # More aggressive noise for stress testing

codec_stub:
  cutoff_hz: 8000.0  # Wider bandwidth simulation
  bits: 12  # Higher quality quantization
```

```yaml
# config/thresholds.yaml
deferral_policy:
  fragility_threshold: 0.4  # More tolerant for music domain
  clipping_threshold: 0.90  # Stricter clipping detection
```

See [Configuration Guide](config/README.md) for full documentation.

### 2. Override Parameters via CLI

For quick experiments, override parameters at runtime:

```bash
python -m audio_trust_harness run \
  --audio sample.wav \
  --out audit.jsonl \
  --fragility-threshold 0.4 \
  --clipping-threshold 0.90
```

### 3. Use Environment Variables for Custom Config Directory

Point to a private configuration directory:

```bash
# Set environment variable to use custom config directory
export AUDIO_TRUST_CONFIG_DIR=/path/to/config-private

# Run with private configs
python -m audio_trust_harness run --audio sample.wav --out audit.jsonl

# Or inline for a single command
AUDIO_TRUST_CONFIG_DIR=./config-private python -m audio_trust_harness run \
  --audio sample.wav \
  --out audit.jsonl
```

This allows you to:
- Keep proprietary configs in a separate private repository
- Switch between different config sets (development, staging, production)
- Avoid modifying the default `config/` directory

## Adding Custom Indicators

Custom indicators allow you to integrate proprietary acoustic features.

### Step 1: Understand the Interface

Indicators are functions that take audio and return a dictionary of feature values:

```python
def compute_indicators(audio: np.ndarray, sample_rate: int) -> dict[str, float]:
    """
    Compute acoustic indicators from audio.
    
    Args:
        audio: Audio samples as numpy array (shape: [samples])
        sample_rate: Sample rate in Hz
        
    Returns:
        Dictionary mapping indicator names to values
    """
    indicators = {}
    
    # Example: Compute your proprietary features here
    indicators["my_custom_feature"] = compute_custom_feature(audio, sample_rate)
    
    return indicators
```

### Step 2: Implement Your Indicator

Create a new file `src/audio_trust_harness/indicators/custom.py`:

```python
"""
Custom proprietary indicators.
"""

import numpy as np
from audio_trust_harness.config import STFT_CONFIG


def compute_custom_indicators(audio: np.ndarray, sample_rate: int) -> dict[str, float]:
    """
    Compute proprietary acoustic indicators.
    
    This is where you integrate your domain-specific features.
    """
    indicators = {}
    
    # Example: Harmonic-to-noise ratio
    indicators["hnr"] = compute_hnr(audio, sample_rate)
    
    # Example: Prosody features for speech
    indicators["f0_mean"] = compute_f0_mean(audio, sample_rate)
    indicators["f0_std"] = compute_f0_std(audio, sample_rate)
    
    # Example: Domain-specific energy patterns
    indicators["energy_envelope_slope"] = compute_energy_slope(audio)
    
    return indicators


def compute_hnr(audio: np.ndarray, sample_rate: int) -> float:
    """
    Compute harmonic-to-noise ratio.
    
    Replace this stub with your proprietary implementation.
    """
    # TODO: Implement your HNR algorithm
    return 10.0  # Placeholder


def compute_f0_mean(audio: np.ndarray, sample_rate: int) -> float:
    """
    Compute mean fundamental frequency.
    
    Replace this stub with your proprietary implementation.
    """
    # TODO: Implement your F0 estimation
    return 150.0  # Placeholder


def compute_f0_std(audio: np.ndarray, sample_rate: int) -> float:
    """
    Compute standard deviation of fundamental frequency.
    
    Replace this stub with your proprietary implementation.
    """
    # TODO: Implement your F0 variation metric
    return 20.0  # Placeholder


def compute_energy_slope(audio: np.ndarray) -> float:
    """
    Compute energy envelope slope.
    
    Replace this stub with your proprietary implementation.
    """
    # TODO: Implement your energy analysis
    return 0.5  # Placeholder
```

### Step 3: Configure Your Indicators

Add configuration for your indicators in `config/indicators.yaml`:

```yaml
# Custom indicator configuration
custom:
  # Parameters specific to your indicators
  hnr_window_size: 0.025  # 25ms window
  f0_min: 75.0  # Min F0 in Hz
  f0_max: 500.0  # Max F0 in Hz
```

### Step 4: Integrate into Pipeline

Modify `src/audio_trust_harness/batch.py` to include your indicators:

```python
from audio_trust_harness.indicators import spectral, temporal
from audio_trust_harness.indicators import custom  # Import your module

# In process_slice_with_perturbations():
indicators = {}

# Existing indicators
indicators.update(spectral.compute_spectral_indicators(perturbed, sample_rate))
indicators.update(temporal.compute_temporal_indicators(perturbed, sample_rate))

# Add your custom indicators
indicators.update(custom.compute_custom_indicators(perturbed, sample_rate))
```

## Adding Custom Perturbations

Custom perturbations allow you to test indicators against domain-specific transformations.

### Step 1: Create Perturbation Class

Create a new file `src/audio_trust_harness/perturbations/custom.py`:

```python
"""
Custom domain-specific perturbations.
"""

import numpy as np
from audio_trust_harness.perturb import Perturbation


class RoomReverbPerturbation(Perturbation):
    """
    Simulate room acoustics and reverberation.
    
    This is a proprietary perturbation for testing speech/music in different acoustic environments.
    """
    
    def __init__(self, room_size: str = "medium", rt60: float = 0.5, seed: int = 1337):
        super().__init__("room_reverb", seed)
        self.room_size = room_size
        self.rt60 = rt60  # Reverberation time in seconds
    
    def apply(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """
        Apply room reverberation to audio.
        
        Replace this stub with your proprietary implementation.
        """
        # TODO: Implement your room simulation
        # This is where you'd integrate a proper reverb algorithm
        
        # Placeholder: Simple exponential decay convolution
        reverb_length = int(self.rt60 * sample_rate)
        reverb_ir = np.exp(-np.arange(reverb_length) / (self.rt60 * sample_rate))
        reverb_ir *= self.rng.randn(reverb_length)
        
        # Convolve (simplified)
        reverbed = np.convolve(audio, reverb_ir, mode='same')
        
        # Normalize
        reverbed = reverbed / np.max(np.abs(reverbed))
        
        return reverbed.astype(np.float32)
    
    def get_params(self) -> dict:
        return {
            "room_size": self.room_size,
            "rt60": self.rt60,
            "seed": self.seed
        }


class MicrophoneSimPerturbation(Perturbation):
    """
    Simulate microphone frequency response.
    """
    
    def __init__(self, mic_type: str = "condenser", seed: int = 1337):
        super().__init__(f"mic_{mic_type}", seed)
        self.mic_type = mic_type
    
    def apply(self, audio: np.ndarray, sample_rate: int) -> np.ndarray:
        """
        Apply microphone frequency response.
        
        Replace this stub with your proprietary implementation.
        """
        # TODO: Implement your microphone simulation
        # This is where you'd apply frequency response curves
        
        # Placeholder: Identity
        return audio.copy()
    
    def get_params(self) -> dict:
        return {
            "mic_type": self.mic_type,
            "seed": self.seed
        }
```

### Step 2: Configure Your Perturbations

Add configuration in `config/perturbations.yaml`:

```yaml
# Custom perturbation configuration
room_reverb:
  room_size: "medium"
  rt60: 0.5  # Reverberation time in seconds

mic_condenser:
  mic_type: "condenser"

mic_dynamic:
  mic_type: "dynamic"
```

### Step 3: Register Perturbations

Update the perturbation factory in `src/audio_trust_harness/perturb.py`:

```python
from audio_trust_harness.perturbations import custom

def get_perturbation(name: str, seed: int = 1337, **kwargs) -> Perturbation:
    # ... existing perturbations ...
    
    # Add your custom perturbations
    elif name == "room_reverb":
        defaults = get_perturbation_defaults("room_reverb")
        room_size = kwargs.get("room_size", defaults.get("room_size", "medium"))
        rt60 = kwargs.get("rt60", defaults.get("rt60", 0.5))
        return custom.RoomReverbPerturbation(room_size=room_size, rt60=rt60, seed=seed)
    
    elif name.startswith("mic_"):
        mic_type = name.split("_")[1]
        return custom.MicrophoneSimPerturbation(mic_type=mic_type, seed=seed)
    
    else:
        raise ValueError(f"Unknown perturbation: {name}")
```

### Step 4: Use Your Perturbations

```bash
python -m audio_trust_harness run \
  --audio sample.wav \
  --out audit.jsonl \
  --perturbations none,room_reverb,mic_condenser
```

## Custom Deferral Policies

For advanced use cases, you may need custom deferral logic.

### Step 1: Understand the Policy Interface

The deferral policy evaluates indicators and produces a decision:

```python
from audio_trust_harness.calibrate.policy import DeferralDecision

class CustomDeferralPolicy:
    def evaluate(
        self,
        indicators_by_perturbation: dict[str, dict[str, float]],
        audio_data: np.ndarray,
        sample_rate: int,
        duration: float,
    ) -> DeferralDecision:
        """
        Evaluate indicators and produce deferral decision.
        
        Args:
            indicators_by_perturbation: Dict of {perturbation_name: {indicator_name: value}}
            audio_data: Raw audio samples
            sample_rate: Sample rate in Hz
            duration: Duration in seconds
            
        Returns:
            DeferralDecision with action, fragility score, and reasons
        """
        # Your custom logic here
        pass
```

### Step 2: Implement Custom Logic

Create `src/audio_trust_harness/calibrate/custom_policy.py`:

```python
"""
Custom domain-specific deferral policy.
"""

import numpy as np
from audio_trust_harness.calibrate.policy import DeferralDecision, DeferralPolicy


class SpeechDeferralPolicy(DeferralPolicy):
    """
    Deferral policy optimized for speech audio.
    
    Implements domain-specific rules for speech authenticity evaluation.
    """
    
    def evaluate(
        self,
        indicators_by_perturbation: dict[str, dict[str, float]],
        audio_data: np.ndarray,
        sample_rate: int,
        duration: float,
    ) -> DeferralDecision:
        """
        Evaluate speech audio with custom rules.
        """
        # Start with base policy evaluation
        base_decision = super().evaluate(
            indicators_by_perturbation, audio_data, sample_rate, duration
        )
        
        # Add custom speech-specific checks
        reasons = list(base_decision.reasons)
        
        # Example: Check for unnatural prosody
        if self._has_unnatural_prosody(indicators_by_perturbation):
            reasons.append("unnatural_prosody_detected")
        
        # Example: Check for voice quality issues
        if self._has_voice_quality_issues(indicators_by_perturbation):
            reasons.append("voice_quality_issue")
        
        # Custom decision logic
        if any("unnatural" in r or "voice_quality" in r for r in reasons):
            action = "defer_to_review"
        else:
            action = base_decision.recommended_action
        
        return DeferralDecision(
            recommended_action=action,
            fragility_score=base_decision.fragility_score,
            reasons=reasons
        )
    
    def _has_unnatural_prosody(self, indicators: dict) -> bool:
        """
        Check for unnatural prosody patterns.
        
        Replace with your proprietary prosody analysis.
        """
        # TODO: Implement your prosody check
        return False
    
    def _has_voice_quality_issues(self, indicators: dict) -> bool:
        """
        Check for voice quality issues.
        
        Replace with your proprietary voice quality metrics.
        """
        # TODO: Implement your voice quality check
        return False
```

## Best Practices

### 1. Separation of Concerns

Keep **evaluation methodology** (framework) separate from **detection logic** (your indicators):

- ✅ Framework: Slicing, perturbation application, audit trail generation
- ✅ Your code: Indicator computation, domain-specific thresholds, proprietary algorithms

### 2. Configuration Over Code

Prefer external configuration for tunable parameters:

- ✅ Thresholds → `config/thresholds.yaml`
- ✅ Perturbation params → `config/perturbations.yaml`
- ✅ Indicator params → `config/indicators.yaml`
- ❌ Hardcoded magic numbers in proprietary indicator code

### 3. Version Your Configurations

Track configuration files in version control separately from code:

```bash
# Private repo for proprietary configs
git clone https://github.com/yourorg/audio-trust-configs-private.git config-private/

# Use private configs
export AUDIO_TRUST_CONFIG_DIR=config-private/
python -m audio_trust_harness run --audio sample.wav --out audit.jsonl
```

### 4. Document Your Indicators

When adding proprietary indicators, document:

- **Purpose**: What does this indicator measure?
- **Range**: What are typical values?
- **Sensitivity**: How does it respond to perturbations?
- **Limitations**: Known failure modes or edge cases?

Example:

```python
def compute_voice_naturalness_score(audio: np.ndarray, sample_rate: int) -> float:
    """
    Compute proprietary voice naturalness score.
    
    Purpose:
        Measures how natural the voice quality sounds based on prosodic features
        and spectral characteristics specific to human speech production.
    
    Range:
        0.0 to 1.0, where 1.0 = most natural, 0.0 = least natural
    
    Sensitivity:
        - Robust to additive noise (SNR > 15dB)
        - Sensitive to codec artifacts below 32kbps
        - Sensitive to pitch manipulation > ±3 semitones
    
    Limitations:
        - Requires speech audio (not suitable for music)
        - Minimum duration: 1 second
        - Optimized for English; may need tuning for other languages
    """
    # Your proprietary implementation here
    pass
```

### 5. Test Custom Components

Write tests for your custom indicators and perturbations:

```python
# tests/test_custom_indicators.py
import numpy as np
from audio_trust_harness.indicators.custom import compute_custom_indicators


def test_custom_indicator_deterministic():
    """Custom indicators should be deterministic."""
    audio = np.random.randn(16000)
    sample_rate = 16000
    
    result1 = compute_custom_indicators(audio, sample_rate)
    result2 = compute_custom_indicators(audio, sample_rate)
    
    assert result1 == result2


def test_custom_indicator_valid_range():
    """Custom indicators should return values in expected range."""
    audio = np.random.randn(16000) * 0.5
    sample_rate = 16000
    
    result = compute_custom_indicators(audio, sample_rate)
    
    # Example: Voice naturalness should be in [0, 1]
    assert 0.0 <= result["voice_naturalness"] <= 1.0
```

## Security Considerations

When integrating proprietary indicators:

### 1. Protect Proprietary Algorithms

- ❌ Do NOT commit proprietary indicator implementations to public repos
- ✅ Keep proprietary code in private repos or separate modules
- ✅ Use interfaces and plugin patterns to separate public framework from private implementation

### 2. Sanitize Audit Logs

Be careful about what gets logged:

```python
def compute_proprietary_indicator(audio: np.ndarray) -> dict[str, float]:
    # Internal calculations that reveal proprietary logic
    internal_features = compute_secret_features(audio)
    
    # Only expose summary metrics in audit logs
    return {
        "proprietary_score": internal_features.summary_score,
        # Do NOT log: internal_features.feature_vector (reveals algorithm details)
    }
```

### 3. Avoid Leaking Thresholds

When tuning thresholds on proprietary data:

- ✅ Store tuned thresholds in private config files
- ✅ Use environment-specific config directories
- ❌ Do NOT commit production-tuned thresholds to public repos

```bash
# Public repo: Generic example thresholds
config/thresholds.yaml  # fragility_threshold: 0.3 (example)

# Private repo: Production-tuned thresholds
config-private/thresholds.yaml  # fragility_threshold: 0.27 (tuned on production data)
```

## Plugin System (Future)

A formal plugin system is planned for v0.3:

- **Dynamic loading**: Load indicators/perturbations from external modules
- **Plugin registry**: Discover and register plugins automatically
- **Plugin metadata**: Version, dependencies, license information
- **Plugin validation**: Type checking and interface compliance

Until then, use the patterns described above for extending the framework.

## Getting Help

- **Configuration questions**: See [Configuration Guide](config/README.md)
- **Design decisions**: See [NOTES.md](NOTES.md)
- **General usage**: See [README.md](README.md)
- **Bug reports**: Open an issue on GitHub

## Contributing Extensions

If you develop generic, non-proprietary indicators or perturbations that would benefit the community:

1. **Document thoroughly**: Add docstrings and usage examples
2. **Add tests**: Ensure reliability and correctness
3. **Use generic parameters**: Make them configurable for different use cases
4. **Submit PR**: Contribute back to the framework

Remember: The framework is the methodology; your extensions are the experiments.
