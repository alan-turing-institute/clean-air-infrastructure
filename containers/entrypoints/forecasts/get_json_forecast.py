import geopandas as gpd
from sqlalchemy import func
import json
from cleanair.databases.tables import AirQualityResultTable, MetaPoint, HexGrid
from cleanair.databases import DBReader
from cleanair.loggers import get_logger
from cleanair.decorators import db_query


class AirQualityJson(DBReader):
    def __init__(self, **kwargs):
        # Initialise parent classes
        super().__init__(**kwargs)

        # Ensure logging is available
        if not hasattr(self, "logger"):
            self.logger = get_logger(__name__)

    @db_query
    def get_forecast_json(self, instance_id):

        with self.dbcnxn.open_session() as session:

            out_sq = (
                session.query(
                    AirQualityResultTable.point_id,
                    AirQualityResultTable.measurement_start_utc,
                    AirQualityResultTable.NO2_mean,
                    AirQualityResultTable.NO2_var,
                    func.ST_GeometryN(HexGrid.geom, 1).label("geom")
                )
                .join(HexGrid, HexGrid.point_id == AirQualityResultTable.point_id)
                .filter(AirQualityResultTable.instance_id == instance_id
                )
            ).subquery()

        
            out = (
                session.query(
                    func.jsonb_build_object('type', 'Feature', 
                                            'id', out_sq.c.point_id,
                                            'geometry', func.ST_AsGeoJSON(out_sq.c.geom),
                                            'properties', func.jsonb_build_object('measurement_start_utc', out_sq.c.measurement_start_utc, 
                                                                                  'NO2_mean', out_sq.c.NO2_mean,
                                                                                  'NO2_var', out_sq.c.NO2_var) )
                )
            )

            return out

    def generate_json(self, *args, **kwargs):
        """Generate a csv file from a sqlalchemy query"""

        query = self.get_forecast_json(*args, **kwargs)

        for i, row in enumerate(query.yield_per(1000).enable_eagerloads(False)):
 
            row[0]['geometry'] = json.loads(row[0]['geometry'])

            yield row[0]
        



if __name__ == "__main__":

    read_results = AirQualityJson(
        secretfile="/Users/ogiles/Documents/project_repos/clean-air-infrastructure/.secrets/.db_secrets_ad.json"
    )

    # print(read_results.get_forecast_json(
    #         instance_id="9a44e654774f6a1fca9ed9a2586f6c26bdb6f6d5527933c7388874fbb95e76f7",
    #         output_type='sql'
    #     )
    # )
    

    df = read_results.generate_json(
            instance_id="9a44e654774f6a1fca9ed9a2586f6c26bdb6f6d5527933c7388874fbb95e76f7",
        )

    print(read_results.get_forecast_json(instance_id="9a44e654774f6a1fca9ed9a2586f6c26bdb6f6d5527933c7388874fbb95e76f7", output_type='sql'))

    quit()

    json_output = list(df)

    # print(json.dumps({'type': "FeatureCollection", "features": json_output}, indent = 4))


    with open('/Users/ogiles/Desktop/KAINOS_DATA/full_forecast.geojson', 'w') as f:
       json.dump({'type': "FeatureCollection", "features": json_output}, f, indent = 4)



    # df = read_results.get_forecast(
    #         instance_id="9a44e654774f6a1fca9ed9a2586f6c26bdb6f6d5527933c7388874fbb95e76f7",
    #         output_type="gdf",
    #     )

    # df.to_file('/Users/ogiles/Desktop/KAINOS_DATA/full_forecast.geojson', driver = 'GeoJSON')

    

