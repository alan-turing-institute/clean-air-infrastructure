"""
LAQN
"""
from sqlalchemy import func, and_
import pandas as pd
from ..databases import interest_point_table, DBReader, aqe_tables, laqn_tables


class InterestPointReader(DBReader):
    """
    Read and process LAQN data
    """
    def query_interest_points(self, boundary_geom, include_sources=None, exclude_point_ids=None):
        """
        Return all interest points inside a boundary_geom (e.g. all the sites within London)
        Keyword arguments:
            include_sites -- A list of SiteCodes to include. If None then gets all
        """
        with self.dbcnxn.open_session() as session:
            _query = session.query(interest_point_table.InterestPoint).filter(interest_point_table.InterestPoint.location.ST_Within(boundary_geom))
            if include_sources:
                _query = _query.filter(interest_point_table.InterestPoint.source.in_(include_sources))
            if exclude_point_ids:
                _query = _query.filter(interest_point_table.InterestPoint.point_id.notin_(exclude_point_ids))
        return _query


    # def do_query(self, query):
    #     with self.dbcnxn.open_session() as session:
    #         result = session.query(query).all()
    #     return result

    def query_locations(self, boundary_geom, include_sources=None, exclude_point_ids=None):
        _query = self.query_interest_points(boundary_geom, include_sources, exclude_point_ids)
        return _query


    def query_interest_point_buffers(self, buffer_sizes, boundary_geom,
                                     include_sources=None, exclude_point_ids=None,
                                     num_seg_quarter_circle=8):
        """
        Return a set of buffers of size buffer_sizes around the interest points
        returned by self.query_interest_points
        """

        interest_point_query = self.query_interest_points(boundary_geom, include_sources, exclude_point_ids).subquery()

        def func_base(geom, size):
            return func.Geometry(func.ST_Buffer(func.Geography(geom), size, num_seg_quarter_circle))

        query_funcs = [func_base(interest_point_query.c.location, size).label('buffer_' + str(size)) for size in buffer_sizes]

        with self.dbcnxn.open_session() as session:
            _query = session.query(interest_point_query.c.point_id,
                                interest_point_query.c.source,
                                *query_funcs)

        return _query

    # def query_interest_point_readings(self, start_date, end_date, boundary_geom, include_sites):
    #     """
    #     Get readings from interest points between dates of interest, passing a list of sites to get readings for
    #     """

    #     # start_date = datetime.strptime(start_date, r"%Y-%m-%d").date()
    #     # end_date = datetime.strptime(end_date, r"%Y-%m-%d").date()

    #     subquery = self.query_interest_points(boundary_geom, include_sites).subquery()

    #     with self.dbcnxn.open_session() as session:
    #         result = session.query(subquery.c.SiteCode.label("id"),
    #                                laqn_tables.LAQNReading.MeasurementDateGMT.label('time'),
    #                                laqn_tables.LAQNReading.SpeciesCode,
    #                                laqn_tables.LAQNReading.Value
    #                                ).join(laqn_tables.LAQNReading)
    #         result = result.filter(laqn_tables.LAQNReading.MeasurementDateGMT.between(start_date, end_date))
    #         df_result = pd.read_sql(result.statement, self.dbcnxn.engine)

    #         df_result = pd.pivot_table(df_result,
    #                                    values='Value',
    #                                    index=['id', 'time'],
    #                                    columns='SpeciesCode', dropna=False).reset_index()
    #     return df_result
