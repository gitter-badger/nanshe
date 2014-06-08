#!/usr/bin/env python

__author__="John Kirkham"
__date__ ="$Apr 9, 2014 4:00:40PM$"


import os

# Generally useful and fast to import so done immediately.
import numpy

# Need in order to have logging information no matter what.
import advanced_debugging

import HDF5_logger

# Short function to process image data.
import advanced_image_processing

# For IO. Right now, just includes read_parameters for reading a config.json file.
import read_config

import HDF5_serializers

import vigra
import vigra.impex

# Get the logger
logger = advanced_debugging.logging.getLogger(__name__)



@advanced_debugging.log_call(logger)
def batch_generate_save_dictionary(*new_filenames, **parameters):
    """
        Uses generate_save_dictionary to process a list of filename (HDF5 files) with the given parameters for trainDL.
        Results will be saved in each file.
        
        Args:
            new_filenames     names of the files to read.
            parameters        passed directly to generate_save_dictionary.
    """

    # simple. iterates over each call to generate and save results in given HDF5 file.
    for each_new_filename in new_filenames:
        # runs each one and saves results in each file
        generate_save_dictionary(each_new_filename, **parameters)


@advanced_debugging.log_call(logger)
def generate_save_dictionary(new_filename, debug = False, **parameters):
    """
        Uses advanced_image_processing.generate_dictionary to process a given filename (HDF5 files) with the given parameters for trainDL.
        
        Args:
            new_filenames     name of the internal file to read (should be a Dataset)
            parameters        passed directly to advanced_image_processing.generate_dictionary.
    """
    
    # No need unless loading data. thus, won't be loaded if only using numpy arrays with advanced_image_processing.generate_dictionary.
    import h5py
    
    # Need in order to read h5py path. Otherwise unneeded.
    #import lazyflow.utility.pathHelpers as pathHelpers # Use this when merged into the ilastik framework.
    import pathHelpers
    
    
    new_filename_details = pathHelpers.PathComponents(new_filename)
    
    new_filename_ext = new_filename_details.extension
    new_filename_ext = new_filename_ext.lower()
    new_filename_ext = new_filename_ext.replace(os.path.extsep, "", 1)
    if ( (new_filename_ext == "tif") or (new_filename_ext == "tiff") ):
        # TIFF file. Convert to HDF5
        new_hdf5_filename = new_filename_details.externalDirectory + os.path.sep + new_filename_details.filenameBase + os.path.extsep + "h5"
        internal_path = "images"
        new_hdf5_filepath = new_hdf5_filename + "/" + internal_path
        
        logger.info("Got a TIFF file as input. Will copy over to an HDF5 file, which will be named \"" + new_hdf5_filepath + "\".")
        
        with h5py.File(new_hdf5_filename, "a") as new_hdf5_file:
            data = None
            if vigra.impex.numberImages(new_filename_details.externalPath) > 1:
                # Our algorithm expect double precision
                data = vigra.impex.readVolume(new_filename_details.externalPath, dtype = "DOUBLE")
                data = data.view(numpy.ndarray)
                # TODO: Very hacky. Need to fix. Should also move this to another function.
                # Simon's data has channel and then time. One channel is garbage. So, we dump it.
                # Besides this algorithm does not know what to do with another channel.
                data = data.reshape( data.shape[0:2] + (data.shape[2]/2, 2,) )
                data = vigra.taggedView(data, 'xytc')
                data = data.withAxes('c', 't', 'x', 'y')[0]
                data = data.view(numpy.ndarray)
            else:
                data = vigra.impex.readImage(new_filename_details.externalPath, dtype = "DOUBLE")
                data = vigra.taggedView(numpy.array(data), 'xyc')
                data = data.withAxes('c', 'x', 'y')[0]
                data = data.view(numpy.ndarray)
            
            if internal_path in new_hdf5_file:
                del new_hdf5_file[internal_path]
            
            new_hdf5_file[internal_path] = data
    elif ( (new_filename_ext == "h5") or (new_filename_ext == "hdf5") or (new_filename_ext == "he5") ):
        # HDF5 file. Nothing to do here.
        new_hdf5_filepath = new_filename
    else:
        raise Exception("File with filename: \"" + new_filename + "\""  + " provided with an unknown file extension: \"" + new_filename_ext + "\". Support for ")
    
    
    # Inspect path name to get where the file is and its internal path
    new_hdf5_filepath_details = pathHelpers.PathComponents(new_hdf5_filepath)
    
    # The name of the data without the its path
    new_hdf5_filepath_details.internalDatasetName = new_hdf5_filepath_details.internalDatasetName.strip("/")
    
    with h5py.File(new_hdf5_filepath_details.externalPath, "a") as new_file:
        # Must contain the internal path in question
        if new_hdf5_filepath_details.internalPath not in new_file:
            raise Exception("The given data file \"" + new_filename + "\" does not contain \"" + new_hdf5_filepath_details.internalPath + "\".")
        
        # Must be a path to a h5py.Dataset not a h5py.Group (would be nice to relax this constraint)
        elif not isinstance(new_file[new_hdf5_filepath_details.internalPath], h5py.Dataset):
            raise Exception("The given data file \"" + new_filename + "\" does not not contain a dataset for \"" + new_hdf5_filepath_details.internalPath + "\".")
        
        # Where to read data files from
        input_directory = new_hdf5_filepath_details.internalDirectory.rstrip("/")
        
        # Where the results will be saved to
        output_directory = ""
        
        if input_directory == "":
            # if we are at the root
            output_directory = "/ADINA_results" + "/" + new_hdf5_filepath_details.internalDatasetName.rstrip("/")
        else:
            # otherwise (not at that the root)
            output_directory = input_directory + "_ADINA_results" + "/" + new_hdf5_filepath_details.internalDatasetName.rstrip("/")
        
        # Delete the old output directory if it exists.
        if output_directory in new_file:
            del new_file[output_directory]
        
        # Create a new output directory.
        new_file.create_group(output_directory)
        
        # Create a hardlink (does not copy) the original data
        new_file[output_directory]["original_data"] = new_file[new_hdf5_filepath_details.internalPath]
        
        # Copy out images for manipulation in memory
        new_data = new_file[output_directory]["original_data"][:]
        
        # Get a debug logger for the HDF5 file (if needed)
        array_debug_logger = HDF5_logger.generate_HDF5_array_debug_logger(new_file[output_directory], debug = debug, overwrite_group = True)
        
        # Generate the new neurons
        new_neurons = advanced_image_processing.generate_neurons(new_data, array_debug_logger = array_debug_logger, **parameters)
        
        # Save them
        if new_neurons.size:
            HDF5_serializers.write_numpy_structured_array_to_HDF5(new_file[output_directory], "neurons", new_neurons, True)
        else:
            logger.warning("No neurons were found in the data.")
        
        # Write the configuration parameters in the attributes as a string.
        new_file[output_directory].attrs["parameters"] = repr(parameters)
        

@advanced_debugging.log_call(logger)
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

    # Creates command line parser
    parser = argparse.ArgumentParser(description = "Parses input from the command line for a batch job.")

    # Takes a config file and then a series of one or more HDF5 files.
    parser.add_argument("config_filename", metavar="CONFIG_FILE", type = str, help = "JSON file that provides configuration options for how to use dictionary learning on the input files.")
    parser.add_argument("input_files", metavar="INPUT_FILE", type = str, nargs='+', help = "HDF5 file(s) to process (a single dataset or video will be expected in /images (time must be the first dimension) the results will be placed in /results (will overwrite old data) of the respective file with attribute tags related to the parameters used).")

    # Results of parsing arguments (ignore the first one as it is the command line call).
    parsed_args = parser.parse_args(argv[1:])

    # Go ahead and stuff in parameters with the other parsed_args
    # A little risky if parsed_args may later contain a parameters variable due to changing the main file
    # or argparse changing behavior; however, this keeps all arguments in the same place.
    parsed_args.parameters = read_config.read_parameters(parsed_args.config_filename)

    # Runs the dictionary learning algorithm on each file with the given parameters and saves the results in the given files.
    batch_generate_save_dictionary(*parsed_args.input_files, **parsed_args.parameters)

    return(0)



if __name__ == "__main__":
    # only necessary if running main (normally if calling command line). no point in importing otherwise.
    import sys
    
    # call main if the script is loaded from command line. otherwise, user can import package without main being called.
    sys.exit(main(*sys.argv))