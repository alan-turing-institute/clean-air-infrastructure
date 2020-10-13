from cleanair.databases import DBWriter
from cleanair.databases.tables import JamCamMetaData


def test_jamcam_metadata_query(secretfile, connection):

    db_instance = DBWriter(
        secretfile=secretfile, connection=connection, initialise_tables=False
    )

    with db_instance.dbcnxn.open_session() as session:
        query = session.query(JamCamMetaData)
        results = query.all()
        first = query.first()

        print(results)

        assert False
