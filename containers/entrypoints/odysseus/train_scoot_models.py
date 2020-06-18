"""Training scoot models for the air quality project."""

import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import tensorflow as tf

from odysseus.parsers import TrainScootModelParser
from odysseus.experiment import TrafficInstance
from odysseus.databases import TrafficQuery
from odysseus.dates import (
    NORMAL_BASELINE_START,
    NORMAL_BASELINE_END,
    LOCKDOWN_BASELINE_START,
    LOCKDOWN_BASELINE_END,
)
from odysseus.dataset import prepare_batch, TrafficDataset
from odysseus.modelling import parse_kernel
from odysseus.modelling import train_sensor_model

def main():
    """Main entrypoint function."""
    parser = TrainScootModelParser()
    parser.add_custom_subparsers()
    args = parser.parse_args()

    # get a list of detectors
    traffic_query = TrafficQuery(secretfile=args.secretfile)
    detectors = TrainScootModelParser.detectors_from_args(traffic_query, args)

if __name__ == "__main__":
    main()
