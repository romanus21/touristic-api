import math

import networkx
from networkx import MultiGraph
from sqlalchemy.engine import Engine

from app.config import settings
from app.db import get_engine
from app.guide.cuckoo.cuckoo import CuckooAlgo
from app.guide.pois import Sight, LeafletSight
from app.guide.scripts.sql_scripts import (
    edges_by_bb,
    nodes_by_bb,
    gen_pois_by_bb_inf,
    nearest_node_by_bb_and_coord,
)
from app.utils.geometry import BBox, bbox_from_point


def get_graph(
    bbox: BBox,
    engine: Engine,
) -> networkx.MultiGraph:
    graph = networkx.MultiGraph(crs="EPSG:4326")

    edges = engine.execute(edges_by_bb.format(*bbox.in_order)).mappings()
    nodes = engine.execute(nodes_by_bb.format(*bbox.in_order)).mappings()
    nodes = {node.get("id"): node for node in nodes}

    for edge in edges:
        u = edge.get("u")
        u_node: dict = nodes.get(u)
        v = edge.get("v")
        v_node: dict = nodes.get(v)
        key = edge.get("id")
        length = edge.get("length")
        graph.add_node(u, x=u_node.get("lat"), y=u_node.get("lon"))
        graph.add_node(v, x=v_node.get("lat"), y=v_node.get("lon"))
        graph.add_edge(u_for_edge=u, v_for_edge=v, length=length, key=key)

    connected_components = networkx.connected_components(graph)
    connected_components = sorted(
        connected_components, key=lambda x: len(x), reverse=True
    )
    largest_connected_graph_nodes = connected_components[0]
    graph = graph.subgraph(largest_connected_graph_nodes)

    return graph


def get_sights(
    bbox: BBox, graph: MultiGraph, engine: Engine, filters: list[str]
) -> dict[int, Sight]:
    str_filters = f" and ({' or '.join(filters)})" if len(filters) > 0 else ""
    pois = engine.execute(
        gen_pois_by_bb_inf.format(*bbox.in_order, filters=str_filters)
    ).mappings()

    sights = dict()
    for sight in pois:
        _id = sight.get("id")
        name = sight.get("name")
        popularity = sight.get("popularity")
        nodes = sight.get("nearest_nodes")
        nodes = [node for node in nodes if graph.has_node(node)]
        if not nodes:
            continue
        sight = Sight(nodes=nodes, id=_id, popularity=popularity, name=name)
        sights[_id] = sight

    return sights


def get_node_by_coord(lat: float, lon: float, bbox: BBox, engine: Engine):
    node = engine.execute(
        nearest_node_by_bb_and_coord.format(*bbox.in_order, lat, lon)
    ).fetchone()[0]
    return node


def get_cycle_route(
    start_lat, start_lon, minutes: float, filters: list[str]
) -> tuple[list[list[float, float]], list[LeafletSight], float]:
    engine = get_engine()
    start_point = (start_lat, start_lon)
    bbox = bbox_from_point(start_point)

    graph = get_graph(bbox, engine=engine)
    sights = get_sights(bbox, graph, engine=engine, filters=filters)
    print(len(sights))

    start_node = get_node_by_coord(
        lat=start_lat, lon=start_lon, bbox=bbox, engine=engine
    )
    algo = CuckooAlgo(
        sights=sights,
        graph=graph,
        start_node=start_node,
        route_time=minutes,
    )

    result = algo.calc()

    route = []
    route_length = 0
    nodes = [start_node]

    for index in range(0, len(result.solution)):
        node = result.solution[index].nodes[0]
        nodes.append(node)

    nodes_number = len(nodes)
    for index in range(0, nodes_number + 1):
        source = nodes[index % nodes_number]
        target = nodes[(index + 1) % nodes_number]
        tmp_route_nodes = networkx.shortest_path(
            graph, source=source, target=target
        )
        for _index in range(len(tmp_route_nodes) - 1):
            route_length += graph.get_edge_data(
                tmp_route_nodes[_index], tmp_route_nodes[_index + 1]
            )[0]["length"]
        for node in tmp_route_nodes:
            node = graph.nodes[node]
            route.append([node["x"], node["y"]])

    leaflet_sights: list[LeafletSight] = [
        LeafletSight(sight, engine) for sight in result.solution
    ]

    minutes = math.floor(route_length / settings.SPEED * 60)

    return route, leaflet_sights, minutes
