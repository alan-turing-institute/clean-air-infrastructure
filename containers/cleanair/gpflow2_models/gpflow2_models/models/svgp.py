import gpflow
import pickle
import json
import time
import tensorflow as tf
import pandas as pd
import numpy as np
from scipy.cluster.vq import kmeans2


# Replace the path with the actual path to your pickle file
file_path_X = "./breathe_training_data.pkl"
file_path_Y = "./breathe_training_NO2.pkl"

X = pd.DataFrame(
    pd.read_pickle(
        "/Users/suedaciftci/projects/clean-air/clean-air-infrastructure/breathe_training_data.pkl"
    )
)
Y = pd.DataFrame(
    pd.read_pickle(
        "/Users/suedaciftci/projects/clean-air/clean-air-infrastructure/breathe_training_NO2.pkl"
    )
)
input_dim = X.shape[1]
output_dim = Y.shape[1]
kernel = gpflow.kernels.Matern32(input_dim, lengthscales=1.0)
M = 100
N = 1069
batch_size = 100

# Convert X and inducing_variable to numeric arrays
inducing_variable = X[:M]

likelihood = gpflow.likelihoods.Gaussian(variance=1.0)

# Now you can use kmeans2 safely after converting X and inducing_variable to numeric arrays
z_r = kmeans2(X, inducing_variable, minit="points")[0]
dataset = tf.data.Dataset.from_tensor_slices((X, Y))
dataset = dataset.shuffle(buffer_size=X.shape[0]).batch(batch_size)

# Create the mean function using lists instead of numpy arrays
A = [[1.0] for _ in range(input_dim)]
b = [1.0]
mean_function = gpflow.mean_functions.Linear(A=A, b=b)

model = gpflow.models.SVGP(
    kernel=kernel,
    likelihood=likelihood,
    inducing_variable=z_r,
    num_data=N,
    mean_function=mean_function,
)
start_time = time.time()
optimizer = tf.optimizers.Adam()

# Training loop
num_epochs = 10
Elbo = []
for epoch in range(num_epochs):
    for batch in dataset:
        X_batch, Y_batch = batch

        with tf.GradientTape() as tape:
            # Compute the loss for the mini-batch
            loss = -model.elbo((X_batch, Y_batch))
        # Compute the gradients
        gradients = tape.gradient(loss, model.trainable_variables)

        # Update the model parameters
        optimizer.apply_gradients(zip(gradients, model.trainable_variables))
    # Make predictions on the data points
    predictions = model.predict_f(X_batch)[0]  # Get the mean predictions

    # Print the predictions and data points
    # for i in range(len(predictions)):
    #     print(f"Data Point {i}: Prediction = {predictions[i]}, Actual = {Y_batch[i]}")

    if epoch % 1 == 0:
        Elbo.append(
            loss.numpy().item()
        )  # Convert tensor to Python float and append to Elbo
        print(f"Epoch {epoch}: ELBO = {loss:.2f}")


# After training, you can make predictions with the trained model
filename = (
    f"elbo_{num_epochs}_epochs_bl.json"  # Construct the file name with num_epochs
)
with open(filename, "w", encoding="utf-8") as elbo_file:
    json.dump(Elbo, elbo_file)
end_time = time.time()
elapsed_time = end_time - start_time
print("Training time: {:.2f} seconds".format(elapsed_time))
