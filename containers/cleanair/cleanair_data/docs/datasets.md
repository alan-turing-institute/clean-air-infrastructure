# Datasets

One of the many challenges of the London Air Quality Project is efficiently handling the many spatio-temporal datasets.

This guide aims to give an overview of these datasets and describe how they fit together.

| Dataset Name                                                                                         | Provider                | Description                                           |
|-----------------------------------------------------------------------------------------------------|-------------------------|-------------------------------------------------------|
| [London Air Quality Network](https://www.londonair.org.uk/) (LAQN)                                  | Imperial College London | High accuracy air quality sensors every 15 minutes   |
| [Copernicus satellite air quality forecasts](https://atmosphere.copernicus.eu/)                     | Copernicus, ECMWF       | Hourly air quality forecasts derived from Satellite data |
| [SCOOT traffic data](https://s3.console.aws.amazon.com/s3/buckets/surface.data.tfl.gov.u)           | Transport for London    | Traffic flow and congestion data at junctions        |
| [Breathe London Sensor Network](https://api.breathelondon.org/api/ListSensors?key=)                 | Breathe London          | Data from a network of sensors monitoring air quality across the city |

## APIs

### LAQN

**URL:** [https://api.erg.ic.ac.uk/AirQuality/Data/Site/SiteCode=KC1/StartDate=2022-06-01/EndDate=2022-12-01/Json](https://api.erg.ic.ac.uk/AirQuality/Data/Site/SiteCode=KC1/StartDate=2022-06-01/EndDate=2022-12-01/Json)

- Provides raw air quality data based on the parameters:
  - **SiteCode:** Identifier for the monitoring site.
  - **SpeciesCode:** Refers to the specific pollutant or species monitored.
  - **StartDate** and **EndDate:** Defines the data range. The start date is inclusive, while the end date is exclusive.
- The default time granularity is **hourly**, and the data is returned in JSON format.
- The response includes readings for all species and the corresponding site code.
- **Historical data is available.**

---

### Satellite Data

**URL:** [https://ads.atmosphere.copernicus.eu/cdsapp#!/dataset/cams-europe-air-quality-forecasts?tab=form](https://ads.atmosphere.copernicus.eu/cdsapp#!/dataset/cams-europe-air-quality-forecasts?tab=form)

- **Historical data** is accessible up to **30-04-2024** using the API key, which is functional.
- Currently (as of December 2024), there is a known issue with accessing data from the **ECMWF satellite**. For more details, refer to: [https://forum.ecmwf.int/t/cds-ads-and-ewds-down-until-further-notice/8015](https://forum.ecmwf.int/t/cds-ads-and-ewds-down-until-further-notice/8015).

---

### SCOOT

**URL:** [https://s3.console.aws.amazon.com/s3/buckets/surface.data.tfl.gov.u](https://s3.console.aws.amazon.com/s3/buckets/surface.data.tfl.gov.u)

- **Data Fields:**
  - **SCOOTLinkID:** Unique identifier for the SCOOT link.
  - **LinkDescription:** Description of the junction location, often by road name.
  - **Date:** Date of the recorded data.
  - **TwentyFourHourVehicleFlowTotal:** Total traffic flow observed over a 24-hour period across all links approaching the junction.
  - **FlowDataCompletenessPercentage:** Indicates the completeness of the dataset; 100% means the data is fully available.
  - **AverageCongestionPercentage:** The average congestion level within a 24-hour period.
  - **CongestionDataCompletenessPercentage:** Similar to flow completeness, indicates the percentage of available congestion data.

---

### Breathe London

**URL:** [https://api.breathelondon.org/api/ListSensors?key=](https://api.breathelondon.org/api/ListSensors?key=)

- Provides a list of sensors and their data for air quality monitoring.
- The API key is universal for all users.
