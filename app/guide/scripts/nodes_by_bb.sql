with edges as (select st_union(geometry) edge_union
               from (select *
                     from osm_edges
                     where osm_edges.geometry &&
                           st_makeenvelope({0},{1},
                                           {2},{3})
                               ) edges_in_bbox),
     edges_bbox as (select st_extent(edge_union) bbox
                    from edges)
select id, lat, lon
from osm_nodes
where osm_nodes.geometry && (select bbox from edges_bbox);