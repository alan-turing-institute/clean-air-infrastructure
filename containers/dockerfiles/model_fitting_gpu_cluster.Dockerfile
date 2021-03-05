# Use pre-built model_fitting_gpu so that all packages are already installed
FROM cleanairdocker.azurecr.io/model_fitting_gpu:ollie

#overwrite cleanair models with new experiments
COPY cleanair /app/cleanair

# Install cleanair
RUN pip install '/app/cleanair[models]'

