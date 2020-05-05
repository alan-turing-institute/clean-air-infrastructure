"""Matplotlib dashboard"""

import tkinter as tk
import pandas as pd
import numpy as np
import geopandas as gpd
import matplotlib
import os

import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button, RadioButtons
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.widgets import TextBox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from datetime import datetime
import shapely
from shapely import wkt
from shapely.ops import nearest_points
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon

import json
import pickle


class DashBoard:
    """
        Dashboard class. A dashboard is made up of a collection of pages, and each
            pages is made up of widgets.
    """

    def __init__(self):
        self.bg_color = "#7f8c8d"
        self.experiments_root = "../experiment_data/"
        self.load_page("default")

    def plot(self):
        """
            Plot current figure
        """

        tk.mainloop()

    def load_page(self, name):
        """
            Redraw dashboard with the passed page name
        """

        pages = {"default": ComparePlots}

        self.page = pages[name](self)
        self.create_layout()
        self.draw_page()

        plt.tight_layout()

        canvas = FigureCanvasTkAgg(self.fig, master=self.master)  # A tk.DrawingArea.
        canvas.draw()
        canvas.get_tk_widget().pack(in_=self.page_frame)

        self.topbar = tk.Frame(
            self.master, width=self.screen_width - 80, height=40, bg="blue"
        )
        self.topbar.place(x=80, y=0)
        self.page.draw_topbar(self, self.topbar)

        self.plot()

    def draw_page(self):
        """
            Calculate the pages layout array and draw
        """

        page_layout = self.page.get_layout()

        layout = []

        for row in range(page_layout["n_rows"]):
            row_arr = []

            for col in range(page_layout["n_cols"]):
                row_arr.append(self.layout[row, 1 + col])

            layout.append(row_arr)

        self.page.draw(self.fig, layout)

    def create_layout(self):
        """
            Dashboard layout has an column of buttons on the LHS and then a page on 
                the remaining RHS.
        """

        self.master = tk.Tk()
        self.master.configure(background=self.bg_color)

        self.screen_width = self.master.winfo_screenwidth()
        self.screen_height = self.master.winfo_screenheight()
        self.dpi = 100

        self.page_frame = tk.Frame(self.master)
        self.page_frame.pack(fill=tk.BOTH, expand=1)

        self.fig = plt.figure(
            figsize=(self.screen_width / self.dpi, self.screen_height / self.dpi),
            dpi=self.dpi,
            frameon=True,
            facecolor=self.bg_color,
        )

        page_layout = self.page.get_layout()

        # GridSpec: nrows, ncols, spaces between subplots
        # layout is an array of rows x cols
        self.layout = matplotlib.gridspec.GridSpec(
            page_layout["n_rows"],
            1 + page_layout["n_cols"],
            figure=self.fig,
            wspace=0,
            hspace=0,
            width_ratios=[0.05] + [0.95 * w for w in page_layout["width_ratios"]],
            height_ratios=page_layout["height_ratios"],
        )

class Page:
    """
        Define a page in a DashBoard
    """

    def __init__(self, dashboard):
        self.dashboard = dashboard
        self.layout = None
        self.plot_sat = False

    def draw(self, fig, layout):
        """
            Draw the axes. Layout is an array of the subplots to draw on.
        """
        pass

    def draw_topbar(self, dashboard, topbar):
        """
            Draw Tkinter topbar.
        """
        pass

    def get_layout(self):
        """
            Each page made using GridSpec.
            returns:
                n_rows
                n_cols
                width_ratios
                height_ratios
        """
        pass

    def load_pickle(self, fp):
        with open(fp, 'rb') as handle:
            return pickle.load(handle)

    def load_satellite_data(self, experiment_name, model, data_idx, param_idx):
        """
            load satellite input training data
        """

        #load raw satellite X
        self.processed_satellite_data = pd.read_csv(
            self.dashboard.experiments_root
            + "{name}/data/data{data_idx}/normalised_satellite_data_x.csv".format(
                name=experiment_name,
                data_idx=data_idx,
                index_col=0,
                low_memory=False,
            )
        )


        #load raw satellite Y
        self.processed_satellite_data_values = pd.read_csv(
            self.dashboard.experiments_root
            + "{name}/data/data{data_idx}/normalised_satellite_data_y.csv".format(
                name=experiment_name,
                data_idx=data_idx,
                index_col=0,
                low_memory=False,
            )
        )


        #create satellite tile geometry
        self.sat_locations = pd.read_csv('satellite_site.csv')
        self.sat_locations["src_geom"] = self.sat_locations["geom"]
        self.sat_locations["geom"] = self.sat_locations["src_geom"].apply(wkt.loads)
        self.sat_locations = gpd.GeoDataFrame(self.sat_locations, geometry="geom")

    def load_raw_data(self, experiment_name, model, data_idx, param_idx):
        self.processed_training_data = pd.read_csv(
            self.dashboard.experiments_root
            + "{name}/data/data{data_idx}/normalised_training_data.csv".format(
                name=experiment_name,
                data_idx=data_idx,
                index_col=0,
                low_memory=False,
            )
        )
        self.processed_predicting_data = pd.read_csv(
            self.dashboard.experiments_root
            + "{name}/data/data{data_idx}/normalised_pred_data.csv".format(
                name=experiment_name, data_idx=data_idx, low_memory=False
            )
        )

    def load_training_data(self, experiment_name, model, data_idx, param_idx):
        self.training_data = self.load_pickle(
            self.dashboard.experiments_root
            + "{name}/data/data{data_idx}/train.pickle".format(
                name=experiment_name,
                data_idx=data_idx,
            )
        )

        self.testing_data = self.load_pickle(
            self.dashboard.experiments_root
            + "{name}/data/data{data_idx}/test.pickle".format(
                name=experiment_name,
                data_idx=data_idx,
            )
        )


    def load_results(self, experiment_name, model, data_idx, param_idx):
        self.predictions_testing = self.load_pickle(
            self.dashboard.experiments_root
            + "{name}/results/{model}_param{param_idx}_data{data_idx}/test_pred.pickle".format(
                model=model,
                name=experiment_name,
                param_idx=param_idx,
                data_idx=data_idx,
            )
        )

        self.predictions_training = self.load_pickle(
            self.dashboard.experiments_root
            + "{name}/results/{model}_param{param_idx}_data{data_idx}/train_pred.pickle".format(
                model=model,
                name=experiment_name,
                param_idx=param_idx,
                data_idx=data_idx,
            )
        )

    def load_experiment_data(self, experiment_name, model, data_idx, param_idx):
        """
            Loads raw data, training data and results for a given experiment run.
            Checks to see if satellite was used in the experiment.
        """
        try:
            # load meta data
            with open(
                self.dashboard.experiments_root
                + "{name}/meta/data.json".format(name=experiment_name)
            ) as json_file:
                data_json = json.load(json_file)

            # we only need to check the first element of data configurations to see if satelitte is included
            self.plot_sat = False
            if data_json[0]["include_satellite"] is True:
                self.plot_sat = True

            # satellite raw data is stored in seperate files to the ground sensors
            if self.plot_sat:
                self.load_satellite_data(experiment_name, model, data_idx, param_idx)

            self.load_raw_data(experiment_name, model, data_idx, param_idx)
            self.load_results(experiment_name, model, data_idx, param_idx)
            self.load_training_data(experiment_name, model, data_idx, param_idx)

            return True
        except Exception as e:
            print(e)
            return False

    def get_experiment_names(self):
        """
            Get list of all folders inside `experiments_root`. Filter out cluster folder.
        """
        names = [
            name
            for name in os.listdir(self.dashboard.experiments_root)
            if (
                os.path.isdir(self.dashboard.experiments_root + name)
                and (name != "cluster")
            )
        ]
        return names

    def get_experiment_config(self, experiment_name):
        config_fp = (
            self.dashboard.experiments_root + experiment_name + "/meta/experiment.csv"
        )
        config = pd.read_csv(config_fp)
        return config

    def get_correct_column_names(self, df):
        df["id"] = df["point_id"]
        df["pred"] = df["val"]
        df["var"] = 2 * np.sqrt(df["var"])
        df["observed"] = df["NO2"]
        df["datetime"] = df["measurement_start_utc"]
        return df


    def process_source(self, src, testing_only = False):
        # get src predictions
        pred = 'NO2'

        src_testing_predictions = self.processed_predicting_data[
            self.processed_predicting_data["source"] == src
        ]


        src_testing_predictions["val"] = self.predictions_testing[src][pred]['mean']
        src_testing_predictions["var"] = self.predictions_testing[src][pred]["var"]


        src_testing_predictions = self.get_correct_column_names(src_testing_predictions)

        if not testing_only:
            src_training_predictions = self.processed_training_data[
                self.processed_training_data["source"] == src
            ]

            src_training_predictions["val"] = self.predictions_training[src][pred]['mean']
            src_training_predictions["var"] = self.predictions_training[src][pred]['var']

            src_training_predictions = self.get_correct_column_names(
                src_training_predictions
            )

            self.min_datetime = min(
                min(src_training_predictions["measurement_start_utc"]),
                min(src_testing_predictions["measurement_start_utc"]),
            )
            self.max_datetime = max(
                max(src_training_predictions["measurement_start_utc"]),
                max(src_testing_predictions["measurement_start_utc"]),
            )

            src_training_predictions["measurement_start_utc"] = pd.to_datetime(
                src_training_predictions["measurement_start_utc"]
            )
            src_testing_predictions["measurement_start_utc"] = pd.to_datetime(
                src_testing_predictions["measurement_start_utc"]
            )

            return (
                pd.concat([src_training_predictions, src_testing_predictions]),
                src_training_predictions,
                src_testing_predictions
            )

        else:
            self.min_datetime = min(src_testing_predictions["measurement_start_utc"])
            self.max_datetime = max(src_testing_predictions["measurement_start_utc"])
            src_testing_predictions["measurement_start_utc"] = pd.to_datetime(
                src_testing_predictions["measurement_start_utc"]
            )

            return (
                src_testing_predictions,
                src_testing_predictions,
                src_testing_predictions
            )

class CompareFeatures(Page):
    """
        Visualise input features
    """

    def __init__(self, dashboard):
        Page.__init__(self, dashboard)
        self.map_layer = "hexgrid"
        self.sensor_layer = "laqn"



    def draw(self, fig, layout):
        self.layout = layout
        self.fig = fig

        self.title_lhs = self.fig.add_subplot(self.layout[1][0], frameon=False)
        self.title_lhs.axis("off")
        # place a text box in upper left in axes coords

        self.map_lhs = self.fig.add_subplot(self.layout[2][0])
        # self.map_rhs = self.fig.add_subplot(self.layout[1][1])

        self.timeseries_lhs = self.fig.add_subplot(self.layout[4][0])
        # self.timeseries_rhs = self.fig.add_subplot(self.layout[2][1])

        self.slider_lhs = self.fig.add_subplot(self.layout[6][0])
        # self.slider_lhs.subplots_adjust(wspace=0.1)
        # self.slider_rhs = self.fig.add_subplot(self.layout[3][1])

        if False:
            #default experiment
            self.update_experiment_data(
                'satellite',
                'mr_dgp',
                '0',
                '0',
            )

    def create_dropdown(self, master, choices, default=None):
        tkvar1 = tk.StringVar(master)
        choices1 = choices
        if default:
            tkvar1.set(default)  # set the default option
        else:
            tkvar1.set(choices[0])  # set the default option

        popupMenu1 = tk.OptionMenu(master, tkvar1, *choices1)
        popupMenu1.config(width=10, height=2)
        popupMenu1.pack(in_=master, side=tk.LEFT)
        return tkvar1, popupMenu1

    def update_sat_timeseries(self, _id, scatter_plot, timeseries_plot):
        sat_obs = self.sat_obs[self.sat_obs['box_id'] == _id]
        if self.sat_splot is not  None:
            self.sat_splot.remove()

        self.sat_splot = self.timeseries_lhs.scatter(sat_obs['measurement_start_utc'], sat_obs['value'], color='black', marker='x')

        self.fig.canvas.draw_idle()

    def update_timeseries(self, _id, scatter_plot, timeseries_plot):

        scatter_plot.update_active(_id)
        timeseries_plot.update(_id)
        self.fig.canvas.draw_idle()

    def update_slider(
        self, datetime, epoch, title_text, grid_plot, hexgrid_plot, scatter_plot, timerseries_plot
    ):
        timerseries_plot.update_cur_epoch(datetime)

        if grid_plot is not None:
            grid_plot.update(datetime)

        if hexgrid_plot is not None:
            hexgrid_plot.update(datetime)

        scatter_plot.update(datetime)

        title_text.set_text(datetime)

    def update_experiment_data(self, experiment_name, model, data_id, param_id, val=None):
        val = 'val' if val is None else val

        self.clean()

        loaded_flag = self.load_experiment_data(experiment_name, model, data_id, param_id)
        if loaded_flag is False:
            print("Could not load: ", experiment_name, model, data_id, param_id)
            return

        columns = {
            "id": "point_id",
            "pred": val,
            "sat_obs": "value",
            "var": "var",
            "observed": "NO2",
            "x": "lon",
            "y": "lat",
            "datetime": "measurement_start_utc",
            "epoch": "measurement_start_utc",
        }

        training_keys = self.predictions_training.keys()
        testing_keys = self.predictions_testing.keys()



        if 'hexgrid' in training_keys:
            pass

        scatter_id = 'laqn'

        (sensor_predictions, sensor_training_predictions, sensor_testing_predictions) = self.process_source(self.sensor_layer)


        self.splot = ST_ScatterPlot(
            columns, self.fig, self.map_lhs, None, sensor_predictions
        )
        self.tplot = ST_TimeSeriesPlot(
            columns,
            self.fig,
            self.timeseries_lhs,
            sensor_training_predictions,
            sensor_testing_predictions,
        )

        self.splot.setup(
            callback=lambda x: self.update_timeseries(x, self.splot, self.tplot)
        )
        self.splot.plot(self.min_datetime)

        self.tplot.setup()
        self.tplot.plot(self.splot.cur_id)


        unique_epochs = pd.unique(sensor_predictions["epoch"])

        self.text_lhs = self.title_lhs.text(
            0.5,
            0.95,
            self.min_datetime,
            transform=self.title_lhs.transAxes,
            fontsize=14,
            horizontalalignment="center",
            verticalalignment="top",
        )

        self.sat_splot = None
        sat_obs = pd.merge(
            left = self.processed_satellite_data_values,
            right = self.sat_locations,
            how = 'left',
            left_on="box_id",
            right_on="box_id"
        )
        sat_obs[columns['epoch']] = pd.to_datetime(sat_obs[columns['epoch']])
        self.sat_obs = sat_obs


        columns_sat = columns.copy()
        columns_sat['id'] = 'box_id'
        self.val_grid_plot = ST_GridPlot(
            columns_sat,
            "sat_obs",
            self.fig,
            self.map_lhs,
            sat_obs,
            cax_on_right=False,
            norm_on_training=True,
            label="NO2",
            geopandas_flag=True,
        )

        self.val_grid_plot.setup(
            callback=lambda x: self.update_sat_timeseries(x, self.splot, self.tplot)
        )
        self.val_grid_plot.plot(self.min_datetime)





        #( laqn_predictions, laqn_training_predictions, laqn_testing_predictions,) = self.process_source(self.sensor_layer)
        ( grid_predictions, grid_training_predictions, grid_testing_predictions,) = self.process_source(self.map_layer, testing_only=True)

        # TODO: quick fix until can get geom easily
        hexgrid_file = pd.read_csv("hexgrid/hexgrid_polygon.csv")
        grid_predictions = pd.merge(
            left=grid_predictions,
            right=hexgrid_file,
            how="left",
            left_on="point_id",
            right_on="point_id",
        )
        grid_predictions["src_geom"] = grid_predictions["geom"]
        grid_predictions["geom"] = grid_predictions["src_geom"].apply(wkt.loads)
        grid_predictions = gpd.GeoDataFrame(grid_predictions, geometry="geom")



        print(grid_predictions.columns)
        self.hex_grid_plot = ST_GridPlot(
            columns,
            "pred",
            self.fig,
            self.map_lhs,
            grid_predictions,
            cax_on_right=False,
            norm_on_training=False,
            label="NO2",
            geopandas_flag=True,
        )
        self.hex_grid_plot.setup()
        self.hex_grid_plot.plot(self.min_datetime)

        self.slider_plot = ST_SliderPlot(
            self.fig,
            self.slider_lhs,
            unique_epochs,
            lambda x, y: self.update_slider(
                x, y, self.text_lhs, self.val_grid_plot, self.hex_grid_plot, self.splot, self.tplot
            ),
        )
        self.slider_plot.setup(unique_epochs[0])

        self.tplot.plot_cur_epoch(unique_epochs[0])



    def update_dropdowns(self, master, experiment_name, tkvars, dropdowns):
        experiment_config = self.get_experiment_config(experiment_name)
        experiment_models = pd.unique(experiment_config["model_name"])
        experiment_param_ids = pd.unique(experiment_config["param_id"])
        experiment_data_ids = pd.unique(experiment_config["data_id"])

        loaded_flag = self.load_experiment_data(experiment_name, experiment_models[0], experiment_data_ids[0], experiment_param_ids[0])
        features = self.processed_training_data.columns

        def update_dropdown(tkvar, dropdown, choices):
            menu = dropdown["menu"]
            menu.delete(0, "end")
            tkvar.set(choices[0])
            for string in choices:
                menu.add_command(
                    label=string, command=lambda value=string: tkvar.set(value)
                )

        update_dropdown(tkvars[1], dropdowns[1], experiment_models)
        update_dropdown(tkvars[2], dropdowns[2], experiment_param_ids)
        update_dropdown(tkvars[3], dropdowns[3], experiment_data_ids)
        update_dropdown(tkvars[4], dropdowns[4], features)

        self.update_experiment_data(
            experiment_name,
            experiment_models[0],
            experiment_data_ids[0],
            experiment_param_ids[0],
            features[0]
        )

    def dropdowns_on_change(self, master, tkvars, dropdowns):
        experiment_name = tkvars[0].get()
        experiment_model = tkvars[1].get()
        experiment_data_id = tkvars[2].get()
        experiment_param_id = tkvars[3].get()
        experiment_feature = tkvars[4].get()
        self.update_experiment_data(
            experiment_name, experiment_model, experiment_data_id, experiment_param_id, experiment_feature
        )

    def draw_topbar(self, dashboard, topbar):
        """
            Draw Tkinter topbar.
        """

        print(self.get_experiment_names())

        self.topbar_frame_lhs = tk.Frame(topbar)
        self.topbar_frame_lhs.place(x=0, y=0)

        self.topbar_frame_rhs = tk.Frame(topbar)
        self.topbar_frame_rhs.place(relx=0.5, y=0)

        experiment_names = self.get_experiment_names()

        # TODO: flag if no experiments
        default = experiment_names[0]

        experiment_config = self.get_experiment_config(default)

        experiment_models = pd.unique(experiment_config["model_name"])
        experiment_param_ids = pd.unique(experiment_config["param_id"])
        experiment_data_ids = pd.unique(experiment_config["data_id"])


        loaded_flag = self.load_experiment_data(experiment_names[0], experiment_models[0], experiment_data_ids[0], experiment_param_ids[0])

        features = self.processed_training_data.columns

        self.update_experiment_data(
            experiment_names[0],
            experiment_models[0],
            experiment_data_ids[0],
            experiment_param_ids[0],
            features[0]
        )

        # TODO: compress duplicate code?

        tkvar_exp_lhs, topbar_exp_lhs = self.create_dropdown(
            master=self.topbar_frame_lhs, choices=experiment_names, default=default
        )
        tkvar_model_lhs, topbar_model_lhs = self.create_dropdown(
            master=self.topbar_frame_lhs, choices=experiment_models
        )
        tkvar_params_lhs, topbar_params_lhs = self.create_dropdown(
            master=self.topbar_frame_lhs, choices=experiment_param_ids
        )
        tkvar_data_lhs, topbar_data_lhs = self.create_dropdown(
            master=self.topbar_frame_lhs, choices=experiment_data_ids
        )

        tkvar_features_lhs, topbar_features_lhs = self.create_dropdown(
            master=self.topbar_frame_lhs, choices=features
        )

        tkvar_exp_rhs, topbar_exp_rhs = self.create_dropdown(
            master=self.topbar_frame_rhs, choices=experiment_names, default=default
        )
        tkvar_model_rhs, topbar_model_rhs = self.create_dropdown(
            master=self.topbar_frame_rhs, choices=experiment_models
        )
        tkvar_params_rhs, topbar_params_rhs = self.create_dropdown(
            master=self.topbar_frame_rhs, choices=experiment_param_ids
        )
        tkvar_data_rhs, topbar_data_rhs = self.create_dropdown(
            master=self.topbar_frame_rhs, choices=experiment_data_ids
        )

        tkvar_exp_lhs.trace(
            "w",
            lambda *args: self.update_dropdowns(
                self.topbar_frame_lhs,
                tkvar_exp_lhs.get(),
                [tkvar_exp_lhs, tkvar_model_lhs, tkvar_params_lhs, tkvar_data_lhs, tkvar_features_lhs],
                [topbar_exp_lhs, topbar_model_lhs, topbar_params_lhs, topbar_data_lhs, topbar_features_lhs],
            ),
        )

        tkvar_model_lhs.trace(
            "w",
            lambda *args: self.dropdowns_on_change(
                self.topbar_frame_lhs,
                [tkvar_exp_lhs, tkvar_model_lhs, tkvar_params_lhs, tkvar_data_lhs, tkvar_features_lhs],
                [topbar_exp_lhs, topbar_model_lhs, topbar_params_lhs, topbar_data_lhs, topbar_features_lhs],
            ),
        )

        tkvar_features_lhs.trace(
            "w",
            lambda *args: self.dropdowns_on_change(
                self.topbar_frame_lhs,
                [tkvar_exp_lhs, tkvar_model_lhs, tkvar_params_lhs, tkvar_data_lhs, tkvar_features_lhs],
                [topbar_exp_lhs, topbar_model_lhs, topbar_params_lhs, topbar_data_lhs, topbar_features_lhs],
            ),
        )

        tkvar_exp_rhs.trace(
            "w",
            lambda *args: self.update_dropdowns(
                self.topbar_frame_rhs,
                tkvar_exp_rhs.get(),
                [tkvar_exp_rhs, tkvar_model_rhs, tkvar_params_rhs, tkvar_data_rhs],
                [topbar_exp_rhs, topbar_model_rhs, topbar_params_rhs, topbar_data_rhs],
            ),
        )

    def clean(self):
        self.map_lhs.clear()
        self.timeseries_lhs.clear()
        self.slider_lhs.clear()
        if hasattr(self, 'hex_grid_plot'):
            del self.hex_grid_plot

    def get_layout(self):
        """
            Return 2 columns and two rows
        """
        return {
            "n_rows": 7,
            "n_cols": 2,
            "width_ratios": [0.5, 0.5],
            "height_ratios": [0.05, 0.05, 0.50, 0.05, 0.3 - 0.05, 0.06, 0.04],
        }

class ComparePlots(Page):
    """
        Compare two experiments side by side
    """

    def __init__(self, dashboard):
        Page.__init__(self, dashboard)
        self.map_layer = "hexgrid"
        self.sensor_layer = "laqn"



    def draw(self, fig, layout):
        self.layout = layout
        self.fig = fig

        self.title_lhs = self.fig.add_subplot(self.layout[1][0], frameon=False)
        self.title_lhs.axis("off")
        # place a text box in upper left in axes coords

        self.map_lhs = self.fig.add_subplot(self.layout[2][0])
        # self.map_rhs = self.fig.add_subplot(self.layout[1][1])

        self.timeseries_lhs = self.fig.add_subplot(self.layout[4][0])
        # self.timeseries_rhs = self.fig.add_subplot(self.layout[2][1])

        self.slider_lhs = self.fig.add_subplot(self.layout[6][0])
        # self.slider_lhs.subplots_adjust(wspace=0.1)
        # self.slider_rhs = self.fig.add_subplot(self.layout[3][1])

        if False:
            #default experiment
            self.update_experiment_data(
                'satellite',
                'mr_dgp',
                '0',
                '0',
            )

    def create_dropdown(self, master, choices, default=None):
        tkvar1 = tk.StringVar(master)
        choices1 = choices
        if default:
            tkvar1.set(default)  # set the default option
        else:
            tkvar1.set(choices[0])  # set the default option

        popupMenu1 = tk.OptionMenu(master, tkvar1, *choices1)
        popupMenu1.config(width=10, height=2)
        popupMenu1.pack(in_=master, side=tk.LEFT)
        return tkvar1, popupMenu1

    def update_sat_timeseries(self, _id, scatter_plot, timeseries_plot):
        sat_obs = self.sat_obs[self.sat_obs['box_id'] == _id]
        if self.sat_splot is not  None:
            self.sat_splot.remove()

        self.sat_splot = self.timeseries_lhs.scatter(sat_obs['measurement_start_utc'], sat_obs['value'], color='black', marker='x')

        self.fig.canvas.draw_idle()

    def update_timeseries(self, _id, scatter_plot, timeseries_plot):

        scatter_plot.update_active(_id)
        timeseries_plot.update(_id)
        self.fig.canvas.draw_idle()

    def update_slider(
        self, datetime, epoch, title_text, grid_plot, hexgrid_plot, scatter_plot, timerseries_plot
    ):
        timerseries_plot.update_cur_epoch(datetime)

        if grid_plot is not None:
            grid_plot.update(datetime)

        if hexgrid_plot is not None:
            hexgrid_plot.update(datetime)

        scatter_plot.update(datetime)

        title_text.set_text(datetime)

    def update_experiment_data(self, experiment_name, model, data_id, param_id):
        loaded_flag = self.load_experiment_data(experiment_name, model, data_id, param_id)
        if loaded_flag is False:
            print("Could not load: ", experiment_name, model, data_id, param_id)
            return

        columns = {
            "id": "point_id",
            "pred": "val",
            "sat_obs": "value",
            "var": "var",
            "observed": "NO2",
            "x": "lon",
            "y": "lat",
            "datetime": "measurement_start_utc",
            "epoch": "measurement_start_utc",
        }

        training_keys = self.predictions_training.keys()
        testing_keys = self.predictions_testing.keys()



        if 'hexgrid' in training_keys:
            pass

        scatter_id = 'laqn'

        (sensor_predictions, sensor_training_predictions, sensor_testing_predictions) = self.process_source(self.sensor_layer)


        self.splot = ST_ScatterPlot(
            columns, self.fig, self.map_lhs, None, sensor_predictions
        )
        self.tplot = ST_TimeSeriesPlot(
            columns,
            self.fig,
            self.timeseries_lhs,
            sensor_training_predictions,
            sensor_testing_predictions,
        )

        self.splot.setup(
            callback=lambda x: self.update_timeseries(x, self.splot, self.tplot)
        )
        self.splot.plot(self.min_datetime)

        self.tplot.setup()
        self.tplot.plot(self.splot.cur_id)


        unique_epochs = pd.unique(sensor_predictions["epoch"])

        self.text_lhs = self.title_lhs.text(
            0.5,
            0.95,
            self.min_datetime,
            transform=self.title_lhs.transAxes,
            fontsize=14,
            horizontalalignment="center",
            verticalalignment="top",
        )

        self.sat_splot = None
        sat_obs = pd.merge(
            left = self.processed_satellite_data_values,
            right = self.sat_locations,
            how = 'left',
            left_on="box_id",
            right_on="box_id"
        )
        sat_obs[columns['epoch']] = pd.to_datetime(sat_obs[columns['epoch']])
        self.sat_obs = sat_obs


        columns_sat = columns.copy()
        columns_sat['id'] = 'box_id'
        self.val_grid_plot = ST_GridPlot(
            columns_sat,
            "sat_obs",
            self.fig,
            self.map_lhs,
            sat_obs,
            cax_on_right=False,
            norm_on_training=True,
            label="NO2",
            geopandas_flag=True,
        )

        self.val_grid_plot.setup(
            callback=lambda x: self.update_sat_timeseries(x, self.splot, self.tplot)
        )
        self.val_grid_plot.plot(self.min_datetime)





        #( laqn_predictions, laqn_training_predictions, laqn_testing_predictions,) = self.process_source(self.sensor_layer)
        ( grid_predictions, grid_training_predictions, grid_testing_predictions,) = self.process_source(self.map_layer, testing_only=True)

        # TODO: quick fix until can get geom easily
        hexgrid_file = pd.read_csv("hexgrid/hexgrid_polygon.csv")
        grid_predictions = pd.merge(
            left=grid_predictions,
            right=hexgrid_file,
            how="left",
            left_on="point_id",
            right_on="point_id",
        )
        grid_predictions["src_geom"] = grid_predictions["geom"]
        grid_predictions["geom"] = grid_predictions["src_geom"].apply(wkt.loads)
        grid_predictions = gpd.GeoDataFrame(grid_predictions, geometry="geom")



        print(grid_predictions.columns)
        self.hex_grid_plot = ST_GridPlot(
            columns,
            "pred",
            self.fig,
            self.map_lhs,
            grid_predictions,
            cax_on_right=False,
            norm_on_training=True,
            label="NO2",
            geopandas_flag=True,
        )
        self.hex_grid_plot.setup()
        self.hex_grid_plot.plot(self.min_datetime)

        self.slider_plot = ST_SliderPlot(
            self.fig,
            self.slider_lhs,
            unique_epochs,
            lambda x, y: self.update_slider(
                x, y, self.text_lhs, self.val_grid_plot, self.hex_grid_plot, self.splot, self.tplot
            ),
        )
        self.slider_plot.setup(unique_epochs[0])

        self.tplot.plot_cur_epoch(unique_epochs[0])



    def update_dropdowns(self, master, experiment_name, tkvars, dropdowns):
        experiment_config = self.get_experiment_config(experiment_name)
        experiment_models = pd.unique(experiment_config["model_name"])
        experiment_param_ids = pd.unique(experiment_config["param_id"])
        experiment_data_ids = pd.unique(experiment_config["data_id"])

        def update_dropdown(tkvar, dropdown, choices):
            menu = dropdown["menu"]
            menu.delete(0, "end")
            tkvar.set(choices[0])
            for string in choices:
                menu.add_command(
                    label=string, command=lambda value=string: tkvar.set(value)
                )

        update_dropdown(tkvars[1], dropdowns[1], experiment_models)
        update_dropdown(tkvars[2], dropdowns[2], experiment_param_ids)
        update_dropdown(tkvars[3], dropdowns[3], experiment_data_ids)

        self.update_experiment_data(
            experiment_name,
            experiment_models[0],
            experiment_data_ids[0],
            experiment_param_ids[0],
        )

    def dropdowns_on_change(self, master, tkvars, dropdowns):
        experiment_name = tkvars[0].get()
        experiment_model = tkvars[1].get()
        experiment_data_id = tkvars[2].get()
        experiment_param_id = tkvars[3].get()
        self.update_experiment_data(
            experiment_name, experiment_model, experiment_data_id, experiment_param_id
        )

    def draw_topbar(self, dashboard, topbar):
        """
            Draw Tkinter topbar.
        """

        print(self.get_experiment_names())

        self.topbar_frame_lhs = tk.Frame(topbar)
        self.topbar_frame_lhs.place(x=0, y=0)

        self.topbar_frame_rhs = tk.Frame(topbar)
        self.topbar_frame_rhs.place(relx=0.5, y=0)

        experiment_names = self.get_experiment_names()

        # TODO: flag if no experiments
        default = experiment_names[0]

        experiment_config = self.get_experiment_config(default)

        experiment_models = pd.unique(experiment_config["model_name"])
        experiment_param_ids = pd.unique(experiment_config["param_id"])
        experiment_data_ids = pd.unique(experiment_config["data_id"])

        print(experiment_param_ids)

        self.update_experiment_data(
            experiment_names[0],
            experiment_models[0],
            experiment_data_ids[0],
            experiment_param_ids[0],
        )

        # TODO: compress duplicate code?

        tkvar_exp_lhs, topbar_exp_lhs = self.create_dropdown(
            master=self.topbar_frame_lhs, choices=experiment_names, default=default
        )
        tkvar_model_lhs, topbar_model_lhs = self.create_dropdown(
            master=self.topbar_frame_lhs, choices=experiment_models
        )
        tkvar_params_lhs, topbar_params_lhs = self.create_dropdown(
            master=self.topbar_frame_lhs, choices=experiment_param_ids
        )
        tkvar_data_lhs, topbar_data_lhs = self.create_dropdown(
            master=self.topbar_frame_lhs, choices=experiment_data_ids
        )

        tkvar_exp_rhs, topbar_exp_rhs = self.create_dropdown(
            master=self.topbar_frame_rhs, choices=experiment_names, default=default
        )
        tkvar_model_rhs, topbar_model_rhs = self.create_dropdown(
            master=self.topbar_frame_rhs, choices=experiment_models
        )
        tkvar_params_rhs, topbar_params_rhs = self.create_dropdown(
            master=self.topbar_frame_rhs, choices=experiment_param_ids
        )
        tkvar_data_rhs, topbar_data_rhs = self.create_dropdown(
            master=self.topbar_frame_rhs, choices=experiment_data_ids
        )

        tkvar_exp_lhs.trace(
            "w",
            lambda *args: self.update_dropdowns(
                self.topbar_frame_lhs,
                tkvar_exp_lhs.get(),
                [tkvar_exp_lhs, tkvar_model_lhs, tkvar_params_lhs, tkvar_data_lhs],
                [topbar_exp_lhs, topbar_model_lhs, topbar_params_lhs, topbar_data_lhs],
            ),
        )

        tkvar_model_lhs.trace(
            "w",
            lambda *args: self.dropdowns_on_change(
                self.topbar_frame_lhs,
                [tkvar_exp_lhs, tkvar_model_lhs, tkvar_params_lhs, tkvar_data_lhs],
                [topbar_exp_lhs, topbar_model_lhs, topbar_params_lhs, topbar_data_lhs],
            ),
        )

        tkvar_exp_rhs.trace(
            "w",
            lambda *args: self.update_dropdowns(
                self.topbar_frame_rhs,
                tkvar_exp_rhs.get(),
                [tkvar_exp_rhs, tkvar_model_rhs, tkvar_params_rhs, tkvar_data_rhs],
                [topbar_exp_rhs, topbar_model_rhs, topbar_params_rhs, topbar_data_rhs],
            ),
        )

    def get_layout(self):
        """
            Return 2 columns and two rows
        """
        return {
            "n_rows": 7,
            "n_cols": 2,
            "width_ratios": [0.5, 0.5],
            "height_ratios": [0.05, 0.05, 0.50, 0.05, 0.3 - 0.05, 0.06, 0.04],
        }


class ST_ScatterPlot(object):
    def __init__(self, columns, fig, ax, norm, df):
        self.columns = columns

        self.fig = fig
        self.ax = ax

        self.df = df
        self.cmap = None

        if norm is None:
            self.norm = matplotlib.colors.Normalize(
                vmin=np.min(self.df[self.columns["pred"]]),
                vmax=np.max(self.df[self.columns["pred"]]),
            )
        else:
            self.norm = norm

        self.cur_epoch = None

    def setup(self, callback):
        self.callback = callback
        # assume default id is the first one
        self.plot_active(self.df[self.columns["id"]].iloc[0])
        self.fig.canvas.mpl_connect("button_release_event", self.on_plot_hover)

    def get_closest_observed(self, p):
        d = np.array(self.df[[self.columns["x"], self.columns["y"]]]).astype(np.float32)
        dists = np.sum((d - p) ** 2, axis=1)
        i = np.argmin(dists)
        if dists[i] <= 1e-4:
            return self.df.iloc[i][self.columns["id"]]
        else:
            return None

    def on_plot_hover(self, event):
        if event.inaxes is self.ax:
            p = event.xdata, event.ydata
            _id = self.get_closest_observed(p)
            if _id is not None:
                self.callback(_id)

    def get_spatial_slice(self, epoch, data, _id=None):
        s = data[data[self.columns["epoch"]] == epoch]
        if _id:
            s = s[s[self.columns["id"]] == _id]

        return (
            s[self.columns["x"]].astype(np.float32),
            s[self.columns["y"]].astype(np.float32),
            s[self.columns["pred"]].astype(np.float32),
        )

    def plot(self, epoch):
        self.cur_epoch = epoch
        x, y, z = self.get_spatial_slice(epoch, self.df)

        self.scatter = self.ax.scatter(
            x, y, c=z, norm=self.norm, cmap=self.cmap, edgecolors="w"
        )

    def plot_active(self, _id):
        self.cur_id = _id
        x, y, z = self.get_spatial_slice(self.cur_epoch, self.df, _id)
        self.active_scatter = self.ax.scatter(
            x, y, c=z, norm=self.norm, cmap=self.cmap, edgecolors="y"
        )

    def update(self, epoch):
        self.scatter.remove()
        self.plot(epoch)
        self.update_active(self.cur_id)

    def update_active(self, _id):
        self.cur_id = _id
        self.active_scatter.remove()
        self.plot_active(_id)


class ST_TimeSeriesPlot(object):
    def __init__(self, columns, fig, ax, train_df, test_df):
        self.columns = columns
        self.fig = fig
        self.ax = ax

        self.train_df = train_df
        self.test_df = test_df

        self.df = pd.concat([self.train_df, self.test_df])

        self.min_test_epoch = np.min(self.test_df[columns["epoch"]])
        self.max_test_epoch = np.max(self.test_df[columns["epoch"]])
        self.min_train_epoch = np.min(self.train_df[columns["epoch"]])
        self.max_train_epoch = np.max(self.train_df[columns["epoch"]])

    def setup(self):
        pass

    def get_time_series(self, _id, data):
        d = self.df[self.df[self.columns["id"]] == _id]

        d = d.sort_values(by=self.columns["epoch"])

        epochs = d[self.columns["epoch"]]
        var = d[self.columns["var"]].astype(np.float32)
        pred = d[self.columns["pred"]].astype(np.float32)
        observed = d[self.columns["observed"]].astype(np.float32)

        return epochs, var, pred, observed

    def plot(self, _id):
        epochs, var, pred, observed = self.get_time_series(_id, self.df)

        self.var_plot = self.ax.fill_between(epochs, pred - var, pred + var)
        self.observed_scatter = self.ax.scatter(epochs, observed)
        self.pred_plot = self.ax.plot(epochs, pred)
        self.ax.set_xlim([self.min_train_epoch, self.max_test_epoch])

        self.min_line = self.ax.axvline(self.min_test_epoch)
        self.max_line = self.ax.axvline(self.max_test_epoch)

    def plot_cur_epoch(self, epoch):
        self.cur_epoch_line = self.ax.axvline(epoch, ymin=0.25, ymax=1.0)

    def update_cur_epoch(self, epoch):
        self.cur_epoch_line.remove()
        self.plot_cur_epoch(epoch)

    def update(self, _id):
        self.var_plot.remove()
        self.observed_scatter.remove()
        self.ax.lines.remove(self.pred_plot[0])
        self.min_line.remove()
        self.max_line.remove()
        self.plot(_id)


class ST_SliderPlot(object):
    def __init__(self, fig, ax, unique_vals, callback):
        print("slider init")
        self.fig = fig
        self.ax = ax
        self.unique_vals = unique_vals
        self.callback = callback

    def get_text_format(self, i):
        # datetime.fromtimestamp(1472860800).strftime("%Y-%m-%d %H")
        return datetime.fromtimestamp(i).strftime("%Y-%m-%d %H")
        # self.slider.valtext.set_text()
        # self.slider.valtext.set_text("")

    def set_text_format(self):
        self.slider.valtext.set_text("")

    def setup(self, start_val):
        self.slider = Slider(
            self.ax,
            "Date",
            np.min(self.unique_vals),
            np.max(self.unique_vals),
            valinit=start_val,
        )
        self.set_text_format()
        self.slider.on_changed(self.update)

    def update(self, i):
        cur_epoch_i = np.abs(self.unique_vals - i).argmin()
        cur_epoch = self.unique_vals[cur_epoch_i]
        self.set_text_format()

        datetime = self.get_text_format(cur_epoch)
        self.callback(datetime, cur_epoch)


def plot_polygon_collection(
    ax,
    geoms,
    norm,
    values=None,
    colormap="Set1",
    facecolor=None,
    edgecolor=None,
    alpha=1.0,
    linewidth=1.0,
    **kwargs
):
    """ Plot a collection of Polygon geometries """
    patches = []

    for poly in geoms:

        a = np.asarray(poly.exterior)
        if poly.has_z:
            poly = shapely.geometry.Polygon(zip(*poly.exterior.xy))

        patches.append(Polygon(a))

    patches = PatchCollection(
        patches,
        facecolor=facecolor,
        linewidth=linewidth,
        edgecolor=edgecolor,
        alpha=alpha,
        norm=norm,
        **kwargs
    )

    if values is not None:
        patches.set_array(values)
        patches.set_cmap(colormap)

    ax.add_collection(patches, autolim=True)
    ax.autoscale_view()
    return patches


class ST_GridPlot(object):
    def __init__(
        self,
        columns,
        col,
        fig,
        ax,
        df,
        cax_on_right,
        norm_on_training=True,
        label="",
        geopandas_flag=False,
    ):
        self.columns = columns
        self.col = col
        self.geopandas_flag = geopandas_flag

        self.fig = fig
        self.ax = ax

        self.df = df

        self.norm_on_training = norm_on_training
        self.right_flag = cax_on_right
        self.label = label
        self.cmap = None

    def get_spatial_slice(self, epoch):
        s = self.df[self.df[self.columns["epoch"]] == epoch]

        if len(s) == 0:
            return None, None, None

        return (
            s[self.columns["x"]].astype(np.float32),
            s[self.columns["y"]].astype(np.float32),
            s[self.columns[self.col]].astype(np.float32),
        )

    def get_data(self, epoch):
        x_train, y_train, z_train = self.get_spatial_slice(epoch)
        if x_train is None:
            return None, None

        z_train = np.array(z_train)

        s = np.c_[x_train, y_train]

        n = int(np.sqrt(z_train.shape[0]))
        grid_index = np.lexsort((s[:, 0], s[:, 1]))
        s = s[grid_index, :]
        z_train = z_train[grid_index]
        z_train = (z_train).reshape(n, n)
        return s, z_train

    def get_closest_observed(self, p):
        #d = np.array(self.df[[self.columns["x"], self.columns["y"]]]).astype(np.float32)

        cur_df = gpd.GeoDataFrame(self.cur_df, geometry=self.cur_df.geom)
        p = shapely.geometry.Point(p)
        geom_idx = cur_df.geometry.apply(lambda g: g.distance(p)).idxmin()
        geom_id = cur_df.loc[geom_idx][self.columns['id']]
        return geom_id


    def on_plot_hover(self, event):
        if event.inaxes is self.ax:
            p = event.xdata, event.ydata
            _id = self.get_closest_observed(p)
            if _id is not None:
                self.callback(_id)

    def setup(self, callback=lambda x: x):
        self.callback = callback
        df = self.df
        if self.norm_on_training:
            df = self.df

        self.norm = matplotlib.colors.Normalize(
            vmin=np.min(df[self.columns[self.col]]),
            vmax=np.max(df[self.columns[self.col]]),
        )

        # setup color bar
        self.divider = make_axes_locatable(self.ax)
        dir_str = "left"
        if self.right_flag:
            dir_str = "right"

        self.color_bar_ax = self.divider.append_axes(dir_str, size="5%", pad=0.05)
        self.fig.canvas.mpl_connect("motion_notify_event", self.on_plot_hover)

    def update(self, epoch):
        if self.geopandas_flag:

            # If grid_plot is init with zero patches then we need to create them
            if self.grid_plot is None:
                self.plot(epoch)
                return

            df = self.df[self.df[self.columns["epoch"]] == epoch]
            df = df.sort_values(self.columns["id"])

            self.cur_df = df
            print(df[self.columns[self.col]])
            self.grid_plot.set_array(df[self.columns[self.col]])
        else:
            s, z_train = self.get_data(epoch)

            if z_train is None:
                if hasattr(self, "grid_plot"):
                    self.grid_plot.set_data([[]])
            else:
                if hasattr(self, "grid_plot"):
                    self.grid_plot.set_data(z_train)
                else:
                    self.plot(epoch)
        if hasattr(self, "grid_plot"):
            return self.grid_plot
        else:
            return None

    def plot(self, epoch):
        if self.geopandas_flag:
            df = self.df[self.df[self.columns["epoch"]] == epoch]

            # If grid_plot is init with zero patches we cannot plot later
            if df.shape[0] == 0:
                self.grid_plot = None
                return

            df = df.sort_values(self.columns["id"])
            geo_series = gpd.GeoSeries(df["geom"])
            self.grid_plot = plot_polygon_collection(self.ax, geo_series, self.norm)
            self.grid_plot.set_array(df[self.columns[self.col]])
            self.cur_df = df
        else:
            s, z_train = self.get_data(epoch)
            if z_train is None:
                return

            # get extents
            min_x = s[0, 0]
            min_y = s[0, 1]
            max_x = s[s.shape[0] - 1, 0]
            max_y = s[s.shape[0] - 1, 1]

            self.grid_plot = self.ax.imshow(
                z_train,
                origin="lower",
                cmap=self.cmap,
                norm=self.norm,
                aspect="auto",
                extent=[min_x, max_x, min_y, max_y],
            )
            self.fig.colorbar(
                self.grid_plot, cax=self.color_bar_ax, orientation="vertical"
            )

        return self.grid_plot
