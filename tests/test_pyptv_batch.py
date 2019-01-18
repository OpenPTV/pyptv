from pyptv import pyptv_batch

def test_pyptv_batch():
    assert pyptv_batch.main('./test_cavity', 10000, 10004) is None
