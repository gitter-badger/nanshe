__author__ = "John Kirkham <kirkhamj@janelia.hhmi.org>"
__date__ = "$Aug 04, 2014 14:48:56 EDT$"


import collections
import itertools
import os
import os.path
import shutil
import tempfile

import numpy

import vigra
import vigra.impex

import nanshe.additional_generators
import nanshe.expanded_numpy

import nanshe.tiff_file_format


class TestTiffFileFormat(object):
    def setup(self):
        self.temp_dir = ""
        self.filedata = collections.OrderedDict()
        self.data = None

        self.data = numpy.random.random_integers(0, 255, (1000, 1, 102, 101, 1)).astype(numpy.uint8)

        self.temp_dir = tempfile.mkdtemp()
        for i, i_str, (a_b, a_e) in nanshe.additional_generators.filled_stringify_enumerate(
                                        itertools.izip(
                                                *nanshe.additional_generators.lagged_generators(
                                                    xrange(0, self.data.shape[0] + 100 - 1, 100)
                                                )
                                        )
                                    ):
            each_filename = os.path.join(self.temp_dir, "test_tiff_" + str(i) + ".tif")
            each_data = self.data[a_b:a_e]

            self.filedata[each_filename] = each_data

            vigra.impex.writeVolume(nanshe.expanded_numpy.tagging_reorder_array(each_data, to_axis_order="czyxt")[0, 0],
                                    os.path.join(self.temp_dir, "test_tiff_" + str(i) + ".tif"), "")

    def test_get_multipage_tiff_shape_dtype(self):
        for each_filename, each_filedata in self.filedata.items():
            each_shape_dtype = nanshe.tiff_file_format.get_multipage_tiff_shape_dtype(each_filename)

            each_filedata = nanshe.expanded_numpy.tagging_reorder_array(each_filedata, to_axis_order="zyxtc")[0]

            assert(each_shape_dtype["shape"] == each_filedata.shape)
            assert(each_shape_dtype["dtype"] == each_filedata.dtype.type)

    def teardown(self):
        shutil.rmtree(self.temp_dir)

        self.temp_dir = ""
        self.filedata = collections.OrderedDict()
        self.data = None