import plotly.graph_objects as go
import numpy as np
import pandas as pd
import tensorflow as tf
from ..model import sample_intensity, sample_n

def plotly_results(
        sensor_df: pd.DataFrame,
        detector_id: str,
        model,
        test_inputs,
        num_sigmas: int = 2,
        num_samples: int = 100
    ):
    """
    This functions plot the results together with the true counts
    """
    
    # If test inputs is not a tensorflow object, convert it to one
    if isinstance(test_inputs, np.ndarray):
       test_inputs = tf.convert_to_tensor(test_inputs[:,0][:,np.newaxis])
    
    # Compute posterior mean and variance of count distribution
    count_mean_N, count_var_N = sample_n(model, test_inputs, num_samples)
    # Compute posterior mean and variance of intensity distribution
    intensity_mean_N,intensity_var_N = sample_intensity(model,test_inputs,num_samples)
    
    # Plot
    fig = go.Figure()
    
    count_upper_2sigma = go.Scatter(
                        name=r'$Counts \mu+2\sigma$',
                        x=sensor_df['measurement_start_utc'], 
                        y=count_mean_N[:,0] + num_sigmas*np.sqrt(count_var_N)[:,0],
                        mode='lines',
                        marker=dict(color="#444"),
                        line=dict(width=0),
                        fillcolor='rgba(255,0,0,0.3)',
                        fill='tonexty',
                        showlegend = False
                    )

    count_mean_predictions = go.Scatter(
                            x=sensor_df['measurement_start_utc'], 
                            y=count_mean_N[:,0],
                            mode='lines',
                            name='Count predictions',
                            fill='tonexty',
                            fillcolor='rgba(255,0,0,0.3)',
                            line=dict(color='rgb(255, 0, 0)')
                        )

    count_lower_2sigma = go.Scatter(
                        name=r'$Counts \mu-2\sigma$',
                        x=sensor_df['measurement_start_utc'], 
                        y=count_mean_N[:,0] - num_sigmas*np.sqrt(count_var_N)[:,0],
                        marker=dict(color="#444"),
                        mode='lines',
                        line=dict(width=0),
                        showlegend = False
                    )
    
    intensity_upper_2sigma = go.Scatter(
                        name=r'Intensity $\mu+2\sigma$',
                        x=sensor_df['measurement_start_utc'], 
                        y=intensity_mean_N[:,0] + num_sigmas*np.sqrt(intensity_var_N)[:,0],
                        mode='lines',
                        marker=dict(color="#444"),
                        line=dict(width=0),
                        fillcolor='rgba(0,255,0,0.3)',
                        fill='tonexty',
                        showlegend = False
                    )

    intensity_mean_predictions = go.Scatter(
                            x=sensor_df['measurement_start_utc'], 
                            y=intensity_mean_N[:,0],
                            mode='lines',
                            name='Intensity predictions',
                            fill='tonexty',
                            fillcolor='rgba(0,255,0,0.3)',
                            line=dict(color='rgb(0, 255, 0)')
                        )

    intensity_lower_2sigma = go.Scatter(
                        name=r'$Intensity \mu-2\sigma$',
                        x=sensor_df['measurement_start_utc'], 
                        y=intensity_mean_N[:,0] - num_sigmas*np.sqrt(intensity_var_N)[:,0],
                        marker=dict(color="#444"),
                        mode='lines',
                        line=dict(width=0),
                        showlegend = False
                    )
    
    actual = go.Scatter(
                x=sensor_df['measurement_start_utc'], 
                y=sensor_df['n_vehicles_in_interval'],
                mode='lines+markers',
                name='Actual counts',
                line=dict(color='#1f77b4')
    )
    
    data = [count_lower_2sigma, count_mean_predictions, count_upper_2sigma,
            intensity_lower_2sigma, intensity_mean_predictions, intensity_upper_2sigma,
            actual]
    
    layout = go.Layout(
                        title='Timeseries of sensor {id}'.format(id=detector_id),
                        xaxis_title="Datetime",
                        yaxis_title="# of vechicles per hour",
                        font=dict(size=16)
            )

    return data
    
    # fig = go.Figure(data=data, layout=layout)
    
    # fig.show()
