
DEFAULT_SCHEME = [
                    {
                        "constants": {
                            "spatial_field": "pdm_2d_rot_global",
                            "temporal_field": "unixtime_dbl_global"
                        },
                        "bound_class": "padamo.node_lib.node_hdf5.SimpleH5SourceArray",
                        "position": [
                            207,
                            259
                        ],
                        "outputs": {
                            "signal": [
                                [
                                    1,
                                    "value"
                                ]
                            ]
                        }
                    },
                    {
                        "constants": {},
                        "bound_class": "padamo.node_lib.node_viewer.current_view",
                        "position": [
                            931,
                            264
                        ],
                        "outputs": {}
                    },
                    {
                        "constants": {},
                        "bound_class": "padamo.node_lib.node_viewer.loaded_file",
                        "position": [
                            22,
                            257
                        ],
                        "outputs": {
                            "value": [
                                [
                                    0,
                                    "filename"
                                ]
                            ]
                        }
                    }
                ]