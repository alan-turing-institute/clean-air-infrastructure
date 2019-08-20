import sys
sys.path.append('/Users/ogiles/Documents/project_repos/clean-air-infrastructure/docker/')

from datasources import LondonBoundary, LAQNDatabase, HexGrid
from datasources.databases import  laqn_tables

from geoalchemy2.types import WKBElement
from geoalchemy2.shape import to_shape

import matplotlib.pyplot as plt

import pandas as pd 
    

if __name__ == '__main__':

    # Import datasources
    laqndb = LAQNDatabase(end = '2019-01-05', ndays = 10, secretfile = '.db_inputs_local_secret.json')
    # laqndb.update_site_list_table()
    # laqndb.update_reading_table()


    lb = LondonBoundary(secretfile = '.db_inputs_local_secret.json')
    hg = HexGrid(secretfile = '.db_inputs_local_secret.json')
    
    # Get the points just within that site
    sites_within_boundary = laqndb.get_sites_within_geom(lb.convex_hull)

    start_date = '2019-01-01'
    end_date = '2019-01-02'
    out = hg.get_interest_points(start_date, end_date)
    out2 = laqndb.get_interest_points(lb.convex_hull, start_date, end_date)
    
    # convexhull = lb.convex_hull
    # shape = to_shape(WKBElement(convexhull))

    # plt.plot(*shape.exterior.xy)
    # # plt.show()

    

    # for s in sites_within_boundary.all():
    #     plt.plot(*(to_shape(s.geom)).xy, 'or')
    #     print(s)

    # print(pd.read_sql(sites_within_boundary.statement, laqndb.dbcnxn.engine))
    # plt.show()

# q = s.query(Parent).filter(Parent.child.has(Child.value > 20))