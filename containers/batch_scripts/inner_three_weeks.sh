#!/bin/bash

# detector_batch_size = 100         # number of detectors in one batch
# num_detectors = 12421             # total number of detectors in our db

# testing params
detector_batch_size=10;
num_detectors=100;

# iterate over kernels
for kernel_id in matern32 rbf periodic
do
    # iterate over detector batches
    for batch in $(seq 0 $detector_batch_size $num_detectors);
    do
        # iterate over number of inducing points
        for i in 24 48
        do
            python /app/lockdown_train.py \
                -k $kernel_id \
                -b 2020-02-10 \
                -e 2020-03-02 \
                -t normal \
                -c pearl \
                --root ~/experiments \
                -x three \
                -m svgp \
                -i $i \
                -s ~/.secrets/db_secrets.json \
                --epochs 2000 \
                --batch_start $batch \
                --batch_size $detector_batch_size \
                --nweeks 3 &
            python /app/lockdown_train.py \
                -k $kernel_id \
                -b 2020-03-23 \
                -e 2020-04-13 \
                -t lockdown \
                -c pearl \
                --root ~/experiments \
                -x three \
                -m svgp \
                -i $i \
                -s ~/.secrets/db_secrets.json \
                --epochs 2000 \
                --batch_start $batch \
                --batch_size $detector_batch_size \
                --nweeks 3 &
        done;
    done;
done;
