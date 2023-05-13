import logging

import networkx
import osmnx as ox
from geopandas import GeoDataFrame
from pyrosm import OSM
from shapely import wkt
from sqlalchemy.engine import Engine

from app.config import settings
from app.db import get_engine
from app.guide.dijkstra.guide import DijkstraGuide
from app.guide.scripts.sql_scripts import (
    nodes_by_bb,
    edges_by_bb,
    gen_pois_by_bb_inf,
    djikstra_edges,
    pois_by_bb_inf,
)
from app.utils.geometry import BBox

side_mvmnt = {
    "west": lambda x, y: x[1] - y / settings.MEiDE,
    "east": lambda x, y: x[1] + y / settings.MEiDE,
    "south": lambda x, y: x[0] - y / settings.MEiDE / 2,
    "north": lambda x, y: x[0] + y / settings.MEiDE / 2,
}


def __move_by_sides_of_world(
    point: tuple[float, float], dist: float, side: str
):
    return side_mvmnt[side](point, dist)


def get_graph(
    start_point: tuple[float, float],
    end_point: tuple[float, float],
    engine: Engine,
) -> (networkx.MultiGraph, BBox):
    graph = networkx.MultiGraph(crs="EPSG:4326")

    south, north = (
        (start_point, end_point)
        if start_point[0] < end_point[0]
        else (end_point, start_point)
    )

    west, east = (
        (start_point, end_point)
        if start_point[1] < end_point[1]
        else (end_point, start_point)
    )

    north = __move_by_sides_of_world(north, 400, "north")
    south = __move_by_sides_of_world(south, 400, "south")
    east = __move_by_sides_of_world(east, 400, "east")
    west = __move_by_sides_of_world(west, 400, "west")

    edges = engine.execute(
        djikstra_edges.format(south, east, north, west)
    ).mappings()
    nodes = engine.execute(
        nodes_by_bb.format(south, east, north, west)
    ).mappings()
    nodes = {node.get("id"): node for node in nodes}

    for edge in edges:
        u = edge.get("u")
        u_node: dict = nodes.get(u)
        v = edge.get("v")
        v_node: dict = nodes.get(v)
        key = edge.get("id")
        length = edge.get("length")
        influence_ids = edge.get("influence_ids")
        graph.add_node(u, x=u_node.get("lat"), y=u_node.get("lon"))
        graph.add_node(v, x=v_node.get("lat"), y=v_node.get("lon"))
        graph.add_edge(
            u_for_edge=u,
            v_for_edge=v,
            length=length,
            key=key,
            influence_ids=influence_ids,
        )

    connected_components = networkx.connected_components(graph)
    connected_components = sorted(
        connected_components, key=lambda x: len(x), reverse=True
    )
    largest_connected_graph_nodes = connected_components[0]
    graph = graph.subgraph(largest_connected_graph_nodes)

    bbox = BBox(south=south, east=east, north=north, west=west)

    return graph, bbox


def str_to_geometry(obj):
    return wkt.loads(obj["geometry"])


def get_djikstra_route(start_lat, start_lon, end_lat, end_lon):
    engine = get_engine()
    start_point = (start_lat, start_lon)
    end_point = (end_lat, end_lon)

    bbox: BBox
    graph, bbox = get_graph(start_point, end_point, engine)

    pdf = GeoDataFrame.from_postgis(
        pois_by_bb_inf.format(*bbox.in_order),
        engine,
        geom_col="influence_area",
    )
    pdf["geometry"] = pdf.apply(str_to_geometry, axis=1)

    start_node = ox.nearest_nodes(graph, start_lat, start_lon)
    end_node = ox.nearest_nodes(graph, end_lat, end_lon)

    w = DijkstraGuide(graph, pdf)

    touristic_way, pois, result_minutes = w.compute(start_node, end_node)

    out = {
        "route": [
            (graph.nodes[node_id]["x"], graph.nodes[node_id]["y"])
            for node_id in touristic_way
        ],
        "sights": pois,
        "result_minutes": result_minutes,
    }
    return out
