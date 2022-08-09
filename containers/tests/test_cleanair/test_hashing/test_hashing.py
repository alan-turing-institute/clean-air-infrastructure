"""Test the base Instance class."""

from cleanair.hashing import hash_dict


def test_hash_dict():
    """Probe with different dictionaries to ensure they are hashed correctly."""
    dict1 = dict(key=["a", "b"])
    dict2 = dict(key=["b", "a"])
    assert hash_dict(dict1) == hash_dict(dict2)
