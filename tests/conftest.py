import pandas as pd
import pytest

from cscoach.synthetic import simulate_matches


@pytest.fixture(scope="session")
def synth_df() -> pd.DataFrame:
    return simulate_matches(n_matches=240, rounds_per_match=20, seed=1)
