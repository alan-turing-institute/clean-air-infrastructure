# """
# Hexgrid
# """
# from sqlalchemy import func, cast, String
# from ..databases import DBReader
# from ..databases.tables import HexGrid


# class HexGridReader(DBReader):
#     """
#     Class to interface with the glahexgrid database table
#     """
#     def __init__(self, *args, **kwargs):
#         # Initialise parent classes
#         super().__init__(*args, **kwargs)

#     def query_interest_points(self):
#         """
#         Return interest points where interest points are
#             the geometric centroids of the hexgrid as a query object
#         """

#         with self.dbcnxn.open_session() as session:
#             interest_points = session.query((cast(HexGrid.ogc_fid, String(4))).label('id'),
#                                             func.ST_Y(func.ST_Centroid(HexGrid.wkb_geometry)).label("lat"),
#                                             func.ST_X(func.ST_Centroid(HexGrid.wkb_geometry)).label("lon"),
#                                             func.ST_Centroid(HexGrid.wkb_geometry).label('geom'))
#         return interest_points
