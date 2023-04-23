from dataclasses import dataclass

import shapely
from shapely import wkb, wkt
from shapely.geometry.base import BaseGeometry
from sqlalchemy.engine import Engine


@dataclass
class Sight:
    id: int
    popularity: int
    name: str
    nodes: list[int]

    def __hash__(self):
        return self.id

    def get_geometry(self, engine: Engine) -> BaseGeometry:
        rs = engine.execute(
            f"SELECT st_astext(geometry) FROM osm_pois WHERE id = {self.id}"
        )
        return wkt.loads(rs.first()[0])

    def get_wiki(self, engine: Engine) -> str:
        rs = engine.execute(
            f"SELECT wikipedia FROM osm_pois WHERE id = {self.id}"
        )
        article = rs.first()[0]
        link = None
        if article:
            link = f"https://ru.wikipedia.org/wiki/{article}".replace(" ", "_")
        return link


class LeafletSight:
    def __init__(self, sight: Sight, engine: Engine):
        self.name = sight.name
        center = sight.get_geometry(engine).centroid.xy
        self.center = center[0][0], center[1][0]
        self.wiki_url = sight.get_wiki(engine)
