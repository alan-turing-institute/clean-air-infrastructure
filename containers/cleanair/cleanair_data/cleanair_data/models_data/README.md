## Examples

Example config:
```json
{
    "train_start_date": "2019-11-01T00:00:00",
    "train_end_date": "2019-11-30T00:00:00",
    "pred_start_date": "2019-11-01T00:00:00",
    "pred_end_date": "2019-11-30T00:00:00",
    "train_sources": ["laqn", "aqe"],
    "pred_sources": ["laqn", "aqe"],
    "train_interest_points": ["point_id1", "point_id2"],
    "train_satellite_interest_points": ["point_id1", "point_id2"]
    "pred_interest_points": ["point_id1", "point_id2"],
    "species": ["NO2"],
    "features": "all",
    "norm_by": "laqn",
    "model_type": "svgp",
    "tag": "production",
}
```

```python
>>> data_df = model_data.normalised_training_data_df
>>> sources = ["laqn"]
>>> species = ["NO2", "PM10"]
>>> print(model_data.get_training_data_arrays(data_df, sources, species)
    {
        "X": {
            "laqn": x_laqn
        },
        "Y": {
            "laqn": {
                "NO2": y_laqn_NO2,
                "PM10": y_laqn_pm10
            }
        },
        "index": {
            "laqn": {
                "NO2": laqn_NO2_index,
                "PM10: laqn_pm10_index
            }
        }
    }
```
