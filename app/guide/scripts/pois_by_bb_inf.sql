select st_astext(geometry) as geometry, influence_area, id, name
from osm_pois
where osm_pois.geometry
&& st_makeenvelope({0},
{1}, {2}, {3})