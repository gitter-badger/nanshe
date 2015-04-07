"""
This should act similarly to ``nanshe.learner.generate_neurons`` except it will
have multiple output files due to the nature of ``ruffus``. This is fine as we
want to be able to look at each stage. So, this is the first step in that
direction. However, this currently doesn't handle ``multiprocessing``.
"""

__author__ = "John Kirkham <kirkhamj@janelia.hhmi.org>"
__date__ = "$Apr 06, 2015 14:08:58 EDT$"


import h5py

import ruffus

from nanshe.imp import segment as seg
from nanshe.io.xjson import read_parameters


params = {}


@ruffus.transform(
    ["*.raw.h5", "*.json"],
    ruffus.suffix(".raw.h5"),
    ".pre.h5"
)
def preprocess_data(input_data_filename, output_data_filename):
    global params

    input_data = None
    with h5py.File(input_data_filename, "r") as input_data_file:
        input_data = input_data_file["images"][...]

    output_data = seg.preprocess_data(
        input_data, **params["generate_neurons"]["preprocess_data"]
    )

    with h5py.File(output_data_filename, "w") as output_data_file:
        output_data_file.create_dataset(
            "images",
            shape=output_data.shape,
            dtype=output_data.dtype,
            chunks=True
        )
        output_data_file["images"][...] = output_data

@ruffus.transform(
    [preprocess_data, "*.json"],
    ruffus.suffix(".pre.h5"),
    ".dict.h5"
)
def generate_dictionary(input_data_filename, output_data_filename):
    global params

    input_data = None
    with h5py.File(input_data_filename, "r") as input_data_file:
        input_data = input_data_file["images"][...]

    output_data = seg.generate_dictionary(
        input_data, **params["generate_neurons"]["generate_dictionary"]
    )

    with h5py.File(output_data_filename, "w") as output_data_file:
        output_data_file.create_dataset(
            "images",
            shape=output_data.shape,
            dtype=output_data.dtype,
            chunks=True
        )
        output_data_file["images"][...] = output_data


@ruffus.transform(
    [generate_dictionary, "*.json"],
    ruffus.suffix(".dict.h5"),
    ".post.h5"
)
def postprocess_data(input_data_filename, output_data_filename):
    global params

    input_data = None
    with h5py.File(input_data_filename, "r") as input_data_file:
        input_data = input_data_file["images"][...]

    output_data = seg.postprocess_data(
        input_data, **params["generate_neurons"]["postprocess_data"]
    )

    with h5py.File(output_data_filename, "w") as output_data_file:
        output_data_file.create_dataset(
            "images",
            shape=output_data.shape,
            dtype=output_data.dtype,
            chunks=True
        )
        output_data_file["images"][...] = output_data


def main(*argv):
    global params

    parser = ruffus.cmdline.get_argparse(ignored_args=["config"])
    parser.add_argument(
        "-c", "--config", help="JSON config file", required=True
    )

    options = parser.parse_args(argv[1:])
    config_filename = options.config
    params = read_parameters(config_filename)

    ruffus.cmdline.run(options)

    return(0)


if __name__ == "__main__":
    import sys
    sys.exit(main(*sys.argv))