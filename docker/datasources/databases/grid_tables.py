from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
import numpy as np 
Base = declarative_base()

class Grid(Base):
    """Table of Grid points sites"""
    __tablename__ = "grid_points"

    id = Column(Integer, nullable=False, primary_key = True)
    Latitude = Column(DOUBLE_PRECISION)
    Longitude = Column(DOUBLE_PRECISION)
    geom = Column(Geometry(geometry_type="POINT", srid=4326, dimension=2, spatial_index=True))

    def __repr__(self):
        return "<Grid(ID='%s', Latitude='%s', Longitude='%s'" % (
                self.id, self.Latitude, self.Longitude)

def initialise(engine):
    Base.metadata.create_all(engine)


def build_grid(grid_size = 100, grid_lats = (51.4, 51.6), grid_lons = (-0.2, 0)):
    """
    Create a grid and return as a list of Grid objects
    """
    
    total_size = grid_size**2
    grid_min_lat, grid_max_lat = grid_lats[0], grid_lats[1]
    grid_min_lon, grid_max_lon = grid_lons[0], grid_lons[1]

    lats = np.linspace(grid_min_lat, grid_max_lat, grid_size)
    lons = np.linspace(grid_min_lon, grid_max_lon, grid_size)

    lat_diff = np.abs(lats[1]-lats[0])
    lon_diff = np.abs(lons[1]-lons[0])

    #unique id for each lat/lon location
    grid_ids = np.expand_dims(range(total_size), -1).astype(np.int)

    grid_points = np.array([[lat, lon]  for lat in lats for lon in lons])
    
    grid_points_df = pd.DataFrame(grid_points, columns=['lat', 'lon'])
    grid_points_df['id'] = grid_ids

    grid_points_df['geom_wkt'] = grid_points_df.apply(lambda row: get_polygon(row, lat_diff,lon_diff) , axis=1)

    return grid_points_df[['id', 'lat', 'lon', 'geom_wkt']]