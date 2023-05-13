from pydantic import BaseModel


class Point(BaseModel):
    lat: float
    lon: float

    @property
    def xy(self):
        return self.lat, self.lon


class CalcCyclicRoute(BaseModel):
    point: Point
    minutes: float


class CalcLinearRoute(BaseModel):
    start_point: Point
    end_point: Point
