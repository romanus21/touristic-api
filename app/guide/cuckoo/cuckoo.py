import logging
import random
from copy import copy
from dataclasses import dataclass
from typing import Any

import networkx
import networkx as nx
from networkx import MultiGraph

from app.config import settings
from app.guide.algo import Hour, Algo, AlgoResult
from app.guide.pois import Sight


@dataclass
class Cuckoo:
    c: list[Sight]
    e: float

    def __copy__(self):
        return Cuckoo(c=self.c.copy(), e=self.e)


@dataclass
class Nest:
    c: list[Sight]
    e: float

    def __init__(self, cuckoo: Cuckoo):
        self.c = cuckoo.c.copy()
        self.e = cuckoo.e

    def __copy__(self):
        return Cuckoo(c=self.c.copy(), e=self.e)


class CuckooAlgo(Algo):
    iterations = 100

    cuckoos_number = 50
    nests_number = 50

    deletion_probability = 0.01

    def __init__(
        self,
        graph: MultiGraph,
        sights: dict[int, Sight],
        start_node: int,
        route_time: Hour,
        desired_sights: int,
    ):
        super().__init__(graph, sights, start_node, route_time, desired_sights)
        self.graph = graph
        self.nodes: set = set(node for node in graph.nodes)
        self.sights = sights
        self.start_node = start_node
        self.route_time = route_time

        desired_sights = max(int(self.route_time / 10), 2)
        desired_sights = min(desired_sights, 20)

        self.harmony_size = min(desired_sights, len(self.sights))

        self.cuckoos: list[Cuckoo] = list()
        self.nests: list[Nest] = list()
        self.scope: dict[Sight, int] = dict()
        self.reverse_scope: dict[int, Sight] = dict()
        self.set_scope()
        self.reverse_scope = dict(zip(self.scope.values(), self.scope.keys()))

        self.best_fitness = 0
        self.best_cuckoo: Any[Cuckoo, None] = None

        self.__cache: dict[int, dict[int, list[int]]] = dict()
        self.__length_cache: dict[int, dict[int, list[float]]] = dict()

    def set_scope(self):
        for index, sight in enumerate(list(self.sights.values())):
            self.scope[sight] = index

    def moving_index(self, sight: Sight, delta: int):
        index = self.scope[sight]
        return (index + delta) % len(self.scope)

    def get_cached_route(self, start_node: int, end_node: int) -> list[int]:
        route = self.__cache.get(start_node, dict()).get(end_node)
        return route

    def create_cached_route(
        self, start_node: int, end_node: int, route: list[int]
    ):
        self.__cache.setdefault(start_node, dict())
        self.__cache[start_node][end_node] = route
        reversed_route = route[::-1]
        self.__cache.setdefault(end_node, dict())
        self.__cache[end_node][start_node] = reversed_route

    def create_cuckoo(self) -> Cuckoo:
        result = list()
        gens = self.sights.copy()
        for _ in range(self.harmony_size):
            choice = random.choice(list(gens.keys()))
            result.append(gens.pop(choice))
        cuckoo = Cuckoo(c=result, e=self.fitness_calculation(result))
        return cuckoo

    @staticmethod
    def __cuckoo_to_nodes(harmony: list[Sight]):
        return [chord.nodes[0] for chord in harmony]

    def __create_cache(self, start, end, length):
        self.__length_cache.setdefault(start, dict())
        self.__length_cache[start][end] = length
        self.__length_cache.setdefault(end, dict())
        self.__length_cache[end][start] = length

    def __route_distance(self, route: list[int]):
        result = 0
        for index in range(0, len(route) - 1):
            start_node = route[index % len(route)]
            end_node = route[(index + 1) % len(route)]

            length = self.__length_cache.get(start_node, dict()).get(end_node)
            if not length:
                edge = self.graph.get_edge_data(start_node, end_node)
                length = edge[0]["length"]
                self.__create_cache(start_node, end_node, length)

            result += length

        return result

    @property
    def ideal_dist(self):
        return self.route_time * settings.SPEED

    def fitness_calculation(self, cuckoo: list[Sight]):
        if len(set(cuckoo)) < self.harmony_size:
            return 0

        node_genotype = self.__cuckoo_to_nodes(cuckoo)
        node_genotype = [self.start_node] + node_genotype
        genotype_len = len(node_genotype)

        route = []
        end_node = None

        intersected = 0

        for index in range(0, genotype_len):
            start_index = index % genotype_len
            end_index = (index + 1) % genotype_len
            start_node = node_genotype[start_index]
            end_node = node_genotype[end_index]

            tmp_route = self.get_cached_route(start_node, end_node)
            if not tmp_route:
                try:
                    tmp_route = nx.shortest_path(
                        self.graph, start_node, end_node
                    )
                except networkx.exception.NetworkXNoPath:
                    logging.error(
                        f"no way between nodes: {start_node} and {end_node}"
                    )
                    return 0
                self.create_cached_route(start_node, end_node, tmp_route)

            intersection = set(tmp_route).intersection(set(route))
            intersected += len(intersection)

            route += tmp_route[0 : len(tmp_route) - 1]

        route += [end_node]

        interest = sum([gen.popularity for gen in cuckoo])

        real_dist = self.__route_distance(route)

        fitness = (
            interest
            * (1 - (real_dist - self.ideal_dist) ** 3 / self.ideal_dist**3)
            * (1 / (intersected * 2 + 1))
        )

        return fitness

    def init_population(self):
        for _ in range(self.cuckoos_number):
            cuckoo = self.create_cuckoo()
            self.cuckoos.append(cuckoo)
        for _ in range(self.nests_number):
            self.nests.append(Nest(Cuckoo(c=[], e=0)))

    def cuckoos_flight(self):
        for c_index, cuckoo in enumerate(self.cuckoos):
            for s_index, sight in enumerate(cuckoo.c):
                r1 = random.choice([-1, 1])
                r2 = random.random() * 20

                delta = r1 * r2**2
                sight_global_index = self.scope[sight]
                self.cuckoos[c_index].c[s_index] = self.reverse_scope[
                    int((sight_global_index + delta) % len(self.sights))
                ]
                self.cuckoos[c_index].e = self.fitness_calculation(
                    self.cuckoos[c_index].c
                )

    def lay_eggs(self):
        for index, cuckoo in enumerate(self.cuckoos):
            ind = random.randint(0, self.nests_number - 1)

            if cuckoo.e >= self.nests[ind].e:
                self.nests[ind] = Nest(cuckoo)

                if cuckoo.e > self.best_fitness:
                    self.best_fitness = cuckoo.e
                    self.best_cuckoo = copy(cuckoo)
            else:
                self.cuckoos[index] = Cuckoo(
                    c=self.nests[ind].c, e=self.nests[ind].e
                )

        for nest in self.nests:
            if random.random() < self.deletion_probability:
                nest.c = []
                nest.e = 0

    def calc(self):
        self.init_population()

        for iteration in range(self.iterations):
            self.cuckoos_flight()
            self.lay_eggs()

        if not self.best_cuckoo:
            raise Exception("no best harmony")

        result = AlgoResult(solution=self.best_cuckoo.c)

        return result
