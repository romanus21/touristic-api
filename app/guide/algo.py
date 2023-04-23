import abc
from abc import ABC
from dataclasses import dataclass

from networkx import MultiDiGraph, MultiGraph

from app.guide.pois import Sight

Hour = float


@dataclass
class AlgoResult:
    solution: tuple[Sight]


class Algo(ABC):
    @abc.abstractmethod
    def __init__(
        self,
        graph: MultiGraph,
        sights: dict[int, Sight],
        start_node: int,
        route_time: Hour,
        desired_sights: int,
    ):
        pass

    def calc(self) -> AlgoResult:
        raise NotImplementedError()
