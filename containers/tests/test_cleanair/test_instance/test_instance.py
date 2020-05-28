"""Test the base Instance class."""

from cleanair.instance import Instance

def test_hash_dict():
    """Probe with different dictionaries to ensure they are hashed correctly."""
    dict1 = dict(key=["a", "b"])
    dict2 = dict(key=["b", "a"])
    assert Instance.hash_dict(dict1) == Instance.hash_dict(dict2)
