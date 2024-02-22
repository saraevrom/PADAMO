from .node_viewer import create_setter, SIGNAL, APP_TAB

ViewNode = create_setter(APP_TAB+"/Quicklook", SIGNAL, "quicklook_view", "Quicklook",optional=False)