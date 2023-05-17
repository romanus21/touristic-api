from datetime import datetime

from app.guide.cuckoo.route import (
    get_cycle_route,
)
from app.guide.dijkstra.route import get_djikstra_route


def calc():
    start_lat, start_lon = (59.93512000000004, 30.311480000000074)
    get_cycle_route(start_lat, start_lon, 60)


def calc_route():
    start_lat, start_lon = (59.90502001713264, 30.314780012851003)
    end_lat, end_lon = (59.91502001713264, 30.324780012851003)
    print(get_djikstra_route(start_lat, start_lon, end_lat, end_lon))


if __name__ == "__main__":
    # print(settings.BASE_DIR)
    print("qwe")
    start = datetime.now()
    calc()
    end = datetime.now()
    print((end - start).seconds)
    # start = datetime.now()
    # calc()
    # end = datetime.now()
    # print((end-start).seconds)
    # start = datetime.now()
    # calc()
    # end = datetime.now()
    # print((end-start).seconds)
