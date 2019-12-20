"""
Methods to choose sensors to validate on.
"""

import random
import datetime
import numpy as np
import pandas as pd
import geopandas as gpd
import networkx as nx
import osmnx as ox
from haversine import haversine, Unit
from shapely.ops import nearest_points

def sensor_choice(sdf, k, choice='random', distance="haversine", r=0.1, x="Longitude", y="Latitude"):
    """
    Choose k sensors to predict on.

    Parameters
    ___

    sdf : DataFrame
        Contains sensor info.
        If 'nearest' is not a key, then we will compute
        the nearest node to each sensor in df.

    k : int
        Number of sensors to choose.

    choice : str, optional
        The method to choose sensors.
        If 'random' then sensors will be chosen with random probability.
        If 'buffer' then no sensors within radius r will be chosen
        in the same validation set.

    distance : str, optional
        Distance metric when using the 'buffer' choice parameter, 
        e.g. 'haversine', 'road', 'manhattan', etc.

    r : float, optional
        Radius in kilometers.

    x : str, optional
        Name of the x coor in the df.

    y : str, optional
        Name of the y coor in the df.

    Returns
    ___

    set
        Set of k sensors.
        All sensors will be at least r distance away from eachother.

    Notes
    ___

    If the 'buffer' choice is made, then we choose k sensors such that
    no two chosen sensors are within radius r of each other.
    The distance between the two sensors is computed by the 'distance' metric.
    """
    indices = list(sdf.index)
    if choice == 'random':
        return random.sample(indices, k)
    elif choice == 'buffer':
        S = set()   # set of sensors to choose
        if distance == "road":
            # get dataframes, graphs and lookups for graph algorithms
            G, ndf, edf = get_graph_nodes_edges()
            if "nearest" not in sdf.columns:
                sdf["nearest"] = get_node_nearest_sensor(ndf, sdf)

        while len(S) < k:
            # randomly choose sensor
            sensor = random.choice(indices)
            sensor_y, sensor_x = sdf.at[sensor, y], sdf.at[sensor, x]
            add = True

            # get shortest path from sensor to all other nodes
            if distance == "road":
                shortest_paths = nx.single_source_dijkstra_path_length(
                    G, sdf['nearest'][sensor], cutoff=r, weight="length"
                )

            # iterate through all sensors in S
            for index, row in sdf.loc[S].iterrows():

                if distance == "haversine":
                    length = haversine(
                        (sensor_y, sensor_x),
                        (row[y], row[x])
                    )
                elif distance == "road":
                    length = shortest_paths[sdf.at[index, 'nearest']]

                # check if condition is broken if we add this sensor
                if length <= r:
                    add = False
                    break

            if add:     # add sensor if it is valid
                S.add(sensor)

        return S

def remove_closed_sensors(sdf, removed_closed=True, closure_date=None):
    """
    Remove sensors that have closed.
    
    Parameters
    ___

    sdf : DataFrame
        Sensor data.

    removed_closed : bool, optional
        If the date the sensor closed is less than `closure_date` then
        remove the sensor.

    closure_date : str, optional
        If `removed_closed` is true, then remove all sensors that closed before this date.

    Returns
    ___
    
    DataFrame
    """
    if closure_date is None:
        closure_date = datetime.datetime.now().strftime("YYYY-MM-DD HH:MM:SS")
    if removed_closed:
        sdf = sdf[(pd.isnull(sdf["date_closed"])) | (sdf["date_closed"] > closure_date)]
    return sdf

def get_node_nearest_sensor(ndf, sdf):
    """
    Get the nearest node to a each sensor.

    Parameters
    ___

    ndf : DataFrame
        Nodes dataframe, each with a geometry (Point).

    sdf : DataFrame
        Sensors dataframe, each with a geometry (Point).

    Returns
    ___

    Series
        Indexed by sensor ids, values are node ids.

    Notes
    ___

    ToDo: this is implemented in Geopandas and is VERY SLOW.
    We should use PostGIS instead by creating buffers around
    sensors and finding the intersection with the road network.
    """
    # unary union of the gpd2 geomtries 
    pts3 = ndf.geometry.unary_union

    def near(point, pts=pts3):
        # find the nearest point and return the corresponding nodeId value
        nearest = ndf.geometry == nearest_points(point, pts)[1]
        return ndf[nearest].index.get_values()[0]

    # for each laqn sensor, find the nearest vertex in the graph
    return sdf.apply(lambda row: near(row.geom), axis=1)

def get_graph_nodes_edges(node_fp=None, edge_fp=None, from_db=True, from_osmnx=False):
    """
    Get a graph, node dataframe, and edge dataframe of the road network.

    By default, the graph will be loaded from the database.

    Parameters
    ___

    node_fp : str, optional
        Filepath to nodes shapefile.

    edge_fp : str, optional
        Filepath to edges shapefile.

    from_db : bool, optional
        If true, read nodes and edges from database.

    from_osmnx : bool, optional
        If true, get data by querying osmnx.

    Returns
    ___

    G : nx.MultiDiGraph
        Multi directed graph.

    ndf : gpd.GeoDataFrame
        Node dataframe.

    edf : gpd.GeoDataFrame
        Edge dataframe.
        
    """
    if from_db:
        # get a node and edge dataframe from the database
        raise NotImplementedError()
    elif from_osmnx:
        raise NotImplementedError()
    else:
        # get filepaths if None
        print("# Loading nodes and edges from files.")

        # load dataframes from files
        ndf = gpd.GeoDataFrame.from_file(node_fp)
        edf = gpd.GeoDataFrame.from_file(edge_fp)

    # check crs
    if ndf.crs != edf.crs:
        print("WARNING: Node dataframe and edge dataframe crs are inconsistent. Trying to correct by setting both to 4326")
        ndf = ndf.to_crs({'init': 'epsg:4326'})
        edf = edf.to_crs({'init': 'epsg:4326'})

    # fix indices and column names
    ndf = ndf.set_index("TOID")
    edf['u'] = edf['startNode'].copy()
    edf['v'] = edf['endNode'].copy()
    edf = edf.drop(['startNode', 'endNode'], axis=1)

    # get lat and lon (y and x respectively) for nodes
    ndf['x'] = ndf['geometry'].x
    ndf['y'] = ndf['geometry'].y

    # check for repeated multi edges
    edf["key"] = add_keys_to_duplicate_edges(edf)

    # remove startnodes and endnodes that are not in ndf
    nodes = set(ndf.index)
    keep_edges = [u in nodes and v in nodes for u, v in zip(edf['u'], edf['v'])]
    edf = edf[keep_edges]

    # add names to dataframes
    ndf.gdf_name = 'nodes'
    edf.gdf_name = 'edges'

    # convert to graph from dataframes
    print("# Converting geodataframes to a graph")
    G = ox.gdfs_to_graph(ndf, edf)

    return G, ndf, edf

def add_keys_to_duplicate_edges(edf):
    """
    Given an edge dataframe, assign keys to multi edges.

    Parameters
    ___

    edf : Dataframe
        Must have u and v columns.

    Returns
    ___

    Series
        The same index but with a column of keys attached.

    """
    # create a new series
    K = pd.Series(
        data=np.zeros(edf.shape[0]),
        index=edf.index
    )
    
    # count how many times an edge is in edf
    count_edges = {}
    for i, u, v in zip(edf.index, edf["u"], edf["v"]):
        if (u, v) in count_edges:
            count_edges[(u,v)].append(i)
        elif (v, u) in count_edges:
            count_edges[(v, u)].append(i)
        else:
            count_edges[(u, v)] = [i]
        
    # assign keys to the series
    for (u, v), l in count_edges.items():
        k = 0
        for i in l:
            K.at[i] = k
            k += 1

    return K
