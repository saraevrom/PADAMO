import json
from padamo.utilities.appdata_workspace import AppWorkspace
from .default_conf import DEFAULT_SCHEME


class GraphWorkspace(AppWorkspace):
    SUBPATH = "graphs"

    def populate(self):
        with open(self("default_scheme.json"), "w") as fp:
            json.dump(DEFAULT_SCHEME, fp)
