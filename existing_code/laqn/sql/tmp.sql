select 
   array_agg(site_id) as arr
from 
   orca.laqn_hourly_data_with_geom 
where 
   date='2018-03-01 10:00:00' 
group by geom;

select
   array_agg(id),
   array_agg(no2)
from
   (
      select
         unnest(sites.arr) as id,
         geom
      from
         (
            select 
               array_agg(site_id) as arr,
               geom
            from 
               orca.laqn_hourly_data_with_geom 
            where 
               date='2018-03-01 10:00:00' 
            group by geom
         ) as sites
      where
         array_length(sites.arr, 1) > 1
   ) as sites,
   orca.laqn_hourly_data_with_geom as data
where
   sites.id = data.site_id and
   data.date='2018-03-01 10:00:00'
group by
   sites.geom;

