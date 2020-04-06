import gpflow
import tensorflow as tf
import numpy as np

## Given the data and the specific sensor this function optimise the ELBO and plot the results 
def train_sensor_model(X, Y, kernel, optimizer, epochs = 100, logging_epoch_freq = 10, M=10, inducing_point_method="random"):
    
    ## To remove newaxis when more features
    num_features = X[:,0][:,np.newaxis].shape[0]
    
    X = tf.convert_to_tensor(X[:,0][:,np.newaxis])
    Y = tf.convert_to_tensor(Y.astype(np.float64))

    # ToDo : number of rows
    if M == X.shape[0]:
        ind_points = X
    elif inducing_point_method == "random":
        # randomly select 
        ind_points = tf.random.shuffle(X)[:M]
    else:
        # select of regular grid
        # ToDo: double check this line
        ind_points = tf.expand_dims(
            tf.linspace(np.min(X[:,0]), np.max(X[:,0]), M),1
        )
    
    lik = gpflow.likelihoods.Poisson()
    
    ## Add code for inducing inputs - Needed when we run on the full data
    model = gpflow.models.SVGP(kernel=kernel, likelihood=lik, inducing_variable=ind_points)
    
    ## Uncomment to see which variables are training and those that are not
    #print_summary(model)
    
    simple_training_loop(X, Y, model, optimizer, epochs = epochs, 
                         logging_epoch_freq = logging_epoch_freq)

    return model
    
def simple_training_loop(X, Y, model: gpflow.models.SVGP, optimizer, epochs: int = 1, logging_epoch_freq: int = 10, num_batches_per_epoch: int = 10):

    ## Optimization functions - train the model for the given epochs
    def optimization_step(model: gpflow.models.SVGP, X, Y):
        with tf.GradientTape(watch_accessed_variables=False) as tape:
            tape.watch(model.trainable_variables)
            obj = -model.elbo(X, Y)
            grads = tape.gradient(obj, model.trainable_variables)
        optimizer.apply_gradients(zip(grads, model.trainable_variables))

    tf_optimization_step = tf.function(optimization_step)
    for epoch in range(epochs):
        for _ in range(num_batches_per_epoch):
            tf_optimization_step(model, X, Y)

        epoch_id = epoch + 1
        if epoch_id % logging_epoch_freq == 0:
            tf.print(f"Epoch {epoch_id}: ELBO (train) {model.elbo(X,Y)}")
