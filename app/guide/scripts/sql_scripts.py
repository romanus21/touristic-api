import os

from app.config import settings

with open(
    os.path.join(
        settings.BASE_DIR,
        "guide",
        "scripts",
        "edges_by_bb.sql",
    )
) as f:
    edges_by_bb = f.read()

with open(
    os.path.join(
        settings.BASE_DIR,
        "guide",
        "scripts",
        "gen_pois_by_bb.sql",
    )
) as f:
    pois_by_bb_inf = f.read()

with open(
    os.path.join(
        settings.BASE_DIR,
        "guide",
        "scripts",
        "nodes_by_bb.sql",
    )
) as f:
    nodes_by_bb = f.read()

with open(
    os.path.join(
        settings.BASE_DIR,
        "guide",
        "scripts",
        "nearest_node_by_bb_and_coord.sql",
    )
) as f:
    nearest_node_by_bb_and_coord = f.read()
