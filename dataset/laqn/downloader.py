import psycopg2
import urllib.request
import requests
from time import sleep
from subprocess import call
from psql_runner import run_file

ROOT = '/Users/ohamelijnck/Documents/london_air/covariates/LondonairDownloader'
config = {
    'USE_SITE_INFO_CACHE': True,
    'urls': {
        'site_info': 'http://www.londonair.org.uk/r_data/sites.RData'
    },
    'roots': {
        'root': ROOT,
        'sites': ROOT+'/sites_info',
        'sql': ROOT+'/sql',
        'data': ROOT+'/data'
    },
    'files': {
        'site_info_rdata': 'site_info.Rdata',
        'site_info_csv': 'site_info.csv',
        'site_info_schema': 'sites_info_schema.sql'
    }
        
}

conn = psycopg2.connect("dbname='%s'" % 'postgis_test')


def download_and_save_url(url, file_name):
    print('Downloading %s' % url)
    urllib.request.urlretrieve(url, file_name)

def rdata_to_csv(file_rdata, file_csv_output, rdata_df):
    call(['Rscript','--vanilla','rdata_to_csv.r',file_rdata,file_csv_output,rdata_df])


def download_and_insert_site_info():
    site_info_rdata = config['roots']['sites']+'/'+config['files']['site_info_rdata']
    site_info_csv_output = config['roots']['sites']+'/'+config['files']['site_info_csv']
    site_info_schema = config['roots']['sql']+'/'+config['files']['site_info_schema']

    #Download
    if config['USE_SITE_INFO_CACHE'] is False:
        download_and_save_url(config['urls']['site_info'], site_info_rdata)

    #Save to csv
    rdata_to_csv(site_info_rdata, site_info_csv_output, 'sites')

    #Insert to postgres and run schema
    run_file(site_info_schema, [['<SITE_INFO_CSV>', '\''+site_info_csv_output+'\'']]) #replace <site_info_csv> with the csv file name


def get_site_codes_in_year_range(start_year, end_year):
    start_date = '01/01/{year}'.format(year=start_year)
    end_date = '01/01/{year}'.format(year=end_year)

    sql = 'select sitecode from orca.laqn_sites where (DateClosed >= {end!r} or DateClosed is null);'.format(end=str(end_date))
    cur = conn.cursor()
    cur.execute(sql)

    site_codes = cur.fetchall()

    conn.commit()
    conn.close()
    return site_codes

def download(site_codes, years):
    """
        Files are in format <site_code_upper>_<year>.Rdata on http://www.londonair.org.uk/r_data/
    """
    count = 0
    for year in years:
        for site in site_codes:
            site = site[0]
            filename = "{site}_{year}.Rdata".format(site=site,year=year)
            url = "http://www.londonair.org.uk/r_data/{filename}".format(filename=filename)
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


                print('Downloaded %s'%site)
    print(count)


#download_and_insert_site_info()
start_year = '2019'
end_year = '2019'
years = ['2019']
site_codes = get_site_codes_in_year_range(start_year, end_year)
download(site_codes, years)







