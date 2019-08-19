import sys
sys.path.append('/Users/ogiles/Documents/project_repos/clean-air-infrastructure/docker/')

from datasources import LondonBoundary, LAQNDatabase
from datasources.databases import  laqn_tables

from geoalchemy2.types import WKBElement
from geoalchemy2.shape import to_shape

import matplotlib.pyplot as plt

import pandas as pd 
    

if __name__ == '__main__':

    laqndb = LAQNDatabase(end = '2019-01-01', ndays = 2, secretfile = '.db_inputs_local_secret.json')
    # laqndb.update_site_list_table()
    # laqndb.update_reading_table()


    lb = LondonBoundary(secretfile = '.db_inputs_local_secret.json')
    
    # Get the boundary of London as a convex hull
    convexhull = lb.convex_hull()
    shape = to_shape(WKBElement(convexhull))

    plt.plot(*shape.exterior.xy)
    # plt.show()

    # Get the points just within that site
    sites_within_boundary = laqndb.get_sites_within_geom(convexhull)

    for s in sites_within_boundary.all():
        plt.plot(*(to_shape(s.geom)).xy, 'or')
        print(s)

    print(pd.read_sql(sites_within_boundary.statement, laqndb.dbcnxn.engine))
# plt.show()

# q = s.query(Parent).filter(Parent.child.has(Child.value > 20))