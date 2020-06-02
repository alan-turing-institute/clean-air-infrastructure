import gpflow

KERNELS = [
    dict(
        name="matern32",
        hyperparameters=dict(
            lengthscale=0.1,
            variance=0.1,
        )
    ),
    dict(
        name="rbf",
        hyperparameters=dict(
            lengthscale=0.1,
            variance=0.1,
        )
    ),
    dict(
        name="periodic",
        hyperparameters=dict(
            period=0.5,
            lengthscale=0.7,
            variance=4.5,
        )
    )
]

def parse_kernel_token(next_token, kernel_map):
    """
    Takes a list or dict description of a kernel and returns a gpflow kernel.
    """
    kernel = None

    # multiply kernels together
    if isinstance(next_token, list):
        # take produce of kernels in list
        for item in next_token:
            if not kernel:
                kernel = parse_kernel_token(item, kernel_map)
            else:
                kernel = kernel * parse_kernel_token(item, kernel_map)
        return kernel
    # add kernels together
    if isinstance(next_token, dict) and "+" in next_token and isinstance(next_token["+"], list):
        for item in next_token["+"]:
            if not kernel:
                kernel = parse_kernel_token(item, kernel_map)
            else:
                kernel = kernel + parse_kernel_token(item, kernel_map)
        return kernel
    # get kernel with hyperparameters
    if isinstance(next_token, dict):
        params = next_token["hyperparameters"].copy()
        return kernel_map[
            next_token["name"]
        ](**params)
    # no matches for tokens
    raise TypeError("Token was not a list or dict.")

def parse_kernel(token):
    """
    Takes a list or dict and returns a kernel by parsing the datastructure.
    """
    mod = gpflow.kernels
    kernel_map = dict(
        [(name.lower(), cls) for name, cls in mod.__dict__.items() if isinstance(cls, type)]
    )
    return parse_kernel_token(token, kernel_map)
