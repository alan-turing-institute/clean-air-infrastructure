import pickle
import numpy as np
import pandas as pd
import geopandas as gpd
from pathlib import Path
import stdata
from stdata.vis.spacetime import SpaceTimeVisualise
import matplotlib.pyplot as plt

DATA_PATH = Path('/Users/ohamelijnck/Downloads/data_mrdgp')
RESULTS_PATH = Path('/Users/ohamelijnck/Downloads/data_mrdgp')
RESULTS_FILE = 'predictions_mrdgp_2000it_2000pre_500ip.pkl'

def load_data():
    training_data = pickle.load(open(str(DATA_PATH / "train_data.pickle"), "rb"))
    testing_data = pickle.load(open(str(DATA_PATH / "test_data.pickle"), "rb"))
    raw_data = pd.read_pickle( DATA_PATH / "raw_data.pickle")

    return training_data, testing_data, raw_data

def load_results():
    training_data = pickle.load(
        open(str(RESULTS_PATH / RESULTS_FILE), "rb")
    )
    return training_data


def fix_df_columns(df):
    return df.rename(columns={"point_id": "id", "datetime": "measurement_start_utc"})


if __name__ == "__main__":
    ex_root = Path("containers/cleanair/gpjax_models")

    training_data, testing_data, raw_data = load_data()

    train_laqn_df = fix_df_columns(raw_data["train"]["laqn"]["df"])
    test_laqn_df = fix_df_columns(raw_data["test"]["laqn"]["df"])

    hexgrid_df = fix_df_columns(raw_data["test"]["hexgrid"]["df"])

    # Load results
    results = load_results()

    train_laqn_df["pred"] = results["predictions"]["train_laqn"]["mu"][0].astype(np.float64)
    train_laqn_df["var"] = results["predictions"]["train_laqn"]["var"][0].astype(np.float64)
    train_laqn_df["observed"] = train_laqn_df["NO2"].astype(np.float64)
    train_laqn_df['NO2'] = train_laqn_df['NO2'].astype(np.float64)

    test_laqn_df["pred"] = results["predictions"]["test_laqn"]["mu"][0].astype(np.float64)
    test_laqn_df["var"] = results["predictions"]["test_laqn"]["var"][0].astype(np.float64)
    test_laqn_df["observed"] = np.NaN

    laqn_df = pd.concat([train_laqn_df, test_laqn_df])
    laqn_df['NO2'] = laqn_df['NO2'].astype(np.float64)
    laqn_df['pred'] = laqn_df['pred'].astype(np.float64)

    hexgrid_df = gpd.GeoDataFrame(
        hexgrid_df, geometry=gpd.points_from_xy(hexgrid_df["lon"], hexgrid_df["lat"])
    )
    hexgrid_df["geom"] = hexgrid_df["geometry"].buffer(0.002)

    hexgrid_df["pred"] = results["predictions"]["hexgrid"]["mu"][0]
    hexgrid_df["var"] = results["predictions"]["hexgrid"]["var"][0]



    train_sat_df = fix_df_columns(raw_data['train']['sat']['df'].copy())
    train_sat_df['NO2'] = train_sat_df['NO2'].astype(np.float64)
    train_sat_df['observed'] = train_sat_df['NO2'].astype(np.float64)

    #train_sat_df['pred'] = results["predictions"]['sat']['mu'][0].astype(np.float64)
    #train_sat_df['var'] = results["predictions"]['sat']['var'][0].astype(np.float64)


    sub_sat_df = train_sat_df[train_sat_df['measurement_start_utc'] == train_sat_df.iloc[0]['measurement_start_utc']].copy()
    sub_laqn_df = train_laqn_df[train_laqn_df['measurement_start_utc'] == train_sat_df.iloc[0]['measurement_start_utc']].copy()

    plt.scatter(sub_sat_df['lon'], sub_sat_df['lat'], c=sub_sat_df['NO2'])
    plt.scatter(sub_laqn_df['lon'], sub_laqn_df['lat'], c=sub_laqn_df['NO2'])


    plt.show()

    # Create a SpaceTimeVisualise object with geopandas_flag=True
    vis_obj = SpaceTimeVisualise(laqn_df, hexgrid_df, sat_df=train_sat_df, geopandas_flag=True)

    # Show the visualization
    vis_obj.show()
