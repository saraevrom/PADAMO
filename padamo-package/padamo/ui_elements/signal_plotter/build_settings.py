from ..settings_frame import SettingMenu, DoubleValue, ComboboxValue, CheckboxValue, IntValue, EntryValue

def build_menu(menu: SettingMenu):
    menu.add_setting(ComboboxValue, "lightcurve", "Light curve","Off",
                     options=["Off", "All", "Selected"], sensitive=True)
    menu.add_setting(IntValue, "lightcurve_ma", "Light curve MA", 1)
    menu.add_setting(CheckboxValue, "lightcurve_mean", "Use mean instead of sum in LC", False, sensitive=True)
    menu.add_setting(CheckboxValue, "lightcurve_median_offset", "Offset LC to median", False, sensitive=True)
    menu.add_setting(CheckboxValue, "lightcurve_suppress_negative", "Suppress LC negative values", False, sensitive=True)
    menu.add_setting(CheckboxValue, "display_full_matrix", "Display full pixel map", False,
                     sensitive=True)
    menu.add_setting(CheckboxValue, "show_pixels", "Show pixel signals", True, sensitive=True)
    menu.add_setting(IntValue, "tick_label_size", "Tick label size",10)
    menu.add_setting(EntryValue, "title", "Title","")
    menu.add_setting(EntryValue, "x_label", "X label","")
    menu.add_setting(EntryValue, "y_label", "Y label","")
    menu.add_setting(DoubleValue, "threshold", "Signal lower threshold", 3.5)
    menu.add_setting(CheckboxValue, "threshold_whole", "Seek in all frames", True)
    menu.add_setting(IntValue, "threshold_frame_start", "Detection Frame start", 0)
    menu.add_setting(IntValue, "threshold_frame_end", "Detection Frame end", 1)
