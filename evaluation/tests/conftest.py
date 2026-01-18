"""Shared test fixtures and configuration for pytest."""

import pytest


@pytest.fixture(autouse=True)
def reset_random_seed():
    """Reset random seed before each test for reproducibility."""
    import random

    import numpy as np

    np.random.seed(42)
    random.seed(42)
