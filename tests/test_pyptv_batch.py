from pyptv import pyptv_batch

def test_pyptv_batch():
    assert pyptv_batch.main('tests/test_cavity', 10000, 10004) is None
