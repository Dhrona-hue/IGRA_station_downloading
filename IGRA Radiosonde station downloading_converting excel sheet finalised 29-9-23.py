"""
Created on Fri Sep 29 13:02:16 2023

@author: Dhrona
"""
####This is a python code to download the IGRA Radiosonde station datas accross the globe and export it into the required excel format

# Import necessary libraries
import igra
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
from scipy import interpolate
from datetime import datetime
from siphon.simplewebservice.igra2 import IGRAUpperAir

# Download the station list from the IGRA dataset and store it in '/tmp' directory
stns = igra.download.stationlist('/tmp')

# Filter stations to select those with data available between 1980 and 2022 and within a latitude range of -30 to 30 degrees
stns_ftr = stns.loc[(stns['start'] <= 1980) & (stns['end'] >= 2022)]
stns_ftr1 = stns_ftr.loc[(stns_ftr['lat'] >= -30) & (stns_ftr['lat'] <= 30)]

# Remove unnecessary columns from the station information
stns_ftr2 = stns_ftr1.drop(['wmo', 'alt', 'state', 'lon', 'start', 'end', 'total'], axis=1)

# Create a header row with column names and reset the index
stns_ftr2.loc[0] = stns_ftr2.columns.to_list()
stns_ftr2 = stns_ftr2.reset_index(drop=False)

# Transpose the station information for easier access by columns
stns_ftr3 = np.transpose(stns_ftr2)

# Define the date range for which data is needed
date = [datetime(1980, 1, 1, 0), datetime(2022, 12, 31, 12)]

# Loop through a range of station numbers (1 to 314)
for m in range(1,315):
    # Get station ID, name, and latitude for the current station
    station = stns_ftr3.loc['id', m]
    stn_name = stns_ftr3.loc['name', m]
    stn_lat = stns_ftr3.loc['lat', m]
    
    # Request upper air data for the specified date range and station
    df, header = IGRAUpperAir.request_data(date, station, derived=True)
    
    # Create a DataFrame from the obtained data
    mat = pd.DataFrame(df)
    
    # Remove unnecessary columns from the DataFrame
    mat1 = df.drop(['pressure', 'reported_height', 'temperature_gradient', 'potential_temperature',
                    'potential_temperature_gradient', 'virtual_temperature', 'virtual_potential_temperature',
                    'vapor_pressure', 'saturation_vapor_pressure', 'reported_relative_humidity',
                    'calculated_relative_humidity', 'relative_humidity_gradient', 'u_wind', 'u_wind_gradient',
                    'v_wind', 'v_wind_gradient', 'refractive_index'], axis=1)
    
    # Convert the 'date' column to datetime format
    mat1['date'] = pd.to_datetime(mat1['date'], format='%d.%m.%Y %H:%M')
    
    # Extract year, month, day, and hour from the 'date' column
    mat1['year'] = mat1['date'].apply(lambda x: x.year)
    mat1['month'] = mat1['date'].apply(lambda x: x.month)
    mat1['day'] = mat1['date'].dt.day
    mat1['hour'] = mat1['date'].dt.hour
    
    # Remove the 'date' column from the DataFrame
    mat2 = mat1.drop(['date'], axis=1)
    
    # Initialize empty lists for data processing
    Z = []  # To store year and month pairs
    A = []  # To store interpolated temperature data
    
    # Loop through years from 1980 to 2022
    for l in range(1980, 2023):
        A1 = []  # To store monthly temperature data
        # Loop through months (1 to 12)
        for k in range(1, 13):
            A2 = []  # To store daily temperature data
            # Loop through days (1 to 31)
            for i in range(1, 32):
                # Loop through hours (0 to 23)
                for j in range(24):
                    # Select data for the current year, month, day, and hour
                    mat4 = mat2.loc[(mat2['year'] == l) & (mat2['month'] == k) & (mat2['day'] == i) & (mat2['hour'] == j)]
                    if len(mat4) >= 1:
                        B = mat4
                        ind = np.arange(0, 40.1, 0.1)
                        X = np.array(B['calculated_height'] / 1000)
                        Y = np.array(B['temperature'])
                        
                        # Interpolate temperature data using linear interpolation
                        ind1 = interpolate.interp1d(X, Y, bounds_error=False, fill_value='nan')
                        Matrix = ind1(ind)
                    else:
                        # If no data is available, fill with NaN values
                        Matrix = np.empty((401,))
                        Matrix[:] = np.NaN
                        
                    A2.append(Matrix)
                    
                # Calculate the average temperature for each hour of the day
                A9 = np.transpose(np.array(A2))
                Av = np.nanmean(A9, axis=1)
            
            # Append year and month to Z list for tracking
            Z.append([l, k])
            Z1 = np.transpose(np.array(Z))
            
            # Append the average temperature data for the month to A list
            A.append(Av)
            bb = np.transpose(np.array(A))
            
            # Clean up A2 list
            del A2
    
    # Combine year, month, and temperature data
    Needed = np.concatenate((Z1, bb), axis=0)
    
    # Create a DataFrame from the combined data
    Matrixx = pd.DataFrame(Needed)
    
    # Save the data to an Excel file with a name based on station information
    Matrixx.to_excel(station + '_' + stn_name.replace("/", " ") + '_' + str(stn_lat) + '.xlsx')
