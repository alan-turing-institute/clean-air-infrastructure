# Datasets

One of the many challenges of the London Air Quality Project is efficiently handling the many spatio-temporal datasets.

This guide aims to give an overview of these datasets and describe how they fit together.

| Dataset name  | Provider | Description   |
|---------------|-------|---------------|
| [London Air Quality Network](https://www.londonair.org.uk/) (LAQN) |  Imperial College London | High accuracy air quality sensors every 15 minutes |
| [Copernicus satellite air quality forecasts](https://atmosphere.copernicus.eu/)| Copernicus, ECMWF | Hourly air quality forecasts derived from Satellite data |
| [Breath London](https://www.breathelondon.org/)| The cominity sensing network | Hourly air quality forecasts derived from low cost sensors data |
| [Scoot](https://www.breathelondon.org/)| The cominity sensing network | Traffic detector network via the S3 bucket maintained by TLF

## LAQN

The London Air Quality Network (LAQN) data provides detailed information about air pollution levels across London and the surrounding areas. It is a crucial resource for monitoring and analyzing air quality to understand pollution trends, identify sources of pollution, and inform public health decisions. Here's an overview of LAQN data:

### Overview of LAQN

- **Purpose:** LAQN aims to provide accurate and comprehensive air quality data to support research, policy-making, and public information efforts.
- **Managed by:** The network is managed by King's College London.
- **Coverage:** The network covers multiple monitoring sites across London and the South East of England.

## Satellite Data

Copernicus satellite data refers to the Earth observation data collected by the European Union's Copernicus program. This program operates a fleet of satellites that capture various types of data related to the Earth's atmosphere, land surface, oceans, and climate. These satellites provide valuable information about weather patterns, air quality, vegetation, ocean currents, and other environmental parameters.

ECMWF (European Centre for Medium-Range Weather Forecasts) is one of the organizations responsible for processing and analyzing the Copernicus satellite data. They utilize advanced data assimilation and modeling techniques to integrate the satellite data with other observational and model-based information, allowing for more accurate weather forecasting, climate monitoring, and environmental analysis. The ECMWF satellite data products are widely used by meteorologists, climate scientists, and policymakers for a range of applications, including weather prediction, climate research, and disaster management.

## Breath London

**Breathe London** is an initiative aimed at monitoring and improving air quality in London. It leverages advanced technologies to provide detailed, real-time air quality data to support research, public health, and policy-making efforts. Here's an overview of Breathe London:

### Overview of Breathe London

- **Purpose:** Breathe London aims to deliver high-resolution, real-time air quality data to inform residents, policymakers, and researchers about air pollution in the city and support efforts to improve air quality.
- **Managed by:** The project is a collaboration involving various stakeholders, including government agencies, research institutions, and environmental organizations.

## Scoot

### Overview of SCOOT (Split Cycle Offset Optimization Technique)

SCOOT is an advanced urban traffic control system designed to optimize traffic flow and reduce congestion in real-time. Widely used in London, it leverages real-time data from traffic detectors to dynamically adjust traffic signal timings at intersections.

### Key Features of SCOOT

- **Dynamic Signal Control:** Adjusts traffic signal timings continuously based on real-time traffic data.
- **Traffic Flow Optimization:** Aims to reduce congestion and improve traffic flow efficiency.
- **Wide Deployment:** Implemented in various cities, with extensive use in London.

[more info](scoot.md)
