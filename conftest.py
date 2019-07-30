import pytest


@pytest.fixture(scope="session")
def renew_badges():
    with open("_REPORTS/badges.yaml", "") as f:
        f.write("")
    yield
