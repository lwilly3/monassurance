#!/usr/bin/env python
"""Generate ER diagram from SQLAlchemy models."""
import os

from sqlalchemy_schemadisplay import create_schema_graph

from backend.app.db import models  # noqa: F401 ensure models imported
from backend.app.db.base import Base


def main():
    graph = create_schema_graph(metadata=Base.metadata, show_datatypes=False, show_indexes=False, rankdir='LR')
    out_path = os.path.join(os.path.dirname(__file__), '..', 'docs')
    os.makedirs(out_path, exist_ok=True)
    file_png = os.path.abspath(os.path.join(out_path, 'er_diagram.png'))
    graph.write_png(file_png)
    print(f"ER diagram generated at {file_png}")

if __name__ == "__main__":
    main()
