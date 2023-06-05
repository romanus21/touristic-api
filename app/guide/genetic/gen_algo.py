import concurrent.futures
import random

import networkx
import networkx as nx
from networkx import MultiGraph

from app.guide.algo import Algo, Hour, AlgoResult
from app.guide.pois import Sight

Genotype = tuple[Sight]

pool = concurrent.futures.ThreadPoolExecutor(max_workers=50)


class GenAlgo(Algo):
    speed = 5000

    iterations = 50

    start_population_size = 300
    population_size = 50
    selection_size = 40

    crossing_probability = 0.6
    mutation_probability = 0.2

    def __init__(
        self,
        graph: MultiGraph,
        sights: dict[int, Sight],
        start_node: int,
        route_time: Hour,
    ):
        super().__init__(graph, sights, start_node, route_time)
        self.graph = graph
        self.nodes: set = set(node for node in graph.nodes)

        self.sights = sights

        self.start_node = start_node
        self.route_time = route_time

        desired_sights = max(int(self.route_time / 5), 2)
        desired_sights = min(desired_sights, 20)

        self.harmony_size = min(desired_sights, len(self.sights))

        self.genotype_length = min(desired_sights, len(self.sights))

        self.cache: dict[int, dict[int, list[int]]] = dict()

    def get_cached_route(self, start_node: int, end_node: int) -> list[int]:
        route = self.cache.get(start_node, dict()).get(end_node)
        return route

    def create_cached_route(
        self, start_node: int, end_node: int, route: list[int]
    ):
        self.cache.setdefault(start_node, dict())
        self.cache[start_node][end_node] = route
        reversed_route = route[::-1]
        self.cache.setdefault(end_node, dict())
        self.cache[end_node][start_node] = reversed_route

    @property
    def gens(self) -> dict[int, Sight]:
        return self.sights

    def create_genotype(self) -> Genotype:
        result = list()
        gens = self.gens.copy()
        for _ in range(self.genotype_length):
            choice = random.choice(list(gens.keys()))
            result.append(gens.pop(choice))
        return tuple(result)

    def create_population(self) -> list[Genotype]:
        return [
            self.create_genotype() for _ in range(self.start_population_size)
        ]

    @staticmethod
    def __genotype_to_nodes(genotype: Genotype):
        return [gen.nodes[0] for gen in genotype]

    def __route_distance(self, route: list[int]):
        result = 0
        for index in range(0, len(route) - 1):
            start_node = route[index % len(route)]
            end_node = route[(index + 1) % len(route)]

            edge = self.graph.get_edge_data(start_node, end_node)

            try:
                result += edge[0]["length"]
            except Exception as e:
                print(e)

        return result

    @property
    def ideal_dist(self):
        return self.route_time * self.speed

    def fitness_calculation(self, genotype: Genotype):
        if len(set(genotype)) < self.genotype_length:
            return 0

        node_genotype = self.__genotype_to_nodes(genotype)
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

            if tmp_route is None:
                try:
                    tmp_route = networkx.shortest_path(
                        self.graph,
                        source=start_node,
                        target=end_node,
                    )
                except networkx.exception.NetworkXNoPath:
                    print(f"no way between nodes: {start_node} and {end_node}")
                    return 0
                except networkx.exception.NodeNotFound as e:
                    print(f"no nodes: {e} for {self.start_node}")
                    return 0

                self.create_cached_route(start_node, end_node, tmp_route)

            intersection = set(tmp_route).intersection(set(route))
            intersected += len(intersection)

            route += tmp_route[0 : len(tmp_route) - 1]

        route += [end_node]

        interest = sum([gen.popularity for gen in genotype])

        real_dist = self.__route_distance(route)

        fitness = (
            interest
            * (1 - (real_dist - self.ideal_dist) ** 2 / self.ideal_dist**2)
            * (1 / (2**intersected + 1))
        )

        return fitness

    @staticmethod
    def __range_sort(element):
        return element[1]

    @staticmethod
    def __binary_search(x: float, arr: list):
        low = 0
        high = len(arr) - 1

        while low <= high:
            mid = (high + low) // 2

            if arr[mid][0] < x:
                low = mid + 1
            elif arr[mid][0] < x < arr[mid + 1][0]:
                return mid + 1
            elif arr[mid - 1][0] < x < arr[mid][0]:
                return mid
            elif arr[mid][0] > x:
                high = mid - 1

        return -1

    def __top_selection(
        self, genotypes_fitness: list[tuple[Genotype, float]]
    ) -> list[Genotype]:
        sorted_gf = sorted(genotypes_fitness, key=self.__range_sort)[
            0 : self.selection_size
        ]

        sorted_gf = [gf[0] for gf in sorted_gf]

        return sorted_gf

    def __range_selection(
        self, genotypes_fitness: list[tuple[Genotype, float]]
    ) -> list[Genotype]:
        sorted_gf = sorted(genotypes_fitness, key=self.__range_sort)
        rangs = sum([index + 1 for index in range(len(sorted_gf))])
        genotype_by_percentile = []
        sum_percentile = 0

        for index, gf in enumerate(sorted_gf):
            percentile = index * 100 / rangs
            genotype_by_percentile.append(
                (sum_percentile + percentile, gf[0], gf[1])
            )
            sum_percentile += percentile

        selected_genotypes = set()

        while self.selection_size > len(selected_genotypes):
            choice = random.random() * 100
            index = self.__binary_search(choice, genotype_by_percentile)
            selected_genotypes.add(genotype_by_percentile[index][1])

        return list(selected_genotypes)

    def crossing(self, parent1, parent2) -> tuple[Genotype, Genotype]:
        length = 2
        start = random.randint(0, self.genotype_length - 1)

        child1 = [-1 for _ in range(self.genotype_length)]
        child2 = [-1 for _ in range(self.genotype_length)]

        part1 = [
            parent2[index % self.genotype_length]
            for index in range(start, start + length)
        ]
        part2 = [
            parent1[index % self.genotype_length]
            for index in range(start, start + length)
        ]

        for index in range(length):
            child1[(start + index) % self.genotype_length] = part1[index]
            child2[(start + index) % self.genotype_length] = part2[index]

        un_parted1 = [
            parent1[index]
            for index in range(self.genotype_length)
            if child1[index] == -1
        ]
        un_parted2 = [
            parent2[index]
            for index in range(self.genotype_length)
            if child2[index] == -1
        ]

        element1 = un_parted1.pop(0)
        element2 = un_parted2.pop(0)

        for index in range(
            start + length, start + length + self.genotype_length
        ):
            if child1[index % self.genotype_length] == -1:
                child1[index % self.genotype_length] = element1
                element1 = un_parted1.pop(0) if len(un_parted1) > 0 else None
            if child2[index % self.genotype_length] == -1:
                child2[index % self.genotype_length] = element2
                element2 = un_parted2.pop(0) if len(un_parted2) > 0 else None

        return tuple(child1), tuple(child2)

    def mutation(self, child: Genotype) -> Genotype:
        child: list[Sight] = list(child)

        candidate_index = random.randint(0, self.genotype_length - 1)

        while True:
            replacer_index = random.choice(list(self.gens.keys()))
            replacer = self.gens.get(replacer_index)
            if replacer not in child:
                break

        child[candidate_index] = replacer

        return tuple(child)

    def get_interest(self, solution: list[Sight]):
        interest = sum([gen.popularity for gen in solution])
        return interest

    def get_intersected(self, solution: tuple[Sight]):
        node_genotype = self.__genotype_to_nodes(solution)
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
                    print(f"no way between nodes: {start_node} and {end_node}")
                    return 0
                except networkx.exception.NodeNotFound as e:
                    print(f"no nodes: {e} for {self.start_node}")
                    return 0
                self.create_cached_route(start_node, end_node, tmp_route)

            intersection = set(tmp_route).intersection(set(route))
            intersected += len(intersection)

            route += tmp_route[0 : len(tmp_route) - 1]

        return intersected

    def get_length(self, solution: list[Sight]):
        node_genotype = self.__genotype_to_nodes(tuple(solution))
        node_genotype = [self.start_node] + node_genotype
        genotype_len = len(node_genotype)

        route = []
        end_node = None

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
                    print(f"no way between nodes: {start_node} and {end_node}")
                    return 0
                except networkx.exception.NodeNotFound as e:
                    print(f"no nodes: {e} for {self.start_node}")
                    return 0
                self.create_cached_route(start_node, end_node, tmp_route)

            route += tmp_route[0 : len(tmp_route) - 1]

        route += [end_node]

        real_dist = self.__route_distance(route)

        return real_dist

    def calc(self):
        iterations = dict()
        max_iterations = dict()

        max_fitness = 0
        max_genotype = []
        max_iter = -1

        population = self.create_population()
        genotypes_fitness = list()
        for genotype in population:
            fitness = self.fitness_calculation(genotype)
            if fitness > max_fitness:
                max_fitness = fitness
                max_genotype = genotype
                max_iter = 0
            genotypes_fitness.append((genotype, fitness))

        for iteration in range(1, self.iterations + 1):
            population = []

            # отбор
            selected_genotypes = self.__range_selection(genotypes_fitness)
            genotypes_fitness = list()

            # скрещивание
            for index in range(0, len(selected_genotypes) - 1, 2):
                probability = random.random()
                if probability < self.crossing_probability:
                    child1, child2 = self.crossing(
                        selected_genotypes[index], selected_genotypes[index + 1]
                    )
                else:
                    child1, child2 = (
                        selected_genotypes[index],
                        selected_genotypes[index + 1],
                    )
                population += [child1, child2]

            # мутация
            for index in range(0, len(population)):
                probability = random.random()
                if probability < self.mutation_probability:
                    population[index] = self.mutation(population[index])

            # дополнение популяции
            for _ in range(self.population_size - len(population)):
                population.append(self.create_genotype())

            for genotype in population:
                fitness = self.fitness_calculation(genotype)
                if fitness > max_fitness:
                    max_fitness = fitness
                    max_genotype = genotype
                genotypes_fitness.append((genotype, fitness))

            iterations[iteration] = genotypes_fitness
            max_iterations[iteration] = max_fitness

        node_genotype = self.__genotype_to_nodes(max_genotype)
        # node_genotype = [self.start_node] + node_genotype

        for index, gen in enumerate(max_genotype):
            gen.name = f"{index + 1}. {gen.name}"

        result = AlgoResult(solution=max_genotype)

        return result
