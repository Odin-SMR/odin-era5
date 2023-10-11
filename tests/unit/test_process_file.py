from app.process.handler.process_file import create_short_hash


def test_hash():
    hash1 = create_short_hash()
    hash2 = create_short_hash()
    assert hash1 != hash2
