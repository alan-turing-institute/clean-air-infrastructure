import sys
sys.path.append('/Users/ogiles/Documents/project_repos/clean-air-infrastructure/docker/')

from datasources import LondonBoundary, LAQNDatabase, HexGrid, UKMap



# Import datasources
laqn = LAQNDatabase(secretfile = '.db_inputs_local_secret.json')
hex_grid = HexGrid(secretfile = '.db_inputs_local_secret.json')

print('all_loaded')