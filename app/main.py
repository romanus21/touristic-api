from http.client import HTTPException

import folium.vector_layers
import uvicorn
from fastapi import FastAPI, Request
from folium import folium
from starlette.templating import Jinja2Templates

from app.config import settings
from app.guide.cuckoo.route import get_cycle_route
from app.guide.dijkstra.route import get_djikstra_route
from app.schemas import Point, CalcCyclicRoute, CalcLinearRoute


async def not_found_error(request: Request, exc: HTTPException):
    return templates.TemplateResponse(
        "404.html", {"request": request}, status_code=404
    )


exception_handlers = {
    404: not_found_error,
}

app = FastAPI(exception_handlers=exception_handlers)
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("home.html", context={"request": request})


@app.get("/cyclic_route")
def map(request: Request):
    figure = folium.Figure()

    m = folium.Map(location=(59, 30), zoom_start=15)
    m.add_to(figure)

    figure.render()
    context = {
        "request": request,
        "map": figure,
    }
    return templates.TemplateResponse("show_cyclic_map.html", context=context)


@app.post("/cyclic_route")
def get_cyclic_route(request: CalcCyclicRoute):
    route, sights, minutes = get_cycle_route(
        *request.point.xy, minutes=request.minutes
    )

    return {"route": route, "sights": sights, "minutes": minutes}


@app.get("/linear_route")
def map(request: Request):
    figure = folium.Figure()

    m = folium.Map(location=(59, 30), zoom_start=15)
    m.add_to(figure)

    figure.render()
    context = {
        "request": request,
        "map": figure,
    }
    return templates.TemplateResponse("show_linear_map.html", context=context)


@app.post("/linear_route")
def show_route(request: CalcLinearRoute):
    result = get_djikstra_route(
        *request.start_point.dict().values(), *request.end_point.dict().values()
    )

    return result


if __name__ == "__main__":
    uvicorn.run(
        app=app,
        host="localhost",
        port=settings.PORT,
    )