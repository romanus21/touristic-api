import datetime
import math
from typing import Union

import networkx as nx
from geopandas import GeoDataFrame
from networkx import Graph
from shapely.geometry import Point
from shapely.geometry.base import BaseGeometry

from app.config import settings


class DijkstraGuide:
    search_distance = 500 / 111000

    def __init__(self, graph: Graph, pdf: GeoDataFrame):
        self.graph = graph
        self.pdf: dict[str, dict] = pdf.to_dict()
        self.pois: dict[int, dict[int, set]] = dict()

    def weight_with_tourism(self, u, v, d):
        weight = d[0]["length"]
        poises = self.find_poises(u, v, d[0])
        weight = weight * (0.0001 ** (len(set(poises))))
        return weight

    def find_poises(self, u, v, edge: dict):
        if (
            self.pois.get(min(u, v)) is not None
            and self.pois.get(min(u, v)).get(max(u, v)) is not None
        ):
            return self.pois.get(min(u, v)).get(max(u, v))

        result = []
        self.pois.setdefault(min(u, v), dict())
        self.pois[min(u, v)].setdefault(max(u, v), set())
        if edge["influence_ids"] is None:
            return result
        for osm_id in edge["influence_ids"]:
            ids = [s for s in self.pdf["id"] if self.pdf["id"][s] == osm_id]
            self.pois[min(u, v)][max(u, v)].update(ids)
            result += ids
        return result

    def __length(self, route: list[int]):
        length = 0
        for current in range(len(route) - 1):
            next = current + 1
            u = route[current]
            v = route[next]
            length += self.graph.get_edge_data(u, v)[0].get("length")
        return length

    def compute(self, start, end) -> tuple[list, list, float]:
        self.pois = dict()
        res = nx.dijkstra_path(
            self.graph, start, end, weight=self.weight_with_tourism
        )

        res_poises = {}
        for index in range(1, len(res)):
            start = res[index - 1]
            end = res[index]

            try:
                edge_pois = self.pois.get(start).get(end, set())
            except Exception:
                edge_pois = self.pois.get(end).get(start, set())

            for edge_poi in edge_pois:
                geometry: BaseGeometry = self.pdf["geometry"][edge_poi]

                centroid = geometry.centroid

                influence_area = self.pdf["influence_area"][edge_poi]
                xx, yy = influence_area.exterior.coords.xy
                influence_area_coords = list(zip(xx, yy))

                name = self.pdf["name"][edge_poi]

                if name is None:
                    continue

                res_poises[edge_poi] = {
                    "name": self.pdf["name"][edge_poi],
                    "center": (centroid.x, centroid.y),
                    "influence_area": influence_area_coords,
                }

        length = self.__length(res)
        minutes = math.floor(length / settings.SPEED * 60)

        return res, list(res_poises.values()), minutes
