# Scoot analysis

## Background on SCOOT

The SCOOT system essentially gives us count data for each detector. The aim of [SCOOT is traffic signal control](https://trlsoftware.com/products/traffic-control/scoot/). It uses the count data to optimise the control of signals at junctions.

There are some caveats with SCOOT.

- Sensors are sometimes recallibrated. The last know date of a sensor callibration was 10 Feb. How and when detectors are recallibrated is not known.
- The count data from one detector cannot be directly compared to another detector. We think this is due to the above recallibration problem.
- Upto 10% of sensor could be malfunctioning at any one time. It's not clear why they malfunction, or how we robustly detect malfunctions.
- 2 periods of missing data, beginning of Feb and beginning of Dec.

## Key dates

- Last known callibration of SCOOT detectors was 10th Feb.
- Most offices were closing in the week beginning 16th March. Obviously some offices were closing before this too.
- Lockdown started on Tuesday 24th of March.

## Overview of notebooks

`getting_started` has the installation instructions, checks you can connect to the database and runs a DB query.

`scoot` runs some more complex queries.

`borough_traffic` groups the detectors by which borough they lie in. We then apply aggregate statistics over time for each borough to get a breakdown of what the traffic is doing at a more local level.