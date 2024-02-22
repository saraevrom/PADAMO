from padamo.ui_elements.configurable_gridview import DeviceParameters, CellLayer
from padamo.utilities.workspace import Workspace

DEVICE_VTL = DeviceParameters(name="Verkhnetulomsky", flipped_x=True,
                              flipped_y=False,
                              pixel_size=(2.85, 2.85),
                              pixels_shape=(8, 8),
                              supercells=[
                                  CellLayer(layer_name="Detector", gap=(4.0, 4.0), shape=(2, 2), mask=[])
                              ])

DEVICE_LOZ = DeviceParameters(name="Lovozero", flipped_x=True,
                              flipped_y=False,
                              pixel_size=(2.85, 2.85),
                              pixels_shape=(8, 8),
                              supercells=[
                                  CellLayer(layer_name="Elementary cell", gap=(4.0, 4.0), shape=(2, 2), mask=[]),
                                  CellLayer(layer_name="Detector", gap=(6.0, 6.0), shape=(1, 3), mask=[]),
                              ])


class DetectorWorkspace(Workspace):
    def populate(self):
        with open(self("vtl.json"), "w") as fp:
            fp.write(DEVICE_VTL.to_json())

        with open(self("loz.json"), "w") as fp:
            fp.write(DEVICE_LOZ.to_json())
