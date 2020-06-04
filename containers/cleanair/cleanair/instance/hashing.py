"""Functions for hashing."""
import json
import hashlib

def hash_dict(value: dict) -> str:
    """Dumps a dictionary to json string then hashes that string.

    Args:
        value: A dictionary to hash. Keys and values must be compliant with json types.

    Returns:
        The hash of dictionary.

    Notes:
        Any lists within the dictionary are sorted.
        This means the following two dictionaries `A` and `B` will be hashed to the same string:

        >>> A = dict(key=["a", "b"])
        >>> B = dict(key=["b", "a"])
    """
    # it is ESSENTIAL to sort by keys when creating hashes!
    sorted_values = value.copy()
    for key in sorted_values:
        if isinstance(sorted_values[key], list):
            sorted_values[key].sort()
    hash_string = json.dumps(sorted_values, sort_keys=True)
    return hash_fn(hash_string)

def hash_fn(hash_string: str) -> str:
    """Uses sha256 to hash the given string.

    Args:
        hash_string: The string to hash.

    Returns:
        The hash of the given string.
    """
    sha_fn = hashlib.sha256()
    sha_fn.update(bytearray(hash_string, "utf-8"))
    return sha_fn.hexdigest()
