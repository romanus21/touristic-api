with pois_bbox as (select *
                   from osm_pois
                   where osm_pois.geometry
                             && st_makeenvelope({0},
{1}, {2}, {3}))
select id,
       coalesce(name, replace(wikipedia, 'ru:', ''), amenity,
           historic, memorial, tourism, monument) as name,
       popularity, nearest_nodes
from pois_bbox pbb;