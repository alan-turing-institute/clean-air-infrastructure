# Processing Traffic Datasets

The urbanair project used a traffic dataset called SCOOT.
This guide shows you how to run the SCOOT forecasting model and then create traffic features which can be used by the air quality model.
Before starting this guide, make sure you have:

1. [Installed the cleanair package](installation.md#install-cleanair)
2. [Connect to the database](database_connection.md)

> Note that the SCOOT forecasting model and feature extraction are automatically scheduled to run daily. This guide is purely for testing & development purposes.

## Contents

- [How it works](#how-it-works)
- [How to check the SCOOT features](#how-to-check-the-features)
- [How to extract the SCOOT features](#how-to-extract-the-features)

***

## How it works

We extract scoot features in multiple steps using the urbanair cli:

1. Map scoot sensors to the road network and calculate weighting to use for mapping scoot readings to roads. (This need only be done once)
2. Check what features have already been processed between the times of interest. Return a list of point_ids that haven't been processed.
3. Create buffers around these interest points and inner join with OSHighway where geoms intersect (not joined with scoot data yet - so much smaller join). We now have a lookup table telling us every road segment which is in each buffer. For two interest points this might look like this:
![Example buffers around scoot detectors](figures/scoot_buffer.png)
4. Join the scoot readings to table above and then calculate road readings using  precalculated weightings and store as a [CTE](https://www.postgresql.org/docs/9.1/queries-with.html). This gives us a reading for every road segment in a buffer.
5. For every feature we want to extract aggregate the appropriate column from the CTE created in step 4. Then `UNION` all of these together so can process all features in the same query. Otherwise we'd have to repeat all the above steps for every feature.

### Benefits of this approach

- We map scoot sensors to road readings when we need them. If you just need scoot features at LAQN or AQE sensors you don't want to have to map scoot readings to the entire road network before you can start feature processing
- Don't need to store road readings in the database, which will get very large fast.
- Avoid doing a massive inner join of OSHighway X timestamps with buffers based on a spatial intersection. Instead just join OSHighway with buffers based on spatial intersection and then join scoot readings based on point_id.

Calculating features for more days is not particularly expensive. Adding more interest points is more expensive.

***

## How to check the features

SCOOT features are stored in the PostgreSQL database under the `dynamic_features` schema.
You can check the extracted features for a given data range and for a list of interest point "sources" (e.g. `laqn`, `aqe`, `satellite`):

```bash
urbanair_db features scoot check  --ndays 1 --upto 2022-01-05  --source laqn  --source aqe
```

To see if there are any *missing* features, append the `--only-missing` flag to the above command.

***

## How to extract the features

If you find there are missing features from the above section, you can run the SCOOT forecasting and feature extraction algorithm as follows.

First, check that the mapping from roads to SCOOT sensors is up to date:

```bash
urbanair_db features scoot update-road-maps
```

Now process all the SCOOT features for any interest points that have any missing data for the given date range:

```bash
urbanair_db features scoot fill  --ndays 1 --upto 2020-01-05  --source laqn  --source aqe --insert-method missing 
```
