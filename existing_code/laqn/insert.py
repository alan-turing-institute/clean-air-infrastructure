import psycopg2
import urllib.request
import requests
from time import sleep
from subprocess import call
from psql_runner import run_file
import os
import pandas as pd

def rdata_to_csv(file_rdata, file_csv_output, rdata_df):
    call(['Rscript','--vanilla','rdata_to_csv.r',file_rdata,file_csv_output,rdata_df])

root = '/Users/ohamelijnck/Documents/london_air/covariates/LondonairDownloader'
data_root = root+'/data'
data_target = root+'/csv_files'

YEAR = '2019'

def rdata_to_csv_dir():
    for filename in os.listdir(data_root):
        if filename.endswith(".Rdata"): 
            site = filename.split('.')[0]
            if site.split('_')[1] != YEAR: continue

            filename = data_root + '/' + '{site}.Rdata'.format(site=site)
            filename_csv = data_target + '/' + '{site}.csv'.format(site=site)

            rdata_to_csv(filename, filename_csv, 'x')

def only_get_pollutants_col(pollutants):
    total_df = pd.DataFrame(columns=['site', 'date']+pollutants)
    for filename in os.listdir(data_target):
        if filename.split('.')[0].split('_')[1] != YEAR: continue
        print(filename)

        if filename.endswith(".csv"): 
            df = pd.read_csv(data_target+'/'+filename, sep=';')
            result_df = df[['site', 'date']]
            for p in pollutants:
                if p in list(df.columns):
                    result_df[p] = df[p]
                else:
                    result_df[p] = None
            total_df = total_df.append(result_df)
    
    total_df.to_csv(root+'/tmp/data.csv', index=False)

def insert():
    schema = root+'/sql/laqn_hourly_data.schema.sql'
    run_file(schema, [['<data_file>', '\''+root+'/tmp/data.csv'+'\'']]) #replace <site_info_csv> with the csv file name


rdata_to_csv_dir()

only_get_pollutants_col(["nox","no2","o3","co","pm10_raw","pm10","pm25"])
insert()

