select u,
       v,
       length
from (select *
      from osm_edges
      where osm_edges.geometry &&
            st_makeenvelope({0}, {1},
                            {2}, {3})) edges_in_bbox;