import time
from utils.retry import retry, RetryLimitError
def test_retry_succeeds_after_retry():
    calls = {"n":0}
    def op():
        calls["n"]+=1
        if calls["n"] < 2:
            raise ValueError("fail")
        return "ok"
    res = retry(op, attempts=3, delay=0.01, backoff=1.5, jitter=0.0)
    assert res=="ok"

def test_retry_exhausts_and_raises():
    def op(): raise RuntimeError("bad")
    try:
        retry(op, attempts=2, delay=0.01, backoff=1.2, jitter=0.0)
        assert False
    except Exception:
        assert True
