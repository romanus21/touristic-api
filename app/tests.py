import itertools

from app.db import get_engine
from app.guide.cuckoo.cuckoo import CuckooAlgo
from app.guide.dijkstra.route import get_djikstra_route
from app.guide.cuckoo.route import (
    get_graph,
    get_sights,
    get_node_by_coord,
)
from app.utils.geometry import bbox_from_point


def calc():
    start_lat, start_lon = (59.90502001713264, 30.314780012851003)
    desired_sights = 10

    engine = get_engine()
    start_point = (start_lat, start_lon)
    bbox = bbox_from_point(start_point)

    graph = get_graph(bbox, engine=engine)
    sights = get_sights(bbox, graph, engine=engine)

    start_node = get_node_by_coord(
        lat=start_lat, lon=start_lon, bbox=bbox, engine=engine
    )

    max_fitness = 0
    solution = []
    for perm in itertools.permutations(sights.values()):
        fitness = CuckooAlgo(
            desired_sights=desired_sights,
            sights=sights,
            graph=graph,
            start_node=start_node,
            route_time=1,
        ).fitness_calculation(list(perm))
        if fitness > max_fitness:
            max_fitness = fitness
            solution = perm

    print(solution)


def calc_route():
    start_lat, start_lon = (59.90502001713264, 30.314780012851003)
    end_lat, end_lon = (59.91502001713264, 30.324780012851003)
    print(get_djikstra_route(start_lat, start_lon, end_lat, end_lon))


if __name__ == "__main__":
    calc_route()
