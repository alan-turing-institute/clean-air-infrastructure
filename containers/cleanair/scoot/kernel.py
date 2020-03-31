import gpflow

## Choose kernel based on settings provided
def choose_kernel(settings: dict):
    all_kernels = ["rbf","periodic","matern52","matern32","matern12"]
    
    def map_string_to_kernel(s: str,params: dict):
        if s == 'rbf':
            return gpflow.kernels.RBF(**params)
        elif s == 'periodic':
            return gpflow.kernels.Periodic(**params)
        elif s == 'matern12':
            return gpflow.kernels.Matern12(**params)
        elif s == 'matern32':
            return gpflow.kernels.Matern32(**params)
        elif s == 'matern52':
            return gpflow.kernels.Matern52(**params)
            
    # Pass kernel strings
    kernel_1 = settings["kernel_1"]["name"]
    kernel_1_hyperparameters = settings["kernel_1"]["hyperparameters"]
    kernel_2 = settings["kernel_2"]["name"]
    kernel_2_hyperparameters = settings["kernel_2"]["hyperparameters"]
        
    # Store kernel object here
    kernel = None
    
    # If neither kernels are correctly specified
    if kernel_1 not in all_kernels and kernel_2 not in all_kernels:
        raise ValueError("Neither kernels {} and {} are correclty specified.".format(kernel_1,kernel_2))
    # If either of the two kernels is correctly specified
    if kernel_1 not in all_kernels or kernel_2 not in all_kernels:
        if kernel_1 not in all_kernels:
            print('Using {} kernel'.format(kernel_2))
            print('Hyperparameters')
            print(kernel_2_hyperparameters)
            kernel = map_string_to_kernel(kernel_2,kernel_2_hyperparameters)
        else:
            print('Using {} kernel'.format(kernel_1))
            print('Hyperparameters')
            print(kernel_1_hyperparameters)
            kernel = map_string_to_kernel(kernel_1,kernel_1_hyperparameters)
    elif kernel_1 in all_kernels and kernel_2 in all_kernels:
        print('Using product of {} and {} kernels'.format(kernel_1,kernel_2))
        print('Hyperparameters of {}'.format(kernel_1))
        print(kernel_1_hyperparameters)
        print('Hyperparameters of {}'.format(kernel_2))
        print(kernel_2_hyperparameters)
        kernel_1 = map_string_to_kernel(kernel_1,kernel_1_hyperparameters)
        kernel_2 = map_string_to_kernel(kernel_2,kernel_2_hyperparameters)
        kernel = kernel_1 * kernel_2
    return kernel