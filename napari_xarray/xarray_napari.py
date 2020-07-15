"""
This module is an example of a barebones numpy reader plugin for napari.

It implements the ``napari_get_reader`` hook specification, (to create
a reader plugin) but your plugin may choose to implement any of the hook
specifications offered by napari.
see: https://napari.org/docs/plugins/hook_specifications.html

Replace code below accordingly.  For complete documentation see:
https://napari.org/docs/plugins/for_plugin_developers.html
"""
from enum import Enum

import xarray as xr
import numpy as np
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QVBoxLayout,
    QLabel,
)
from napari_plugin_engine import napari_hook_implementation


class LayerType(Enum):
    Image = "image"
    Labels = "labels"


@napari_hook_implementation
def napari_get_reader(path):
    """A basic implementation of the napari_get_reader hook specification.

    Parameters
    ----------
    path : str or list of str
        Path to file, or list of paths.

    Returns
    -------
    function or None
        If the path is a recognized format, return a function that accepts the
        same path or list of paths, and returns a list of layer data tuples.
    """
    if isinstance(path, list):
        # reader plugins may be handed single path, or a list of paths.
        # if it is a list, it is assumed to be an image stack...
        # so we are only going to look at the first file.
        path = path[0]

    # if we know we cannot read the file, we immediately return None.
    # if not path.endswith(".npy"):
    #     return None

    if path.endswith(".nc"):
        # otherwise we return the *function* that can read ``path``.
        return reader_function


def reader_function(path: str):
    """Take a path or list of paths and return a list of LayerData tuples.

    Readers are expected to return data as a list of tuples, where each tuple
    is (data, [add_kwargs, [layer_type]]), "add_kwargs" and "layer_type" are
    both optional.

    Parameters
    ----------
    path : str or list of str
        Path to file, or list of paths.

    Returns
    -------
    layer_data : list of tuples
        A list of LayerData tuples where each tuple in the list contains
        (data, metadata, layer_type), where data is a numpy array, metadata is
        a dict of keyword arguments for the corresponding viewer.add_* method
        in napari, and layer_type is a lower-case string naming the type of layer.
        Both "meta", and "layer_type" are optional. napari will default to
        layer_type=="image" if not provided
    """
    layer_type = "image"
    labels_flags = ["seg", "mask", "segmentation", "labels"]

    class LayerTypeDialog(QDialog):
        nonlocal layer_type

        def __init__(self, parent=None):
            super(LayerTypeDialog, self).__init__(parent)

            txt = QLabel("Layer type is ambiguous, please select a type")

            self.combo = QComboBox()
            for layer_type_ in LayerType:
                self.combo.addItem(layer_type_.name, layer_type_.value)
            self.combo.currentIndexChanged.connect(self.set_layer_type)

            box = QDialogButtonBox(QDialogButtonBox.Ok)
            box.accepted.connect(self.accept)

            layout = QVBoxLayout(self)
            layout.addWidget(txt)
            layout.addWidget(self.combo)
            layout.addWidget(box)

        def set_layer_type(self):
            nonlocal layer_type
            layer_type = self.combo.currentData()

    if isinstance(path, list):
        raise NotImplementedError("multiple paths not accepted yet")

    data = xr.load_dataarray(path)

    if data.dtype == np.bool:
        layer_type = "labels"
    elif any(x in path for x in labels_flags):
        layer_type = "labels"
    else:
        layer_type = "images"
    # else:
    # ambiguous
    # choose_layer_gui = LayerTypeDialog()
    # choose_layer_gui.exec_()

    if "wavelength" in data.dims:
        layer_data = []
        for wvl in data.wavelength.values:
            layer_tpl = (data.sel(wavelength=wvl).values, {"name": wvl}, layer_type)
            layer_data.append(layer_tpl)
    else:
        layer_data = [(data, {}, layer_type)]

    # optional kwargs for the corresponding viewer.add_* method
    # https://napari.org/docs/api/napari.components.html#module-napari.components.add_layers_mixin
    # add_kwargs = {}

    # layer_type = "image"  # optional, default is "image"
    return layer_data
    # return [(data, add_kwargs, layer_type)]
