#!/bin/bash
kernels=(matern32, rbf, periodic)   # names of kernels
# detector_batch_size = 100         # number of detectors in one batch
# num_detectors = 12421             # total number of detectors in our db

# testing params
detector_batch_size = 10
num_detectors = 100

for kernel_id in ${kernels[@]};
do
    for batch in $(seq 0 $detector_batch_size $num_detectors);
    do
        python /app/lockdown_train.py \
            -k $kernel_id \
            -b 2020-02-10 \
            -e 2020-03-03 \
            -t normal \
            -c pearl \
            --root ~/experiments \
            -x daily \
            -m svgp \
            -i 24 \
            -s ~/.secrets/db_secrets.json \
            --epochs 2000 \
            --batch_start $batch \
            --batch_size $detector_batch_size &
        python /app/lockdown_train.py \
            -k $kernel_id \
            -b 2020-03-23 \
            -e 2020-04-13 \
            -t lockdown \
            -c pearl \
            --root ~/experiments \
            -x daily \
            -m svgp \
            -i 24 \
            -s ~/.secrets/db_secrets.json \
            --epochs 2000 \
            --batch_start $batch \
            --batch_size $detector_batch_size &
