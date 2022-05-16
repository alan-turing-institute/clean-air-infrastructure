# Codebase
The code for the London Air Quality project is concentrated in the [clean-air-infrastructure](https://github.com/alan-turing-institute/clean-air-infrastructure) repository.

A *model analysis tool* is in the [urbanair-analysis](https://github.com/alan-turing-institute/urbanair-analysis) repo.

The connected _Odysseus_ project's code is mostly in its own [tfl_traffic_analysis](https://github.com/warwick-machine-learning-group/tfl_traffic_analysis) repo, though it is built on the same database as cleanair, so database definitions etc. for Odysseus are in the cleanair repo.

## What is inside the containers directory?

| Name              | Description                                           |
| ----------------- | ----------------------------------------------------- |
| cleanair          | SQLAlchemy database definitions, Gaussian process modelling code, preprocessing algorithms, CLI "urbanair" |
| dockerfiles       | All of our dockerfiles for the project                |
| odysseus          | Scan statistics and traffic forecasting models        |
| requirements.txt  | A list of python dependencies for developing the cleanair project.    |
| scripts           | Python scripts for scheduled production jobs          |
| tests             | Python pytest for cleanair, odysseus, urbanair        |
| urbanair          | PI server code for both the Urbanair and Odysseus projects |

