import pytest
import os


@pytest.fixture(scope="session")
def renew_badges():
    os.remove("_REPORTS/badges.yaml")
    yield
