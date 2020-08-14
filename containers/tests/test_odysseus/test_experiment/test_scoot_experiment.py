"""Tests"""


import pandas as pd

from odysseus.experiment import ScootExperiment
from odysseus.databases import TrafficQuery

def test_scoot_experiment(scoot_writer, frame: pd.DataFrame, secretfile, scoot_detectors, scoot_start, scoot_upto):
    print(frame)
    scoot_writer.update_remote_tables()
    scoot_xp = ScootExperiment(frame=frame, secretfile=secretfile)
    readings = scoot_xp.scoot_readings(output_type="df", start=scoot_start)
    traffic_query = TrafficQuery(secretfile=secretfile)
    detectors = traffic_query.scoot_detectors(offset=0, limit=10, borough="Westminster", output_type="df")['detector_id']
    readings = traffic_query.scoot_readings(output_type="df", start=scoot_start)

    print(detectors)
    print(readings)


    #datasets = scoot_xp.load_datasets(scoot_detectors, scoot_start, scoot_upto)
   

    print(datasets)