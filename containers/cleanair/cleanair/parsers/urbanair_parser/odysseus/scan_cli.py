

import typer

app = typer.Typer()

class ScanSoot:
	def __init__(self, borough, grid_resolution, ts_method, days_in_past, days_in_future):
		self.borough = borough
		self.grid_resolution = grid_resolution
		self.ts_method = ts_method
		self.days_in_past = days_in_past
		self.days_in_future = days_in_future
		# Extras
		self.start = today - days_in_past - days_in_future
		self.upto = today
	def scoot_fishnet_readings(self):
		# Uses start and upto to get right amount of data
	def run(self):
		# 1) Get Readings
		readings = self.scoot_fishnet_readings()
		# 2) Pre-process
		processed = ss.preprocessor(readings)
		# 3) Build Forecast
		forecast = ss.forecast(processed, self.days_in_past, self.days_in_future, self.ts_method)
		# 4) Aggregate readings/forecast to grid level
		aggregate = aggregate_readings_to_grid(forecast)
		# 5) Scan
		all_scores = scan(aggregate, self.grid_resolution)
		# 6) Aggregate average scores to grid level
		grid_level_scores = average_gridcell_scores(all_scores, self.grid_resolution)
		return grid_level_scores
	def update_remote_tables(self):
		metric_df = self.run()
		upload_records = metric_df.to_dict('records')
		self.commit_records(upload_records, on_conflict="overwrite", table=some_scan_table)		

@typer.command()
def stats():
    # get the scoot readings given start date, end date, (borough)
    # preprocessing step

    # TODO create database tables for scanstats
    # write to database table
