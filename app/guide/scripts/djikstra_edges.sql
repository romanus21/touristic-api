with edges_bb as (select *
                  from osm_edges
                  where osm_edges.geometry &&
                        st_makeenvelope({0}, {1},
                                        {2}, {3})),
     intersected_edges as (select edges_bb.v,
                                  edges_bb.u,
                                  array_agg(pois_bb.id) influence_ids
                           from edges_bb
                                    join (select *
                                          from osm_pois
                                          where osm_pois.geometry &&
                                                st_makeenvelope(
                                                        {0},
                                                        {1},
                                                        {2},
                                                        {3})) pois_bb
                                         on st_intersects(edges_bb.geometry,
                                                          pois_bb.influence_area)
                           group by edges_bb.v, edges_bb.u)
select
       edges_bbb.u,
       edges_bbb.v,
       length,
       influence_ids
from (select *
      from osm_edges
      where osm_edges.geometry &&
            st_makeenvelope({0}, {1},
                            {2}, {3})) edges_bbb
         left join intersected_edges on edges_bbb.u = intersected_edges.u and
                                        edges_bbb.v = intersected_edges.v;