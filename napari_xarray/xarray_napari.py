"""
This module is an example of a barebones numpy reader plugin for napari.

It implements the ``napari_get_reader`` hook specification, (to create
a reader plugin) but your plugin may choose to implement any of the hook
specifications offered by napari.
see: https://napari.org/docs/plugins/hook_specifications.html

Replace code below accordingly.  For complete documentation see:
https://napari.org/docs/plugins/for_plugin_developers.html
"""
import json

import numpy as np
import xarray as xr
from napari_plugin_engine import napari_hook_implementation
from pathlib import Path


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
    label_flags = ["seg", "mask", "segmentation", "labels"]
    channel_dim = "wavelength"

    try:
        with open(Path.home() / ".napari-xarray-config.json", "r") as f:
            config = json.load(f)
            label_flags = config.get("label_flags", label_flags)
            channel_dim = config.get("channel_dim", channel_dim)
    except IOError:
        pass

    if isinstance(path, list):
        raise NotImplementedError("multiple paths not accepted yet")

    data = xr.load_dataarray(path)

    if data.dtype == np.bool:
        layer_type = "labels"
    elif any(x in path for x in label_flags):
        layer_type = "labels"
    else:
        layer_type = "image"

    if channel_dim in data.dims:
        layer_data = []
        for wvl in data[channel_dim].values:
            layer_tpl = (
                data.sel(**{channel_dim: wvl}).values,
                {"name": wvl},
                layer_type,
            )
            layer_data.append(layer_tpl)
    else:
        # optional kwargs for the corresponding viewer.add_* method
        # https://napari.org/docs/api/napari.components.html#module-napari.components.add_layers_mixin
        add_kwargs = {}
        layer_data = [(data, add_kwargs, layer_type)]

    return layer_data
