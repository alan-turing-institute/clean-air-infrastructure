# Visualisation for the London Air Quality Project

The visualisation component of this project is a collaboration between the London air quality project at Turing (Theo, Ollie, Patrick, Oscar, James R, James W), the [visual diagnostics for MCMC project at Turing](https://www.turing.ac.uk/research/research-projects/visual-diagnostics-markov-chain-monte-carlo-mcmc) (Greg and James T) and the GLA (Paul, Libby, Mike).


***

## Minimum requirements (Phase 1)

Our aim is for phase 1 to be complete by January.

1. **Map**: show a map of Greater London (all boroughs) with air quality predictions overlayed.
    - **Style**: the style of the grid will depend on the visualisation we decide upon (see below).
    - **Resolution**: the resolution of the grid will depend on the model.
    - **Boundary**: let the user specify spatial/temporal boundaries before loading the map. This will reduce the size of the data transferred. For spatial queries, 
1. **Temporal**: display air quality predictions over 48 hours.
    - This could be done using a slider?
1. **Multi-variate**: visualise predictions for 3 different types of pollutants (NO2, PM10, PM2.5).
    - We will show each pollutant seperately on the map - not together.
1. **Variance**: show the variance of the predictions for a single pollutant at a time.

***

## Future extensions (Phase 2)

1. **Time series**: Show the training and prediction time series of a given point.
    - **Grid square**: by clicking a grid square, the time series will plot mean and variance of recent predictions and the next 48 hours of predictions for that grid square.
    - **Sensor**: by clicking on a sensor, the time series will plot the mean and variance of recent predictions (e.g. for the last week) against the sensor data.
1. **Zooming**: show two different grid resolutions to allow greater spatial detail.
    - We show the whole of London in 100m grid resolution. We show detail in 20m resolution.


***


## Use cases

### General public

#### Walkers, runners & cyclists

A cyclist is planning their route to work this morning and wants to minimise air pollution exposure.
Lets say the fastest route is 10km.
Upon first looking at the web app, the cyclist will want to see at a high level where the bad areas of air quality are.
This will narrow down the available routes.
Once the cyclist has a general trajectory in mind, they will want to zoom in on the map to see in detail which roads are worse than others.
If we clearly explain to the cyclist what the variance of a predictions means, they may also choose a route that is certain to have low air pollution exposure.

### GLA & public bodies

### Researchers & academics

#### ML researchers

Looking at the uncertainty in more details.
Plug and play different models and seeing how they compare.

#### Air quality researchers

## Output of the API

### Datafile type

### Data size & compression

### Spatial & temporal bounds

***

## Style: visualisation ideas

As it stands, there are three ideas for how to visualise a single pollutant over a map of London.
Rather than trying to show multiple pollutants on the same map, it will be much simpler to have a toggle or tick box on the side of the application to show different pollutants.

### Hex grid

There are multiple resolutions for the hex grid.
One of the advantages of the hex grid is that it fits nicely with existing GLA standards.
One dis-advantage is the hex grid is not so familiar with people external to the GLA (e.g. the general public, external developers), although whether this is an issue is up for debate.
Further it is not immediately clear how to visualise uncertainty using the hex grid.

![Hex grid](img/hex.png)

Above is a screenshot from a python visualisation.
The top left shows the pollution on the hex grid and the sensors.
Yellow means high air pollution and blue means low pollution.
Clicking on a sensor shows the time series for that sensor.

The top right shows the variance of the prediction.
This highlights the weakness dicussed above about visualising both variance and air quality using the hex grid: it seems we must show them side by side.
Equally this weakness could also be a strength: it clearly shows the variance which is useful for e.g. machine learning researchers who want to see the weaknesses of the model.


### Rotating lines

![Rotating lines](img/ATI_DarkViridis.png)

### Circles

![Circles](img/ATI_LightRed.png)

***


## Previous systems

### London air (King's college)

### GLA hex system

The GLA have a [hex grid](https://maps.london.gov.uk/green-infrastructure/) map of London.
Each hex has a variable (e.g. poverty, loneliness, etc.) associated with it.

### Breathe London

[Breathe London](https://www.breathelondon.org) displays a dot for each sensor.
By clicking on a dot, you can see the time series for a single pollutant over the last 24 hours.
You can click another buttom called `More data` which displays a time series of the last year of air quality data for a given pollutant at that sensor.

**The ability to request more detail** is a feature we should use.


***

## Possible mis-conceptions or mis-understandings

### Variance

If we are highlighting predictions from the model that we are more certain of (i.e. less variance), does that mean we are hiding the weaknesses of our model?

### Continuous

By displaying a grid, we are implying our model predicts over discrete space, even though we can predict over continuous space.


## Extentions / future work

What about inversing the size of the circles representing variances, i.e. highlighting the areas of the model where we are not so certain about the predictions?


***

## Questions

**What is the realistic upper bound we can expect on air pollution? (e.g. 100 \mu g m^{-3})**

> Nitrogen dioxide in London is bounded by ...