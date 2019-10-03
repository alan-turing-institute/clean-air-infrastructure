# """
# London Boundary
# """
# from sqlalchemy import func
# from ..databases import DBReader, londonboundary_table


# class LondonBoundaryReader(DBReader):
#     """
#     Class to interface with the londonboundary database table
#     """
#     def __init__(self, *args, **kwargs):
#         # Initialise parent classes
#         super().__init__(*args, **kwargs)

#     @property
#     def convex_hull(self):
#         """
#         Return the convex hull of the London Boundary as a query object
#         """
#         with self.dbcnxn.open_session() as session:
#             hull = session.scalar(func.ST_ConvexHull(func.ST_Collect(londonboundary_table.LondonBoundary.geom)))
#         return hull

#     def query_all(self):
#         """
#         Return all rows from the database table as an sql query object
#         """
#         with self.dbcnxn.open_session() as session:
#             rows = session.query(londonboundary_table.LondonBoundary)
#         return rows
