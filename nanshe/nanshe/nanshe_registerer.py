#!/usr/bin/env python

__author__ = "John Kirkham <kirkhamj@janelia.hhmi.org>"
__date__ = "$Feb 20, 2015 13:00:51 EST$"


import h5py
from lazyflow.utility import PathComponents

import debugging_tools
import read_config

import expanded_numpy
import registration



# Get the logger
logger = debugging_tools.logging.getLogger(__name__)



@debugging_tools.log_call(logger)
def main(*argv):
    """
        Simple main function (like in C). Takes all arguments (as from sys.argv) and returns an exit status.

        Args:
            argv(list):     arguments (includes command line call).

        Returns:
            int:            exit code (0 if success)
    """

    # Only necessary if running main (normally if calling command line). No point in importing otherwise.
    import argparse

    argv = list(argv)

    # Creates command line parser
    parser = argparse.ArgumentParser(description = "Parses input from the command line for a registration job.")

    parser.add_argument("config_filename",
                        metavar = "CONFIG_FILE",
                        type = str,
                        help = "JSON file that provides configuration options for how to import TIFF(s)."
    )
    parser.add_argument("input_file",
                        metavar = "INPUT_FILE",
                        type = str,
                        nargs = "+",
                        help = "HDF5 file to import (this should include a path to where the internal dataset should be stored)."
    )

    parser.add_argument("output_file",
                        metavar = "OUTPUT_FILE",
                        type = str,
                        nargs = 1,
                        help = "HDF5 file to export (this should include a path to where the internal dataset should be stored)."
    )

    # Results of parsing arguments (ignore the first one as it is the command line call).
    parsed_args = parser.parse_args(argv[1:])

    # Go ahead and stuff in parameters with the other parsed_args
    parsed_args.parameters = read_config.read_parameters(parsed_args.config_filename)
    parsed_args.input_file_components = PathComponents(parsed_args.input_file)
    parsed_args.output_file_components = PathComponents(parsed_args.output_file)


    with h5py.File(parsed_args.input_file_components.filename, "r") as input_file:
        with h5py.File(parsed_args.output_file_components.filename, "a") as output_file:
            data = input_file[parsed_args.input_file_components.internalPath][...]
            result = registration.register_mean_offsets(data, **parsed_args.parameters)
            result = expanded_numpy.truncate_masked_frames(result)
            output_file[parsed_args.output_file_components.internalPath] = result

    return(0)


if __name__ == "__main__":
    # only necessary if running main (normally if calling command line). no point in importing otherwise.
    import sys

    # call main if the script is loaded from command line. otherwise, user can import package without main being called.
    sys.exit(main(*sys.argv))