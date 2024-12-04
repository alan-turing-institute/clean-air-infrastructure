import pickle
import numpy as np
import pandas as pd
from pathlib import Path
import logging
import os


class ExperimentInstanceNotFoundError(Exception):
    """Error for when a blob is not found"""

    def __init__(self, instance_id):
        super().__init__(f"Blob for {instance_id} not found in storage container")


import logging
from pathlib import Path


class FileManager:
    """Class for managing files for the urbanair project"""

    # Constants
    DEFAULT_TRAINING_NAME = "training"
    DATASET = Path("dataset")
    RAW_DATA_PICKLE = DATASET / "raw_data.pkl"
    TRAINING_DATA_PICKLE = "training_data.pkl"
    TEST_DATA_PICKLE = "test_dataset.pkl"
    RESOURCE_GROUP = "Datasets"
    STORAGE_CONTAINER_NAME = "aqdata"
    STORAGE_ACCOUNT_NAME = "londonaqdatasets"
    ACCOUNT_URL = "https://londonaqdatasets.blob.core.windows.net/"

    def __init__(self, input_dir: Path):
        self.input_dir = input_dir
        self.logger = logging.getLogger(__name__)

    @classmethod
    def download_data_blob(cls, name: str = None, input_dir: Path = None) -> None:
        try:
            sas_token = blob_storage.generate_sas_token(
                resource_group=cls.RESOURCE_GROUP,
                storage_account_key="",
                storage_account_name=cls.STORAGE_ACCOUNT_NAME,
                permit_write=True,
            )

            for blob in blob_storage.list_blobs(
                storage_container_name=cls.STORAGE_CONTAINER_NAME,
                account_url=cls.ACCOUNT_URL,
                sas_token=sas_token,
                name_starts_with=name,
            ):
                data_directory = input_dir / cls.DATASET
                data_directory.mkdir(parents=True, exist_ok=True)
                filepath = data_directory / blob.name
                filepath = filepath.with_suffix(".pkl")
                blob_storage.download_blob(
                    blob_name=blob.name,
                    target_file=filepath,
                    storage_container_name=cls.STORAGE_CONTAINER_NAME,
                    account_url=cls.ACCOUNT_URL,
                    sas_token=sas_token,
                )
        except Exception as e:
            cls.logger.error(f"An error occurred during download: {str(e)}")

    def load_training_data(self) -> dict:
        """Load training data from the dataset directory."""
        for dirpath, _, filenames in os.walk(self.input_dir):
            # Check if 'training_dataset.pkl' exists in the current directory
            if "training_dataset.pkl" in filenames:
                # If found, load the data
                file_path = os.path.join(dirpath, "training_dataset.pkl")
                with open(file_path, "rb") as file:
                    return pickle.load(file)
        raise FileNotFoundError(
            f"{FileManager.TRAINING_DATA_PICKLE} not found in {self.input_dir}"
        )

    def load_testing_data(self) -> dict:
        """Load training data from the dataset directory."""
        for dirpath, _, filenames in os.walk(self.input_dir):
            # Check if 'training_dataset.pkl' exists in the current directory
            if "test_dataset.pkl" in filenames:
                # If found, load the data
                file_path = os.path.join(dirpath, "test_dataset.pkl")
                with open(file_path, "rb") as file:
                    return pickle.load(file)
        raise FileNotFoundError(
            f"{FileManager.TEST_DATA_PICKLE} not found in {self.input_dir}"
        )

    def load_pickle(self, pickle_path: Path) -> any:
        """Load either training or test data from a pickled file."""
        self.logger.debug("Loading object from pickle file from %s", pickle_path)
        if not pickle_path.exists():
            raise FileNotFoundError(f"Could not find file at path {pickle_path}")

        with open(pickle_path, "rb") as pickle_f:
            return pickle.load(
                pickle_f, fix_imports=True, encoding="ASCII", errors="strict"
            )

    def validate_input_directory(self, input_dir: Path) -> None:
        if not input_dir.exists():
            raise IOError(f"Input directory {input_dir} does not exist.")
        if not input_dir.is_dir():
            raise IOError(f"{input_dir} is not a directory.")

    def save_pickle(self, obj: any, input_dir: Path) -> None:
        """Save an object to a filepath by pickling."""
        self.logger.debug("Saving object to pickle file at %s", input_dir)
        with open(input_dir, "wb") as pickle_file:
            pickle.dump(obj, pickle_file)

    def load_test_data(self) -> dict:
        """Load test data from either the CACHE or input_dir."""
        pickle_path = self.input_dir / FileManager.TEST_DATA_PICKLE
        return self.load_pickle(pickle_path)
