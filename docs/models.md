# SVGP

## `setup_model`

Parameters:

    x_array: (N x D numpy array) observations input.
    y_array: (N x 1 numpy array) observations output.
    inducing_locations: (M x D numpy array) inducing locations.

Returns:

    None

Method Description:

The method starts by setting the jitter value for numerical stability in cholesky operations. Then it creates an instance of the kernel specified in the model_params attribute of the class, with the kernel type and other kernel parameters passed as arguments.

It then creates an instance of GPflow's SVGP model, passing in the x_array, y_array, the kernel instance, a Gaussian likelihood with a specified variance, the inducing locations, a specified minibatch size, and a linear mean function. The created model is stored in the model attribute of the class.

This method is called when the object of the SVGP class is created, it creates the GPflow's sparse variational Gaussian Processes model and sets it to the model attribute of the class.

## `fit`

The SVGP class is a Sparse Variational Gaussian Process model for air quality modeling. The class has the following methods and attributes:

    KERNELS: A dictionary that maps a set of string keys to GPflow kernel classes. The keys in the dictionary correspond to the type of kernel that the model will use, such as Matern12, Matern32, Matern52, and RBF.

    setup_model(x_array: FeaturesDict, y_array: TargetDict, inducing_locations: npt.NDArray[np.float64]) -> None: This method creates an instance of GPflow's SVGP model. It takes in 3 arguments: x_array, y_array, and inducing_locations. x_array and y_array are the input and output observations for the model, respectively, while inducing_locations are the locations used in the sparse variational process. The method creates an instance of the kernel specified in the model_params attribute of the class and then creates an instance of GPflow's SVGP model, passing in the x_array, y_array, the kernel instance, a Gaussian likelihood with a specified variance, the inducing locations, a specified minibatch size, and a linear mean function. The created model is stored in the model attribute of the class.

    fit(x_train: FeaturesDict, y_train: TargetDict) -> None: This method is used to train the parsing variational Gaussian process model. It takes in two arguments, x_train and y_train, which are the input and output observations used for training. The input observations are expected to come from a single source, 'laqn', and the output observations are expected to be for a single species, 'NO2'. The method starts by validating the input training set using the check_training_set_is_valid method. Then it copies the relevant parts of the input and output observations, x_train[Source.laqn] and y_train[Source.laqn][Species.NO2], into x_array and y_array variables, respectively.
    It then uses the clean_data method to clean and preprocess the data. The method then uses the k-means algorithm to select the inducing points, z_r, by running kmeans2 on x_array with the number of inducing points specified in the model_params attribute of the class.
    It then calls the setup_model method to create an instance of the SVGP model and compiles it. Finally, it uses the Adam optimizer to minimize the model's negative log-likelihood, with the elbo_logger method as a step callback and the number of maximum iterations specified in model_params.

    elbo_logger: A method that logs the evidence lower bound (ELBO) value during optimization.

    clean_data(x_array, y_array): method that clean the input data

    check_training_set_is_valid(x_train, y_train): method that check if the input data is valid

    model_params: an object that holds the parameters of the model such as the kernel type, the likelihood variance, the number of inducing points, the minibatch size, the jitter.

## `predict`

The method takes in a parameter x_test, which is expected to be a FeaturesDict object.

The method starts by defining a lambda function *predict_fn* that takes in a single parameter x and returns the result of calling *self.model.predict_y(x*). It then calls another method *self.predict_srcs(x_test, predict_fn)* and assigns the returned value to the variable y_dict.

Finally, the method returns the *y_dic*t variable. This method is used for making predictions using the stored model and the input features. It's important to note that *self.predict_srcs* and *self.model.predict_y* methods are assumed to be defined elsewhere in the class or a parent class.

## `params`

This is a method named *params* for a class. It returns an object of SVGPParams type.

The method starts by creating a variable *params* and copying the value of the *self.model_params* attribute into it. Then it updates the variance attribute of the kernel attribute of the *params* variable with the value of the variance attribute of the kern attribute of the *self.model* attribute. Similarly, it updates the lengthscales attribute of the *kernel* attribute of the params variable with the value of the lengthscales attribute of the kern attribute of the *self.model* attribute.

Finally, the method returns the *params* variable. This method is returning the parameters of the model with updated variance and lengthscales. This can be useful for getting the current configuration of the model and using it for further analysis or comparison.
