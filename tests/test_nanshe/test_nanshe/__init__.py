__author__ = "John Kirkham <kirkhamj@janelia.hhmi.org>"
__date__ = "$Mar 27, 2015 19:27:22 EDT$"

__all__ = [
    "test_additional_io", "test_advanced_image_processing",
    "test_debugging_tools", "test_extended_region_props",
    "test_generic_decorators", "test_HDF5_recorder", "test_HDF5_searchers",
    "test_HDF5_serializers", "test_nanshe_converter", "test_nanshe_learner",
    "test_nanshe_registerer",  # "test_nanshe_viewer",
    "test_read_config", "test_registration", "test_tiff_file_format",
    "testPathHelpers"
]


import test_additional_io
import test_advanced_image_processing
import test_debugging_tools
import test_extended_region_props
import test_generic_decorators
import test_HDF5_recorder
import test_HDF5_searchers
import test_HDF5_serializers
import test_nanshe_converter
import test_nanshe_learner
import test_nanshe_registerer
# import test_nanshe_viewer
import test_read_config
import test_registration
import test_tiff_file_format
import testPathHelpers