from pseudomat import common


def test_fingerprint():
    pid = common.fingerprint(['johndoe@example.com', 'John’s first project'])
    assert pid == 'RqEvrmGa0rbVo8JY6toXlR0m_nnBmh9w'
