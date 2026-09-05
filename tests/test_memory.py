from veil.memory import LockedBuffer, wipe_bytearray


def test_locked_buffer_snapshot_and_wipe():
    buf = LockedBuffer(b"super-secret")
    assert buf.snapshot() == b"super-secret"
    buf.wipe()
    assert buf.snapshot() == b"\x00" * len("super-secret")


def test_wipe_bytearray():
    data = bytearray(b"abc")
    wipe_bytearray(data)
    assert data == bytearray(b"\x00\x00\x00")
