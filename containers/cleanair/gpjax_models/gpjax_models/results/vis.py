import pickle
import pandas as pd
import geopandas as gpd
import os
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from stdata.vis.spacetime import SpaceTimeVisualise
from ..utils.file_manager import (
    FileManager,
)


class Visualization:
    def __init__(self, input_dir: Path, data_type="default"):
        self.data_type = data_type
        self.file_manager = FileManager(
            input_dir
        )  # Initialize FileManager with input directory
        self.training_data = None
        self.testing_data = None
        self.raw_data = None
        self.results = None
        self.vis_obj = None
        self.train_laqn_df = None
        self.test_laqn_df = None
        self.hexgrid_df = None
        self.sat_df = None

    def load_data(self):
        """
        Use FileManager to load the necessary data for visualization.
        """
        try:
            # Load training and testing data using FileManager
            self.training_data = self.file_manager.load_training_data()
            self.testing_data = self.file_manager.load_testing_data()

            # Load the raw data and other data needed for visualization
            self.raw_data = self.file_manager.load_pickle(
                self.file_manager.input_dir / "raw_data.pkl"
            )
            breakpoint()
            if self.raw_data is None:
                raise ValueError("raw_data could not be loaded. Please check the file.")
        except FileNotFoundError as e:
            print(f"Error loading data: {e}")
        except ValueError as ve:
            print(f"Error: {ve}")

    def load_results(self):
        """
        Use FileManager to load the prediction results.
        """
        try:
            self.results = self.file_manager.load_pickle(
                self.file_manager.input_dir / "predictions_svgp.pkl"
            )
            if self.results is None:
                raise ValueError("Results could not be loaded. Please check the file.")
        except FileNotFoundError as e:
            print(f"Error loading results: {e}")
        except ValueError as ve:
            print(f"Error: {ve}")

    def prepare_data(self):
        if self.raw_data is None:
            raise ValueError("raw_data is None, cannot proceed with prepare_data.")

        if "train" not in self.raw_data or "test" not in self.raw_data:
            raise KeyError(
                "'train' or 'test' key missing in raw_data. Check data format."
            )

        self.train_laqn_df = self.fix_df_columns(self.raw_data["train"]["laqn"]["df"])
        self.test_laqn_df = self.fix_df_columns(self.raw_data["test"]["laqn"]["df"])
        self.hexgrid_df = self.fix_df_columns(self.raw_data["test"]["hexgrid"]["df"])

        # Prepare Satellite data if available
        if "sat" in self.raw_data["train"]:
            self.sat_df = self.fix_df_columns(self.raw_data["train"]["sat"]["df"])
            self.sat_df = (
                self.sat_df[["lon", "lat", "NO2", "epoch", "box_id"]]
                .groupby(["epoch", "box_id"])
                .mean()
                .reset_index()
            )
            self.sat_df["pred"] = self.results["predictions"]["sat"]["mu"][0]
            self.sat_df["var"] = self.results["predictions"]["sat"]["var"][0]
            self.sat_df["observed"] = self.sat_df["NO2"]
        else:
            print("Satellite data not available")

    def fix_df_columns(self, df):
        return df.rename(
            columns={"point_id": "id", "datetime": "measurement_start_utc"}
        )

    def visualize_with_traffic_data(self):
        """
        Visualize the data with traffic information.
        """
        if self.results is None:
            raise ValueError("Results data is missing. Cannot visualize traffic data.")

        self.train_laqn_df["pred"] = self.results["predictions"]["train_laqn"]["mu"][
            0
        ].T
        self.train_laqn_df["var"] = np.squeeze(
            self.results["predictions"]["train_laqn"]["var"][0]
        )
        self.train_laqn_df["observed"] = self.train_laqn_df["NO2"]

        # Concatenate train and test data
        laqn_df = pd.concat([self.train_laqn_df, self.test_laqn_df])

        # Load results for hexgrid if necessary
        train_end = self.train_laqn_df["epoch"].max()
        self.vis_obj = SpaceTimeVisualise(
            laqn_df, self.hexgrid_df, geopandas_flag=True, test_start=train_end
        )

        # Show the visualization
        self.vis_obj.show()

    def visualize_with_sat_data(self):
        """
        Visualize the data with satellite information.
        """
        if self.sat_df is None:
            raise ValueError(
                "Satellite data is missing. Cannot visualize satellite data."
            )

        train_end = self.train_laqn_df["epoch"].max()
        laqn_df = pd.concat([self.train_laqn_df, self.test_laqn_df])

        # Include satellite data in visualization
        self.vis_obj = SpaceTimeVisualise(
            laqn_df,
            self.hexgrid_df,
            self.sat_df,
            geopandas_flag=True,
            test_start=train_end,
        )

        # Show the visualization
        self.vis_obj.show()

    def visualize_with_test_data(self):
        """
        Visualize the test data with the predictions and results.
        """
        if self.results is None:
            raise ValueError("Results data is missing. Cannot visualize test data.")

        self.test_laqn_df["pred"] = self.results["predictions"]["test_laqn"]["mu"][0].T
        self.test_laqn_df["var"] = np.squeeze(
            self.results["predictions"]["test_laqn"]["var"][0]
        )
        self.test_laqn_df["observed"] = (
            None  # Test data typically does not have observed values
        )

        # Use the test data to create the visualization
        laqn_df = self.test_laqn_df  # Only visualize the test data

        # Load results for hexgrid if necessary
        train_end = (
            self.train_laqn_df["epoch"].max()
            if self.train_laqn_df is not None
            else None
        )
        self.vis_obj = SpaceTimeVisualise(
            laqn_df, self.hexgrid_df, geopandas_flag=True, test_start=train_end
        )

        # Show the visualization
        self.vis_obj.show()

    def visualize_default(self):
        """
        Default visualization without traffic or satellite.
        """
        laqn_df = pd.concat([self.train_laqn_df, self.test_laqn_df])

        train_end = self.train_laqn_df["epoch"].max()
        self.vis_obj = SpaceTimeVisualise(
            laqn_df, self.hexgrid_df, geopandas_flag=True, test_start=train_end
        )

        self.vis_obj.show()


if __name__ == "__main__":
    # Example of how to choose data type (with traffic data)
    input_dir = Path(
        "/Users/suedaciftci/projects/clean-air/clean-air-infrastructure/containers/cleanair/gpjax_models/data/dataset_20days_bl"
    )
    vis = Visualization(
        input_dir, data_type="with_traffic"
    )  # Change to "satellite" or "without_traffic" for other types

    # Load and prepare data
    vis.load_data()
    vis.load_results()
    vis.prepare_data()

    # Visualize based on the chosen type
    # Uncomment one of the options below to run the specific visualization:

    # Visualize with traffic data
    # vis.visualize_with_traffic_data()

    # Visualize with satellite data
    # vis.visualize_with_sat_data()

    # Visualize with test data
    vis.visualize_with_test_data()

    # Default visualization (without traffic or satellite)
    # vis.visualize_default()
