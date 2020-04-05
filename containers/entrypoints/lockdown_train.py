import os
import json
from datetime import datetime, timedelta
import tensorflow as tf
from cleanair.parsers import ScootParser
from cleanair.scoot import (
    load_processed_data_from_file,
    save_model_to_file,
    train_sensor_model,
    parse_kernel
)

def main():
    parser = ScootParser()
    args = parser.parse_args()

    kernel_settings = {
        "rbf_ls=0.1_v=0.1": {
            "name": "rbf",
            "hyperparameters": {"lengthscale": 0.1, "variance": 0.1}
        },
        "matern32_ls=0.1_v=0.1": {
            "name": "matern32",
            "hyperparameters": {"lengthscale": 0.1, "variance": 0.1}
        },
        "matern52_ls=0.1_v=0.1": {
            "name":"matern52",
            "hyperparameters":{
                "lengthscale":0.1,
                "variance": 0.1
            }
        },
        "periodic_0.5": {
            "name": "periodic",
            "hyperparameters": {
                "period": 0.5,
                "lengthscale": 0.7,
                "variance": 4.5
            }
        },
    }

    # save the kernel settings
    kernel_settings_fp = os.path.join(
        args.root,
        args.experiment,
        "settings",
        "kernel_settings.json"
    )
    try:
        with open(kernel_settings_fp, "r+") as kernel_file:
            current_settings = json.load(kernel_file)
            current_settings.update(kernel_settings)
            kernel_file.seek(0)
            json.dump(current_settings, kernel_file)
    except FileNotFoundError:
        with open(kernel_settings_fp, "w") as kernel_file:
            json.dump(kernel_settings, kernel_file)

    # load the data settings
    normal_end = datetime.strptime(args.normal_start, "%Y-%m-%dT%H:%M:%S") + timedelta(hours=args.nhours * args.rolls)
    data_settings_fp = os.path.join(
        args.root,
        args.experiment,
        "settings",
        "data_settings.json"
    )
    with open(data_settings_fp, "r") as json_file:
        data_settings = json.load(json_file)

    # setup parameters
    optimizer = tf.keras.optimizers.Adam(0.001)
    epochs = 2000
    logging_epoch_freq = 100
    M = 24      # number of inducing points

    # loop through list of sensor. train model for each sensor
    for data in data_settings:
        if (
            data["normal_start"] >= args.normal_start and
            data["normal_start"] < normal_end.strftime("%Y-%m-%dT%H:%M:%S")
        ):
            for detector_id in data["detectors"]:
                for kernel_id in kernel_settings:
                    x_normal, y_normal = load_processed_data_from_file(
                        root=args.root,
                        experiment=args.experiment,
                        timestamp=data["normal_start"],
                        detector_id=detector_id
                    )
                    # get a kernel from settings
                    kernel = parse_kernel(kernel_settings[kernel_id])

                    # train model
                    model = train_sensor_model(
                        x_normal, y_normal, kernel, optimizer, epochs, logging_epoch_freq, M=M
                    )

                    # save model to file
                    save_model_to_file(
                        model,
                        root=args.root,
                        experiment=args.experiment,
                        timestamp=data["normal_start"],
                        detector_id=detector_id,
                        kernel_id=kernel_id
                    )

if __name__ == "__main__":
    main()
