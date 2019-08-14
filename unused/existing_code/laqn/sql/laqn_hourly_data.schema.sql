drop table if exists orca.laqn_hourly_data;

create table orca.laqn_hourly_data (
   site varchar(3) not null,
   date TIMESTAMP not null,
   nox double precision,
   no2 double precision,
   o3 double precision,
   co double precision,
   pm10_raw double precision,
   pm10 double precision,
   pm25 double precision
);

COPY orca.laqn_hourly_data FROM <data_file> HEADER DELIMITER ',' CSV;
