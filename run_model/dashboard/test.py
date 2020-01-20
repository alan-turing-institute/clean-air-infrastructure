import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import plotly.express as px

from shapely import wkt
import geopandas as gpd
import pandas as pd
import numpy as np

df = pd.read_excel(
    "https://github.com/chris1610/pbpython/blob/master/data/salesfunnel.xlsx?raw=True"
)
mgr_options = ['svgp', 'dgp']

app = dash.Dash()

def get_data():
    experiment_name = 'grid_exp'
    model = 'svgp'
    data_idx = 0
    param_idx = 0

    #load raw data
    processed_training_data = pd.read_csv('../experiments/{name}/data/data{data_idx}/normalised_training_data.csv'.format(name=experiment_name, data_idx=data_idx, index_col=0, low_memory=False))
    processed_predicting_data = pd.read_csv('../experiments/{name}/data/data{data_idx}/normalised_pred_data.csv'.format(name=experiment_name, data_idx=data_idx, low_memory=False))

    prediction = np.load('../experiments/{name}/results/{model}_param{param_idx}_data{data_idx}_y_pred.npy'.format(model=model, name=experiment_name, param_idx=param_idx, data_idx=data_idx), allow_pickle=True)

    training_period = prediction['train']
    testing_period = prediction['test']

    laqn_training_predictions = processed_training_data[processed_training_data['source']=='laqn']
    grid_training_predictions = processed_training_data[processed_training_data['source']=='hexgrid']

    laqn_predictions = processed_predicting_data[processed_predicting_data['source']=='laqn']
    grid_predictions = processed_predicting_data[processed_predicting_data['source']=='hexgrid']

    laqn_training_predictions['val'] = training_period['laqn']['pred']
    laqn_training_predictions['var'] = training_period['laqn']['var']

    laqn_predictions['val'] = testing_period['laqn']['pred']
    laqn_predictions['var'] = testing_period['laqn']['var']

    grid_training_predictions['val'] = training_period['hexgrid']['pred']
    grid_training_predictions['var'] = training_period['hexgrid']['var']
    grid_predictions['val'] = testing_period['hexgrid']['pred']
    grid_predictions['var'] = testing_period['hexgrid']['var']

    print(grid_training_predictions['val'])

    grid_predictions = pd.concat([grid_training_predictions, grid_predictions], axis=0)

    hexgrid_file = pd.read_csv('../visualisation/hexgrid_polygon.csv')
    grid_predictions = pd.merge(left=grid_predictions, right=hexgrid_file, how='left', left_on='point_id', right_on='point_id')
    grid_predictions['src_geom'] = grid_predictions['geom']
    grid_predictions['geom'] = grid_predictions['src_geom'].apply(wkt.loads)
    grid_predictions = gpd.GeoDataFrame(grid_predictions, geometry='geom')

    return laqn_training_predictions, laqn_predictions, grid_predictions

laqn_training_predictions, laqn_predictions, grid_predictions  = get_data()

def plot_polygon_collection(geoms):
    """ Plot a collection of Polygon geometries """
    patches = []
    i = 0
    for poly in geoms:
        print(i, len(geoms))
        i += 1

        a = np.asarray(poly.exterior)
        patches.append(
            go.Scatter(
                x = a[:, 0],
                y = a[:, 1]
            )
        )

    return patches


def get_fig_1():
    print(laqn_training_predictions.columns)
    df = laqn_training_predictions[laqn_training_predictions['measurement_start_utc']=='2019-11-01 00:00:00']
    fig = px.scatter(laqn_training_predictions, x="lon", y="lat", color="val")
    return fig

def get_fig():
    print('starting fig')
    df =  grid_predictions
    df = df[df['measurement_start_utc']=='2019-11-01 00:00:00']
    
    #fig = go.Figure(go.Choroplethmapbox(geojson=df.geom.to_json(), z=df.val, colorscale="Viridis"))
    df['geojson'] = df.geom.to_json()
    fig = go.Figure(px.choropleth_mapbox(df, geojson=df['geojson'], color='val', color_continuous_scale="Viridis", mapbox_style="carto-positron"))
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    
    #traces = plot_polygon_collection(df['geom'])
    print('traces')
    #fig = go.Figure(data=traces)
    return fig

def get_app(id_prefix=''):
    return html.Div(
        [
            dcc.Dropdown( id="Models"+id_prefix, options=[{ 'label': i, 'value': i } for i in mgr_options], value='Models'),
            dcc.Graph(figure=get_fig_1())
        ],
        style={
            'width': '50%',
            'display': 'inline-block'
        }
    )

app.layout = html.Div([
    html.H2("Validation Dashboard"),
    get_app('1'),
])


if __name__ == '__main__':
    app.run_server(debug=True)
