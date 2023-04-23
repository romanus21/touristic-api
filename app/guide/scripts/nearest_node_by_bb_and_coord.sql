SELECT id
FROM (select * from osm_nodes
               where osm_nodes.geometry &&
            st_makeenvelope({0}, {1},
                            {2}, {3})) nodes
ORDER BY st_distance(geometry,
                     geometry('SRID=4326;POINT({4} {5})'))
LIMIT 1
