# Steps to retrieve and store datasets from an API

## LAQN

### Types of Data Collected

1. **Pollutant Measurements:**
   - **Nitrogen Dioxide (NO2):** A common air pollutant from vehicle emissions and industrial activities.
   - **Particulate Matter (PM10 and PM2.5):** Tiny particles that can penetrate the lungs and cause health issues.
   - **Ozone (O3):** A gas formed by reactions between sunlight and pollutants like volatile organic compounds (VOCs) and nitrogen oxides (NOx).
   - **Sulphur Dioxide (SO2):** A gas produced by burning fossil fuels containing sulfur.
   - **Carbon Monoxide (CO):** A gas produced by incomplete combustion of carbon-containing fuels.
   - **Other Pollutants:** Depending on the site, additional pollutants like VOCs and lead may be measured.

2. **Meteorological Data:**
   - **Temperature:** Ambient temperature readings.
   - **Wind Speed and Direction:** Important for understanding pollution dispersion.
   - **Humidity:** Moisture levels in the air.
   - **Solar Radiation:** Sunlight intensity, which can affect photochemical reactions in the atmosphere.

### Data Accessibility

- **Real-Time Data:** LAQN provides real-time air quality data that can be accessed through its website or API.
- **Historical Data:** Users can access historical air quality data for analysis and research purposes.
- **Data Format:** Data is available in various formats, including JSON, CSV, and through web-based dashboards.

### Accessing LAQN Data

#### Using the LAQN Website

1. **Visit the LAQN website:** The primary portal for accessing LAQN data.
2. **Data Dashboard:** The website typically features a dashboard where users can view real-time and historical air quality data for different monitoring sites.
3. **Data Downloads:** Users can download data for specific time periods and pollutants.

#### Using the LAQN API

1. **API Endpoint:** Access the LAQN API to programmatically retrieve air quality data.
2. **Parameters:** Specify parameters such as `SiteCode`, `StartDate`, `EndDate`, and `SpeciesCode` to customize your data request.
3. **Example API Call:** Retrieve data in JSON format.

    ```python
    import requests

    url = 'https://api.erg.ic.ac.uk/AirQuality/Data/Site/SiteCode=KC1/StartDate=2022-06-01/EndDate=2022-12-01/Json'
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        print(data)
    else:
        print("Error:", response.status_code)
    ```

## Satalite

Get Satellite data from:

    (<https://download.regional.atmosphere.copernicus.eu/services/CAMS50>)
    API INFO:
    <https://www.regional.atmosphere.copernicus.eu/doc/Guide_Numerical_Data_CAMS_new.pdf>

    IMPORTANT:
    Satellite forecast data should become available on API at:
         06:30 UTC for 0-48 hours.
         08:30 UTC for 49-72 hours.

To get a square(ish) grid we note that a degree of longitude is cos(latitude)
times a degree of latitude. For London this means that a degree of latitude is about 1.5 times larger than one of longitude. We therefore use 1.5 times as many

```
latitude points as longitude
    half_grid = 0.05  # size of half the grid in lat/lon
    n_points_lat = 12  # number of discrete latitude points per satellite box
    n_points_lon = 8  # number of discrete longitude points per satellite box
bounding box to fetch data for
    sat_bounding_box = {
        "lat_min": 51.2867601564841,
        "lat_max": 51.6918741102915,
        "lon_min": -0.51037511051915,
        "lon_max": 0.334015522513336,
    }
    species_to_copernicus = {
        "NO2": "nitrogen_dioxide",
        "PM25": "particulate_matter_2.5um",
        "PM10": "particulate_matter_10um",
        "O3": "ozone",

```

### Satellite Grid Builder Documentation

We are using  module provides a method, `build_satellite_grid`, for generating a dataframe of satellite grid points based on a given dataframe of satellite boxes. The grid points are created around each satellite box to facilitate data analysis and mapping.

### Usage Example

1. Define species mapping to Copernicus categories:

    ```python
    species_to_copernicus = {
        "NO2": "nitrogen_dioxide",
        "PM25": "particulate_matter_2.5um",
        "PM10": "particulate_matter_10um",
        "O3": "ozone",
    }
    ```

2. Set the number of expected one-hourly data per grib file:

    ```python
    n_grid_squares_expected = 32  # Adjust as needed
    ```

3. Specify the list of species using the Enum 'Species':

    ```python
    from enum import Enum

    class Species(Enum):
        NO2 = "NO2"
        PM25 = "PM25"
        PM10 = "PM10"
        O3 = "O3"
    ```

4. Instantiate the SatelliteGridBuilder class and use the `build_satellite_grid` method:

    ```python
    # Example instantiation
    satellite_grid_builder = SatelliteGridBuilder(half_grid=0.1, n_points_lat=5, n_points_lon=5)

    # Example usage with a dataframe of satellite boxes (satellite_boxes_df)
    satellite_grid_df = satellite_grid_builder.build_satellite_grid(satellite_boxes_df)
    ```

### Parameters

- `half_grid`: Half of the grid spacing around each satellite box.
- `n_points_lat`: Number of grid points along the latitude for each box.
- `n_points_lon`: Number of grid points along the longitude for each box.

### Returns

- A pandas DataFrame containing latitude, longitude, and box_id columns for each grid point.

**Note:** Adjust the grid parameters according to the desired granularity and coverage.

## Breath London

### Types of Data Collected

1. **Pollutant Measurements:**
   - **Nitrogen Dioxide (NO2):** A key indicator of traffic-related air pollution.
   - **Particulate Matter (PM1, PM2.5, and PM10):** Fine particles from various sources, including vehicle emissions, construction sites, and industrial activities.
   - **Ozone (O3):** Formed by chemical reactions between other pollutants in the presence of sunlight.
   - **Carbon Monoxide (CO):** Emitted from vehicles and other combustion sources.
   - **Other Pollutants:** May include volatile organic compounds (VOCs) and black carbon.

2. **Meteorological Data:**
   - **Temperature:** Air temperature readings.
   - **Humidity:** Measurement of moisture in the air.
   - **Wind Speed and Direction:** Important for understanding the dispersion of pollutants.

### Data Collection Methods

- **Fixed Sensors:** High-quality air quality monitoring stations placed at strategic locations across the city.
- **Mobile Sensors:** Sensors mounted on vehicles or carried by individuals to measure air quality in different areas, including areas not covered by fixed stations.
- **Wearable Sensors:** Portable devices worn by individuals to measure personal exposure to air pollution.

### Data Accessibility

- **Real-Time Data:** Breathe London provides real-time air quality data through its website and mobile applications.
- **Historical Data:** Users can access historical air quality data for analysis and research purposes.
- **Data Format:** Data is available in various formats, including JSON, CSV, and through interactive web-based platforms.

### Accessing Breathe London Data

#### Using the Breathe London Website

1. **Visit the Breathe London website:** The primary portal for accessing air quality data.
2. **Data Dashboard:** The website features a dashboard where users can view real-time and historical air quality data from different monitoring sites and mobile sensors.
3. **Data Downloads:** Users can download data for specific time periods and pollutants.

#### Using the Breathe London API

1. **API Endpoint:** Access the Breathe London API to programmatically retrieve air quality data.
2. **Parameters:** Specify parameters such as `location`, `pollutant`, `start_date`, and `end_date` to customize your data request.
3. **Example API Call:** Retrieve data in JSON format.

    ```python
    import requests

    url = 'https://api.breathelondon.org/v1/measurements?location=some_location&start_date=2022-06-01&end_date=2022-12-01'
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        print(data)
    else:
        print("Error:", response.status_code)
    ```

## SCOOT

### Data Collected by SCOOT

1. **Traffic Flow Data:**
   - **Vehicle Counts:** Number of vehicles passing through an intersection.
   - **Traffic Speeds:** Speed of vehicles at different points in the network.
   - **Queue Lengths:** Length of vehicle queues at traffic signals.
   - **Cycle Time:** Duration of traffic signal cycles.

2. **Detector Types:**
   - **Inductive Loop Detectors:** Embedded in the road surface to detect vehicles.
   - **Magnetometers:** Measure changes in the magnetic field caused by passing vehicles.
   - **Other Sensors:** May include video and radar sensors for additional traffic monitoring.

### How SCOOT Works

1. **Data Collection:**
   - **Real-Time Monitoring:** Continuous collection of traffic data from sensors at intersections.
   - **Central Processing:** Data is sent to a central computer for processing.

2. **Signal Optimization:**
   - **Cycle Time Adjustment:** Dynamically adjusts the overall cycle time to balance traffic flow.
   - **Green Time Allocation:** Distributes green time across different traffic movements to minimize delays.
   - **Offset Coordination:** Coordinates signals at adjacent intersections to create a "green wave" for smoother traffic flow.

3. **Adaptation:**
   - **Continuous Updates:** Signal timings are updated every few seconds based on current traffic conditions.
   - **Response to Changes:** Quickly adapts to changes in traffic patterns, such as during peak hours or incidents.

### Accessing SCOOT Data

While direct public access to raw SCOOT data is limited due to the proprietary nature of the system and data privacy concerns, traffic management centers (TMCs) and city authorities can access and utilize this data for urban planning and traffic management.

### Use Cases and Applications

1. **Traffic Management Centers (TMCs):**
   - **Real-Time Monitoring:** TMCs use SCOOT data to monitor and manage traffic in real-time.
   - **Incident Response:** Quickly respond to traffic incidents and adjust signals to mitigate impact.

2. **Urban Planning:**
   - **Infrastructure Improvements:** Use historical SCOOT data to plan infrastructure upgrades and improvements.
   - **Policy Making:** Inform traffic policies and congestion management strategies.

3. **Research and Analysis:**
   - **Traffic Studies:** Conduct detailed traffic flow and congestion studies using SCOOT data.
   - **Model Validation:** Validate traffic models and simulations with real-world data.

### Example Use in Research

Researchers and urban planners can use SCOOT data to study the impact of traffic signal optimization on air quality, traffic congestion, and road safety. For example:

```
<https://s3.console.aws.amazon.com/s3/buckets/surface.data.tfl.gov.u>

- SCOOTLinkID – Refers to the SCOOT Link ID
- LinkDescription – A brief description of the location of the Junction typically by road name
- Date – The date of the data
- TwentyFourHourVehicleFlowTotal – The total flow observed within a 24 hour period across all links approaching the junction
- FlowDataCompletenessPercentage – Refers to the availability of data; 100% is a complete dataset.
- AverageCongestionPercentage – The average congestion within a 24 hour period across all links approaching the junction
- CongestionDataCompletenessPercentage – Refers to the availability of data; 100% is a complete dataset
```
