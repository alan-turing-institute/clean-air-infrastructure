```
docker build -t cleanair_gpf2:test -f containers/cleanair/gpflow2_models/dockerfiles/gpf2_model_fit.Dockerfile containers
```

```
docker run cleanair_gpf2:test az login && urbanair_gpf2 dataset data download --directory ./ && urbanair_gpf2 model fit train /app/gpflow2_models/aq_data.pkl
```

```
docker run cleanair_gpf2:test az login && urbanair_gpf2 dataset data download --directory /app/gpflow2_models
```
