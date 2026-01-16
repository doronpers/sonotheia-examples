# Developer Notes

## Purpose
Technical implementation details, design decisions, and future considerations for Audio Trust Harness developers and contributors.

## Design Rationale

### Why JSONL for Audit Logs?
- Easy to stream and append
- Each line is self-contained (no need to parse entire file)
- Standard format for audit trails
- Supports both per-record and batch processing

### Why Rules-Based Deferral?
- **Transparent**: Every decision is traceable to specific thresholds
- **Falsifiable**: Easy to test and validate behavior
- **No ML complexity**: No training data, model updates, or bias concerns
- **Incremental improvement**: Thresholds can be tuned based on domain knowledge

### Why Deferral Signals (Not Binary Labels)?
- Audio authenticity is context-dependent
- Preserves uncertainty rather than false confidence
- Enables human-in-the-loop workflows
- Avoids oversimplified "real/fake" dichotomy

### Perturbation Philosophy

All perturbations are deterministic (seedable) for reproducibility. The included implementations are deliberately simple approximations with **example parameters**, not production-quality transformations. This design choice:

1. **Reduces dependencies** - No complex codec libraries required for basic testing
2. **Enables rapid prototyping** - Test indicator concepts quickly
3. **Demonstrates methodology** - Shows how to evaluate indicators under stress
4. **Encourages customization** - Users replace stubs with domain-specific perturbations

**For production evaluation:**
- Use real codecs (Opus, MP3, AAC) instead of `codec_stub`
- Use librosa/rubberband for proper pitch/time manipulation
- Integrate domain-specific perturbations (room acoustics, microphone effects, etc.)
- Tune parameters based on expected attack scenarios

All perturbation parameters are configurable via `config/perturbations.yaml`. See [Configuration Guide](config/README.md).

## Technical Decisions

### Audio Processing
- **Target format**: 16kHz mono WAV
- **Resampling**: scipy.signal.resample (adequate for stress testing)
- **FFT**: Default Hann window (standard for spectral analysis)
- **Frame size**: Dynamically computed based on sample rate

### Fragility Computation

Coefficient of Variation (CV) = std / |mean| for each indicator across perturbations.

**Why CV?**
- Simple, interpretable measure of relative stability
- Scale-independent (works for indicators with different units)
- Well-understood statistical metric
- Easy to explain and validate

**Alternatives considered:**
- Absolute standard deviation (scale-dependent, harder to set universal thresholds)
- Interquartile range (less sensitive to outliers, but harder to interpret)
- Relative entropy (complex, requires distributional assumptions)

**For custom indicators:** CV may not be appropriate for all indicator types. Users can implement custom fragility metrics in the deferral policy. See `src/audio_trust_harness/calibrate/policy.py`.

### Threshold Defaults

All threshold values are externalized in `config/thresholds.yaml` and serve as **example starting points** for research and exploration. These are not production-tuned values.

- **Fragility**: CV > 0.3 (30% variation triggers deferral)
  - Example starting point for general audio
  - Music may need higher thresholds due to natural dynamic variation
  - Speech may tolerate lower thresholds
  - **Users should tune based on domain-specific requirements**

- **Clipping**: Peak amplitude > 0.95 (likely distorted)
  - Conservative threshold to catch obvious distortion
  - Adjust based on your audio quality standards

- **Min duration**: 0.5s (insufficient for reliable analysis)
  - Based on minimum STFT window requirements
  - Shorter durations lack spectral resolution

- **Temporal consistency**: Relative change > 0.5 (50% change between slices indicates inconsistency)
  - Conservative to avoid false positives from natural variation
  - May need adjustment for music vs. speech

**Rationale**: These values represent reasonable defaults for exploring the framework. Production systems should conduct empirical tuning on domain-specific datasets to find optimal values for their use case.

See `config/thresholds.yaml` for current values and customization options.

### Cross-Slice Consistency
Evaluates temporal coherence by measuring relative changes in indicators between consecutive slices. Uses baseline ("none" perturbation) indicators to avoid perturbation artifacts. Detects abrupt changes that might indicate splicing or manipulation. Conservative threshold (50%) avoids false positives from natural audio variation.

### Batch Processing
Supports both serial and parallel processing of audio slices. Parallel processing uses Python's multiprocessing module to process slices concurrently, significantly reducing processing time for large audio files. Maintains determinism through consistent seeding. Workers parameter defaults to CPU count but can be configured.

## Extensibility

### CLI-Configurable Thresholds
All deferral policy thresholds can be customized via CLI:
- `--fragility-threshold`: CV threshold for fragility detection (default: 0.3)
- `--clipping-threshold`: Amplitude threshold for clipping (default: 0.95)
- `--min-duration`: Minimum slice duration for valid analysis (default: 0.5s)
## Future Work

### Configuration & Extensibility ✓ (v0.2)
- External configuration files (YAML) ✓
- CLI-configurable thresholds ✓
- Documentation for customization ✓
- Plugin interface for custom indicators (planned)
- Plugin interface for custom perturbations (planned)

### Week 3-4 (P2) ✓
- Cross-slice consistency checks (temporal coherence) ✓
- Additional indicators (zero-crossing rate, spectral rolloff) ✓
- Batch processing optimization (multiprocessing) ✓
- CLI-configurable thresholds ✓

### CLI-Configurable Thresholds ✓
All deferral policy thresholds can now be customized via CLI or config files:
- `--fragility-threshold`: CV threshold for fragility detection (default from config: 0.3)
- `--clipping-threshold`: Amplitude threshold for clipping (default from config: 0.95)
- `--min-duration`: Minimum slice duration for valid analysis (default from config: 0.5s)

This enables domain-specific tuning without code changes. Config files in `config/` directory provide persistent customization.

### Week 5+ ✓
- Visualization tools (plotly/matplotlib) ✓
- Optional integration with production APIs (via adapter pattern) ✓

### Technical Debt ✓
- Consider librosa for higher-quality resampling if needed ✓
- Make FFT window type configurable ✓

### New Features (Week 5+)

#### Production API Adapter Pattern
The `audio_trust_harness.adapters` package provides a uniform interface for different audio analysis backends:

- **LocalAdapter**: Default adapter using built-in indicators (no external dependencies)
- **HTTPAdapter**: Integrates with external analysis APIs via HTTP
- **BaseAdapter**: Abstract base class for custom adapter implementations

Example usage:
```python
from audio_trust_harness.adapters import LocalAdapter, HTTPAdapter, HTTPAdapterConfig

# Local processing (default)
adapter = LocalAdapter()
result = adapter.analyze(audio_data, sample_rate)

# External API integration
config = HTTPAdapterConfig(
    base_url="https://api.example.com/analyze",
    api_key="your-api-key",
)
adapter = HTTPAdapter(config)
result = adapter.analyze(audio_data, sample_rate)
```

#### CLI-Configurable FFT Window Type
The FFT window function can now be customized via CLI:
- `--fft-window`: Window function for spectral analysis (default: hann)
- Valid options: hann, hamming, blackman, bartlett, boxcar, triang, flattop, parzen, bohman, blackmanharris, nuttall, barthann

This enables domain-specific tuning of spectral analysis parameters.

#### Librosa Resampling Backend
Higher-quality resampling is now available via librosa:
- `--resample-backend`: Choose between 'scipy' (default) or 'librosa'
- Librosa provides higher-quality resampling using polyphase filtering
- Requires librosa installation: `pip install librosa`

### Future Considerations
Example: `audio-trust-harness run --resample-backend librosa --audio input.wav --out audit.jsonl`
### Week 5+ (Research Extensions)
- Visualization tools (plotly/matplotlib)
- Plugin system for custom indicators and perturbations
- Example domain-specific tuning guides (music vs. speech)
- Integration patterns for proprietary indicators

### Technical Debt
- Consider librosa for higher-quality resampling if needed
- Make FFT window type configurable
- Multi-scale analysis (different slice durations)
- Additional indicator families

## Privacy & Security

### Audit Log Redaction
- File paths: Only basenames stored (never full paths)
- Audio data: NEVER stored in logs
- Metadata: Only computed indicators and decisions

### Dependency Choices
- Minimal dependencies to reduce attack surface
- No external API calls without explicit configuration
- Deterministic behavior for reproducibility and auditability
