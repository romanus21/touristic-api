from dataclasses import dataclass

from shapely import wkt

from app.config import settings

side_mvmnt = {
    "west": lambda x, y: x[1] - y / settings.MEiDE,
    "east": lambda x, y: x[1] + y / settings.MEiDE,
    "south": lambda x, y: x[0] - y / settings.MEiDE / 2,
    "north": lambda x, y: x[0] + y / settings.MEiDE / 2,
}

BBox = tuple[float, float, float, float]
Point = tuple[float, float]


@dataclass
class BBox:
    north: float
    south: float
    east: float
    west: float

    @property
    def in_order(self):
        return self.south, self.east, self.north, self.west

    def wider(self, meters: float) -> BBox:
        bbox = BBox(
            north=self.north + meters / settings.MEiDE / 2,
            south=self.south - meters / settings.MEiDE / 2,
            east=self.east + meters / settings.MEiDE / 2,
            west=self.west - meters / settings.MEiDE / 2,
        )
        return bbox


def __move_by_sides_of_world(point: Point, dist: float, side: str):
    return side_mvmnt[side](point, dist)


def bbox_from_point(p1: Point) -> BBox:
    north = __move_by_sides_of_world(p1, 1000, "north")
    south = __move_by_sides_of_world(p1, 1000, "south")
    east = __move_by_sides_of_world(p1, 1000, "east")
    west = __move_by_sides_of_world(p1, 1000, "west")

    return BBox(south=south, east=east, north=north, west=west)


def str_to_geometry(obj):
    return wkt.loads(obj["geometry"])
