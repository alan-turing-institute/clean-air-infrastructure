"""Matplotlib dashboard"""

import tkinter as tk
import pandas as pd
import numpy as np
import geopandas
import matplotlib
import os

import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button, RadioButtons
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.widgets import TextBox
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)

class DashBoard():
    """
        Dashboard class. A dashboard is made up of a collection of pages, and each
            pages is made up of widgets.
    """
    def __init__(self):
        self.bg_color = '#7f8c8d'
        self.experiments_root = '../experiments/'
        self.load_page('default')

    def plot(self):
        """
            Plot current figure
        """

        tk.mainloop()

    def load_page(self, name):
        """
            Redraw dashboard with the passed page name
        """

        pages = {
            'default': ComparePlots
        }

        self.page = pages[name](self)
        self.create_layout()
        self.draw_page()

        plt.tight_layout()

        canvas = FigureCanvasTkAgg(self.fig, master=self.master)  # A tk.DrawingArea.
        canvas.draw()
        canvas.get_tk_widget().pack(in_=self.page_frame)

        self.topbar = tk.Frame(self.master, width=self.screen_width-80, height=40, bg='blue')
        self.topbar.place(x=80, y=0)
        self.page.draw_topbar(self, self.topbar)

        self.plot()

    def draw_page(self):
        """
            Calculate the pages layout array and draw
        """

        page_layout = self.page.get_layout()

        layout = []
            
        for row in range(page_layout['n_rows']):
            row_arr = []

            for col in range(page_layout['n_cols']):
                row_arr.append(
                    self.layout[row, 1+col]
                )

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
        self.dpi=100

        self.page_frame = tk.Frame(self.master)
        self.page_frame.pack(fill=tk.BOTH, expand=1)

        self.fig = plt.figure(figsize=(self.screen_width/self.dpi, self.screen_height/self.dpi), dpi=self.dpi, frameon=True, facecolor=self.bg_color)

        page_layout = self.page.get_layout()

        #GridSpec: nrows, ncols, spaces between subplots
        #layout is an array of rows x cols
        self.layout = matplotlib.gridspec.GridSpec(
            page_layout['n_rows'], 
            1+page_layout['n_cols'], 
            figure=self.fig, 
            wspace=0, 
            hspace=0, 
            width_ratios=[0.05] + [0.95*w for w in page_layout['width_ratios']],
            height_ratios=page_layout['height_ratios']
        )


class Page():
    """
        Define a page in a DashBoard
    """

    def __init__(self, dashboard):
        self.dashboard=dashboard
        self.layout = None

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

    def load_experiment_data(self, experiment_name, model, data_idx, param_idx):
        processed_training_data = pd.read_csv(self.dashboard.experiments_root+'../experiments/{name}/data/data{data_idx}/normalised_training_data.csv'.format(name=experiment_name, data_idx=data_idx, index_col=0, low_memory=False))
        processed_predicting_data = pd.read_csv(self.dashboard.experiments_root+'../experiments/{name}/data/data{data_idx}/normalised_pred_data.csv'.format(name=experiment_name, data_idx=data_idx, low_memory=False))
        predictions = np.load(self.dashboard.experiments_root+'../experiments/{name}/results/{model}_param{param_idx}_data{data_idx}_y_pred.npy'.format(model=model, name=experiment_name, param_idx=param_idx, data_idx=data_idx), allow_pickle=True)

        return processed_training_data, processed_predicting_data, predictions


    def get_experiment_names(self):
        return [name for name in os.listdir(self.dashboard.experiments_root) if os.path.isdir(self.dashboard.experiments_root+name)]

    def get_experiment_config(self, experiment_name):
        config_fp = self.dashboard.experiments_root+experiment_name+'/meta/experiment.csv'
        config = pd.read_csv(config_fp)
        return config

    def get_correct_column_names(self, df):
        df['id'] = df['point_id']
        df['pred'] = df['val']
        df['var'] = 2*np.sqrt(df['var'])
        df['observed'] = df['NO2']
        df['datetime'] = df['measurement_start_utc']
        return df

    def process_source(self, src):
        #get src predictions
        src_training_predictions = self.processed_training_data[self.processed_training_data['source']==src]
        src_testing_predictions = self.processed_predicting_data[self.processed_predicting_data['source']==src]

        #merge predictions into raw data
        src_training_predictions['val'] = self.predictions_training[src]['pred']
        src_training_predictions['var'] = self.predictions_training[src]['var']

        src_testing_predictions['val'] = self.predictions_testing[src]['pred']
        src_testing_predictions['var'] = self.predictions_testing[src]['var']

        src_training_predictions = self.get_correct_column_names(src_training_predictions)
        src_testing_predictions = self.get_correct_column_names(src_testing_predictions)

        self.min_datetime = min(min(src_training_predictions['measurement_start_utc']), min(src_testing_predictions['measurement_start_utc']))
        self.max_datetime = max(max(src_training_predictions['measurement_start_utc']), max(src_testing_predictions['measurement_start_utc']))

        src_training_predictions['measurement_start_utc'] = pd.to_datetime(src_training_predictions['measurement_start_utc'])
        src_testing_predictions['measurement_start_utc'] = pd.to_datetime(src_testing_predictions['measurement_start_utc'])

        return src_training_predictions, src_testing_predictions

def submit(text):
    pass


class ComparePlots(Page):
    """
        Compare two experiments side by side
    """

    def __init__(self, dashboard):
        Page.__init__(self, dashboard)
        self.map_layer = 'hexgrid'
        self.sensor_layer = 'laqn'

    def draw(self, fig, layout):
        self.layout = layout
        self.fig = fig

        self.map_lhs = self.fig.add_subplot(self.layout[1][0])
        self.map_rhs = self.fig.add_subplot(self.layout[1][1])

        self.timeseries_lhs = self.fig.add_subplot(self.layout[2][0])
        self.timeseries_rhs = self.fig.add_subplot(self.layout[2][1])

        self.slider_lhs = self.fig.add_subplot(self.layout[3][0])
        self.slider_rhs = self.fig.add_subplot(self.layout[3][1])

    def create_dropdown(self, master, choices, default=None):
        tkvar1 = tk.StringVar(master)
        choices1 = choices
        if default:
            tkvar1.set(default) # set the default option
        else:
            tkvar1.set(choices[0]) # set the default option

        popupMenu1 = tk.OptionMenu(master, tkvar1, *choices1)
        popupMenu1.config(width=10, height=2)
        popupMenu1.pack(in_= master, side=tk.LEFT)
        return tkvar1, popupMenu1

        

    def update_timeseries(self, _id, scatter_plot, timeseries_plot):
        scatter_plot.update_active(_id)
        timeseries_plot.update(_id)
        self.fig.canvas.draw_idle()

    def update_experiment_data(self, experiment_name, model, data_id, param_id):
        processed_training_data, processed_predicting_data, predictions = self.load_experiment_data(experiment_name, model, data_id, param_id)

        self.processed_training_data = processed_training_data
        self.processed_predicting_data = processed_predicting_data
        self.predictions_training = predictions['train']
        self.predictions_testing = predictions['test']

        laqn_training_predictions, laqn_testing_predictions = self.process_source(self.sensor_layer)

        columns = {
            'id': 'point_id',
            'pred': 'val',
            'var': 'var',
            'observed': 'NO2',
            'x': 'lon',
            'y': 'lat',
            'datetime': 'measurement_start_utc',
            'epoch': 'measurement_start_utc',
        }

        splot = ST_ScatterPlot(columns ,self.fig, self.map_lhs, None, laqn_training_predictions)
        tplot = ST_TimeSeriesPlot(columns, self.fig, self.timeseries_lhs, laqn_training_predictions, laqn_testing_predictions)

        splot.setup(callback=lambda x: self.update_timeseries(x, splot, tplot))
        splot.plot(self.min_datetime)

        tplot.setup()
        tplot.plot(splot.cur_id)
        

    def update_dropdowns(self, master, experiment_name, tkvars, dropdowns):
        experiment_config = self.get_experiment_config(experiment_name)
        experiment_models = pd.unique(experiment_config['model_name'])
        experiment_param_ids = pd.unique(experiment_config['param_id'])
        experiment_data_ids = pd.unique(experiment_config['data_id'])

        def update_dropdown(tkvar, dropdown, choices):
            menu = dropdown['menu']
            menu.delete(0, 'end')
            tkvar.set(choices[0])
            for string in choices:
                menu.add_command(
                    label=string, 
                    command=lambda value=string: tkvar.set(value)
                )

        update_dropdown(tkvars[1], dropdowns[1], experiment_models)
        update_dropdown(tkvars[2], dropdowns[2], experiment_param_ids)
        update_dropdown(tkvars[3], dropdowns[3], experiment_data_ids)

        self.update_experiment_data(experiment_name, experiment_models[0], experiment_data_ids[0], experiment_param_ids[0])


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
        
        #TODO: flag if no experiments
        default = experiment_names[0]

        experiment_config = self.get_experiment_config(default)

        experiment_models = pd.unique(experiment_config['model_name'])
        experiment_param_ids = pd.unique(experiment_config['param_id'])
        experiment_data_ids = pd.unique(experiment_config['data_id'])

        print(experiment_param_ids)

        self.update_experiment_data(experiment_names[0], experiment_models[0], experiment_data_ids[0], experiment_param_ids[0])


        #TODO: compress duplicate code?

        tkvar_exp_lhs, topbar_exp_lhs = self.create_dropdown(master = self.topbar_frame_lhs, choices = experiment_names, default=default)
        tkvar_model_lhs, topbar_model_lhs = self.create_dropdown(master = self.topbar_frame_lhs, choices = experiment_models)
        tkvar_params_lhs, topbar_params_lhs = self.create_dropdown(master = self.topbar_frame_lhs, choices = experiment_param_ids)
        tkvar_data_lhs, topbar_data_lhs = self.create_dropdown(master = self.topbar_frame_lhs, choices=experiment_data_ids)

        tkvar_exp_rhs, topbar_exp_rhs = self.create_dropdown(master = self.topbar_frame_rhs, choices = experiment_names, default=default)
        tkvar_model_rhs, topbar_model_rhs = self.create_dropdown(master = self.topbar_frame_rhs, choices = experiment_models)
        tkvar_params_rhs, topbar_params_rhs = self.create_dropdown(master = self.topbar_frame_rhs, choices = experiment_param_ids)
        tkvar_data_rhs, topbar_data_rhs = self.create_dropdown(master = self.topbar_frame_rhs, choices=experiment_data_ids)


        tkvar_exp_lhs.trace('w', lambda *args: self.update_dropdowns(
            self.topbar_frame_lhs, 
            tkvar_exp_lhs.get(), 
            [tkvar_exp_lhs, tkvar_model_lhs, tkvar_params_lhs, tkvar_data_lhs],
            [topbar_exp_lhs, topbar_model_lhs, topbar_params_lhs, topbar_data_lhs]
        ))

        tkvar_exp_rhs.trace('w', lambda *args: self.update_dropdowns(
            self.topbar_frame_rhs, 
            tkvar_exp_rhs.get(), 
            [tkvar_exp_rhs, tkvar_model_rhs, tkvar_params_rhs, tkvar_data_rhs],
            [topbar_exp_rhs, topbar_model_rhs, topbar_params_rhs, topbar_data_rhs]
        ))


    def get_layout(self):
        """
            Return 2 columns and two rows
        """
        return {
            'n_rows': 4,
            'n_cols': 2,
            'width_ratios': [0.5, 0.5],
            'height_ratios': [0.05, 0.6, 0.3-0.05, 0.1]
        }
    
class ST_ScatterPlot(object):
    def __init__(self, columns, fig, ax, norm, df):
        self.columns = columns

        self.fig = fig
        self.ax = ax

        self.df = df
        self.cmap=None

        if norm is None:
            self.norm = matplotlib.colors.Normalize(vmin=np.min(self.df[self.columns['pred']]),vmax=np.max(self.df[self.columns['pred']]))
        else:
            self.norm = norm


        self.cur_epoch = None

    def setup(self, callback):
        self.callback = callback
        #assume default id is the first one
        self.plot_active(self.df[self.columns['id']].iloc[0])
        self.fig.canvas.mpl_connect('button_release_event', self.on_plot_hover)           

    def get_closest_observed(self, p):
        d = np.array(self.df[[self.columns['x'], self.columns['y']]]).astype(np.float32)
        dists = np.sum((d - p)**2, axis=1)
        i =  np.argmin(dists)
        if dists[i] <= 1e-4:
            return self.df.iloc[i][self.columns['id']]
        else:
            return None

    def on_plot_hover(self, event):
        if event.inaxes is self.ax:
            p = event.xdata, event.ydata
            _id = self.get_closest_observed(p)
            if _id is not None:
                self.callback(_id)

    def get_spatial_slice(self, epoch, data, _id=None):
        s = data[data[self.columns['epoch']] == epoch]
        if _id:
            s = s[s[self.columns['id']] == _id]

        return s[self.columns['x']].astype(np.float32), s[self.columns['y']].astype(np.float32), s[self.columns['pred']].astype(np.float32)

    def plot(self, epoch):
        self.cur_epoch = epoch
        x, y, z = self.get_spatial_slice(epoch, self.df)

        self.scatter = self.ax.scatter(x, y, c=z, norm=self.norm, cmap=self.cmap, edgecolors='w')

    def plot_active(self, _id):
        self.cur_id = _id
        x, y, z = self.get_spatial_slice(self.cur_epoch, self.df, _id)
        self.active_scatter = self.ax.scatter(x, y, c=z, norm=self.norm, cmap=self.cmap, edgecolors='y')

    def update(self, epoch):
        self.scatter.remove()
        self.plot(epoch)
        self.update_active(self.cur_id)

    def update_active(self, _id):
        self.cur_id = _id
        self.active_scatter.remove()
        self.plot_active(_id)

class ST_TimeSeriesPlot(object):
    def __init__(self,  columns, fig, ax, train_df, test_df):
        self.columns = columns
        self.fig = fig
        self.ax = ax

        self.train_df = train_df
        self.test_df = test_df

        self.min_test_epoch = np.min(self.train_df[columns['epoch']])
        self.max_test_epoch = np.max(self.train_df[columns['epoch']])
        self.test_start_epoch = self.min_test_epoch

    def setup(self):
        pass

    def get_time_series(self, _id, data):
        d =  self.train_df[self.train_df[self.columns['id']] == _id]

        d = d.sort_values(by=self.columns['epoch'])


        epochs = d[self.columns['epoch']]
        var = d[self.columns['var']].astype(np.float32)
        pred = d[self.columns['pred']].astype(np.float32)
        observed = d[self.columns['observed']].astype(np.float32)

        return epochs, var, pred, observed

    def plot(self, _id):
        epochs, var, pred, observed = self.get_time_series(_id, self.train_df)

        self.var_plot = self.ax.fill_between(epochs, pred-var, pred+var)
        self.observed_scatter = self.ax.scatter(epochs, observed)
        self.pred_plot = self.ax.plot(epochs, pred)
        self.ax.set_xlim([self.min_test_epoch,self.max_test_epoch ])

        self.min_line = self.ax.axvline(self.min_test_epoch)
        self.max_line = self.ax.axvline(self.max_test_epoch)
        self.test_start_line = self.ax.axvline(self.test_start_epoch)

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
