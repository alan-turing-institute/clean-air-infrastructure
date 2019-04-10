import psycopg2
import urllib.request
import requests
from time import sleep
from subprocess import call
from psql_runner import run_file
import os
import pandas as pd
import numpy as np
import re

ROOT = os.getcwd()
print(ROOT)

config = {
    'USE_SITE_INFO_CACHE': True,
    'roots': {
        'root': ROOT,
        'sites': ROOT+'/sites_info',
        'sql': ROOT+'/sql',
        'data': ROOT+'/data'
    },
    'files': {
        'site_info_schema': 'sites_info_schema.sql'
    }
        
}

conn = psycopg2.connect("dbname='%s'" % 'postgis_test')


def download_and_save_url(url, file_name):
    print('Downloading %s' % url)
    urllib.request.urlretrieve(url, file_name)

def rdata_to_csv(file_rdata, file_csv_output, rdata_df):
    call(['Rscript','--vanilla','rdata_to_csv.r',file_rdata,file_csv_output,rdata_df])



def get_site_codes_in_year_range(start_year, end_year):
    start_date = '01/01/{year}'.format(year=start_year)
    end_date = '01/01/{year}'.format(year=end_year)

    sql = 'select SiteCode from orca.aqe_sites where (DateOpened <= {end!r});'.format(end=str(end_date))
    cur = conn.cursor()
    cur.execute(sql)

    site_codes = cur.fetchall()

    conn.commit()
    conn.close()
    return site_codes

def get_url(sitecode, year):
    """
        URLs are of the format
        http://acer.aeat.com/gla-cleaner-air/api/v1/gla-cleaner-air/v1/site/HS4/2018-06-01/2018-06-05
    """

    start_year = '{year}-01-01'.format(year=year)
    end_year = '{year}-12-31'.format(year=year)
    url = 'http://acer.aeat.com/gla-cleaner-air/api/v1/gla-cleaner-air/v1/site/{sitecode}/{start_year}/{end_year}'.format(sitecode=sitecode, start_year=start_year, end_year=end_year)
    return url


def download(site_codes, years):

    count = 0
    for year in years:
        for site in site_codes:
            site = site[0]
            filename = "{site}_{year}.csv".format(site=site,year=year)
            url = get_url(site, year)
            dir_to_save = config['roots']['data'] + '/' + filename
            resp = requests.head(url)
            if resp.status_code is 200:
                #file exists
                count = count + 1
                print('Downloading %s'%site)
                while True:
                    try:
                        urllib.request.urlretrieve(url, dir_to_save)
                        break
                    except Exception as e:
                        print('Exception on site %s'%site)
                        print(e)
                        sleep(10)
                        print('trying again')
                        continue
                    except:
                        print('problem on site %s'%site)
                        sleep(10)
                        print('trying again')


                print('Downloaded %s'%site)
    print(count)

def process(site_codes, years):
    count = 0
    all_cols = ['site','date', 'no2', 'pm10', 'pm25']
    total_df = pd.DataFrame(columns=all_cols)
    for year in years:
        for site in site_codes:
            site = site[0]
            filename = "{site}_{year}.csv".format(site=site,year=year)
            f_path = config['roots']['data'] + '/' + filename
            if not os.path.isfile(f_path):
                continue

            print(filename)

            df = pd.read_csv(f_path)
            df['site'] = site

            for col_i in all_cols:
                match = False
                for col in df.columns:
                    if re.match('^.*{col}.*$'.format(col=col_i), col, re.IGNORECASE):
                        df[col_i] = df[col]
                        match = True
                if match is False:
                    df[col_i] = None

            total_df = total_df.append(df[all_cols])
    
    total_df.to_csv(ROOT+'/data.csv', index=False)




start_year = '2015'
end_year = '2018'
years = ['2016', '2018']
site_codes = get_site_codes_in_year_range(start_year, end_year)
#download(site_codes, years)
process(site_codes, years)







