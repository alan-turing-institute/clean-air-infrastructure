"""Functions for hashing."""
import os
import json
import logging
import hashlib
import git


def get_git_hash() -> str:
    """Get the hex hash of the git repo.

    Returns:
        Git hash of git repo.
    """
    try:
        return git.Repo(search_parent_directories=True).head.object.hexsha
    except git.InvalidGitRepositoryError as error:
        # catch exception and try to get environment variable
        git_hash = os.getenv("GIT_HASH", "")
        if len(git_hash) == 0:
            error_message = (
                "Could not find a git repository in the parent directory."
            )
            error_message += "Setting git_hash to empty string."
            logging.error(error_message)
            logging.error(error.__traceback__)
        else:
            logging.info(
                "Using environment variable GITHASH: %s", git_hash
            )
        return git_hash


def instance_id_from_hash(
    model_name: str, param_id: str, data_id: str, git_hash: str,
) -> str:
    """Return an instance id by hashing the arguments.

    Args:
        model_name: Name of a model.
        param_id: Id of model parameters.
        data_id: Id of a dataset.
        git_hash: Unique git hash to identify code version.

    Returns
        Instance id.
    """
    hash_string = model_name + str(param_id)
    hash_string += git_hash + str(data_id)
    return hash_fn(hash_string)


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
