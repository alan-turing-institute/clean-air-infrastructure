# Datasets

One of the many challenges of the London Air Quality Project is efficiently handling the many spatio-temporal datasets.
This guide aims to give an overview of these datasets, how they fit together and how to download a dataset.

***

## Summary of datasets

| Dataset name  | Provider | Description   |
|---------------|-------|---------------|
| [London Air Quality Network](https://www.londonair.org.uk/) (LAQN) |  Imperial College London | High accuracy air quality sensors every 15 minutes |
| [Copernicus satellite air quality forecasts](https://atmosphere.copernicus.eu/)| Copernicus, ECMWF | Hourly air quality forecasts derived from Satellite data |
| SCOOT | Transport for London | Approximately 10,000 sensors designed for junction monitoring |


***

## Downloading a raw dataset

This part of the guide describes how to download individual datasets (e.g. LAQN, SCOOT) as a CSV file.
You will need to be [connected to the Azure PostgreSQL database](secretfile.md#production-database) for this part of the guide.


## Downloading a pre-processed dataset

This part of the guide describes how to download a pre-processed dataset for use in a model.
