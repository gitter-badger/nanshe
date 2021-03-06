"""
The ``neuron_matplotlib_viewer`` module provides a ``matplotlib``-based viewer.

===============================================================================
Overview
===============================================================================
The module ``neuron_matplotlib_viewer`` provides a simple |matplotlib|_ viewer
for navigating through a 3D imagestack (TYX). However the first dimension could
be Z, as well. This has been deprecated in favor of the ``viewer``.

.. |matplotlib| replace:: ``matplotlib``
.. _matplotlib: http://matplotlib.org

===============================================================================
API
===============================================================================
"""


__author__ = "John Kirkham <kirkhamj@janelia.hhmi.org>"
__date__ = "$Apr 03, 2014 20:20:39 EDT$"


import warnings

warnings.warn(
    "The module `neuron_matplotlib_viewer` is deprecated."
    "Please consider using `viewer` instead.",
    DeprecationWarning
)

# Need in order to have logging information no matter what.
from nanshe.util import prof


# Get the logger
trace_logger = prof.getTraceLogger(__name__)
logger = prof.logging.getLogger(__name__)

import matplotlib as mpl
import matplotlib.figure

from matplotlib.widgets import Slider, Button


@prof.log_class(trace_logger)
class NeuronMatplotlibViewer(matplotlib.figure.Figure):
    """
        Provides a way to interact with numpy arrays pulled from neuron images.

        Wraps a Matplotlib figure instance.
    """

    def __init__(self, *args, **kwargs):
        """
            Initializes a NeuronMatplotlibViewer using the given figure to
            clone and image stack to view.

            After cloning, self will be the same as fig. Additional features
            will be attached to self.

            Args:
                args(list):         arguments to be passed to parent

            Keyword Args:
                kwargs(dict):       arguments to be passed to parent
        """

        super(NeuronMatplotlibViewer, self).__init__(*args, **kwargs)
        super(NeuronMatplotlibViewer, self).__init__(
            *args, **dict([(_k, _v) for (_k, _v) in kwargs.items() if _k is not "neuron_images"])
        )

        self.subplots_adjust(left=0.25, bottom=0.25)
        self.viewer = self.add_axes([0.25, 0.25, 0.7, 0.7])

        #self.set_images(kwargs["neuron_images"])

    def set_images(self,
                   new_neuron_images,
                   cmap=mpl.cm.RdBu,
                   use_matshow=False):
        """
            Sets the images to be viewed.

            Args:
                new_neuron_images(numpy.ndarray):     array of images (first
                                                      index is which image)
        """
        if (new_neuron_images.ndim > 3):
            raise ValueError(
                "Dimensions cannot be greater than 3. " +
                "Was provided new_neuron_images with \"" +
                str(new_neuron_images.ndim) + "\" dimensions."
            )

        self.neuron_images = new_neuron_images
        self.cmap = cmap

        viewer_show_method = None
        if use_matshow:
            viewer_show_method = self.viewer.matshow
        else:
            viewer_show_method = self.viewer.imshow

        if (self.neuron_images.ndim == 3):
            #self.image_view = self.viewer.imshow(self.neuron_images[0], cmap = self.cmap, vmin = self.neuron_images.min(), vmax = self.neuron_images.max())
            self.image_view = viewer_show_method(
                self.neuron_images[0],
                cmap=self.cmap,
                vmin=self.neuron_images.min(),
                vmax=self.neuron_images.max()
            )
        else:
            #self.image_view = self.viewer.imshow(self.neuron_images, cmap = self.cmap, vmin = self.neuron_images.min(), vmax = self.neuron_images.max())
            self.image_view = viewer_show_method(
                self.neuron_images,
                cmap=self.cmap,
                vmin=self.neuron_images.min(),
                vmax=self.neuron_images.max()
            )

        self.image_view_colorbar = self.colorbar(
            self.image_view, ax=self.viewer)

        if (self.neuron_images.ndim == 3):
            self.time_nav = TimeNavigator(self, len(self.neuron_images) - 1)

            self.time_nav_cid = self.time_nav.on_time_update(self.time_update)

    def time_update(self):
        """
            Method to be called by the TimeNavigator when the time changes.
            Updates image displayed.
        """
        if (self.neuron_images.ndim == 3):
            self.image_view.set_array(
                self.neuron_images[self.time_nav.stime.val])
            self.canvas.draw_idle()


@prof.log_class(trace_logger)
class TimeNavigator(object):
    def __init__(self, fig, max_time, min_time=0, time_step=1, axcolor='lightgoldenrodyellow',
                 hovercolor='0.975'):
        """
            Initializes a TimeNavigator using the given figure and a fixed
            number of steps.

            Provides a simple slider bar and buttons to navigate through time.

            Args:
                fig         should be a figure that has been initialized.
                max_time    maximum step for images.
                min_time    minimum step for images.
                time_step   how much to increase/decrease by for each step.
                axcolor     color to be used for all buttons and slider bar.
                hovercolor  color turned when mouse over occurs for any button.
        """

        self.min_time = min_time
        self.max_time = max_time
        self.time_step = time_step
        self.axcolor = axcolor
        self.hovercolor = hovercolor

        self.next_cid = 0

        self.axtime = fig.add_axes(
            [0.25, 0.1, 0.65, 0.03], axisbg=self.axcolor)
        self.stime = Slider(
            self.axtime,
            'Time',
            self.min_time,
            self.max_time,
            valinit=self.min_time,
            valfmt='%i'
        )

        self.stime.on_changed(self.time_update)

        self.beginax = fig.add_axes([0.2, 0.025, 0.1, 0.04])
        self.begin_button = Button(
            self.beginax,
            'Begin',
            color=self.axcolor,
            hovercolor=self.hovercolor
        )
        self.begin_button.on_clicked(self.begin_time)

        self.prevax = fig.add_axes([0.3, 0.025, 0.1, 0.04])
        self.prev_button = Button(
            self.prevax, 'Prev', color=self.axcolor, hovercolor=self.hovercolor
        )
        self.prev_button.on_clicked(self.prev_time)

        self.nextax = fig.add_axes([0.7, 0.025, 0.1, 0.04])
        self.next_button = Button(
            self.nextax, 'Next', color=self.axcolor, hovercolor=self.hovercolor
        )
        self.next_button.on_clicked(self.next_time)

        self.endax = fig.add_axes([0.8, 0.025, 0.1, 0.04])
        self.end_button = Button(
            self.endax, 'End', color=self.axcolor, hovercolor=self.hovercolor
        )
        self.end_button.on_clicked(self.end_time)

        self.callbacks = {}

    def begin_time(self, event):
        """
            Sets time to min_time.

            Args:
                event   Matplotlib event that caused the call to this callback.
        """

        logger.debug(
            "Value of slider before setting to the beginning is \"" +
            str(self.stime.val) + "\"."
        )

        self.time_update(self.min_time)

        logger.debug(
            "Value of slider after setting to the beginning is \"" +
            str(self.stime.val) + "\"."
        )
        assert (self.min_time == self.stime.val)

    def prev_time(self, event):
        """
            Sets time to one time_step prior.

            Args:
                event   Matplotlib event that caused the call to this callback.
        """

        logger.debug(
            "Value of slider before going to the previous time is \"" +
            str(self.stime.val) + "\"."
        )

        self.time_update(self.stime.val - self.time_step)

        logger.debug(
            "Value of slider after going to the previous time is \"" +
            str(self.stime.val) + "\"."
        )

    def next_time(self, event):
        """
            Sets time to one time_step after.

            Args:
                event   Matplotlib event that caused the call to this callback.
        """

        logger.debug(
            "Value of slider before going to the next time is \"" +
            str(self.stime.val) + "\"."
        )

        self.time_update(self.stime.val + self.time_step)

        logger.debug(
            "Value of slider after going to the next time is \"" +
            str(self.stime.val) + "\"."
        )

    def end_time(self, event):
        """
            Sets time to max_time.

            Args:
                event   Matplotlib event that caused the call to this callback.
        """

        self.time_update(self.max_time)

        assert (self.max_time == self.stime.val)

    def normalize_val(self, val):
        """
            Takes the time value and normalizes it to fit within the range.
            Then, makes sure it is a discrete number of steps from the
            min_time.

            Args:
                val     float position from the slider bar to correct

            Returns:
                int:    the normalized value.
        """

        if val < self.min_time:
            return(self.min_time)
        elif val > self.max_time:
            return(self.max_time)
        else:
            return(int(round((val - self.min_time) / self.time_step)))

    def time_update(self, val):
        """
            Takes the time value and normalizes it within the range if it does
            not fit.

            Args:
                val     float position from slider bar to move to
        """

        val = self.normalize_val(val)

        if val != self.stime.val:
            self.stime.set_val(val)

            for each_cid, each_callback in self.callbacks.items():
                logger.debug(
                    "Before calling the caller id for time_update with value \"" +
                    str(each_cid) + "\"."
                )

                each_callback()

                logger.debug(
                    "After calling the caller id for time_update with value \"" +
                    str(each_cid) + "\"."
                )

    def disconnect(self, cid):
        """
            Disconnects the given cid from being notified of time updates.

            Args:
                cid     ID of callback to pull
        """

        logger.debug(
            "Before disconnecting the caller id for time_update with value \"" +
            str(cid) + "\"."
        )
        logger.debug(
            "Contents of the callback dictionary before disconnecting \"" +
            str(self.callbacks) + "\"."
        )

        del self.callbacks[cid]

        logger.debug(
            "After disconnecting the caller id for time_update with value \"" +
            str(cid) + "\"."
        )
        logger.debug(
            "Contents of the callback dictionary after disconnecting\"" +
            str(self.callbacks) + "\"."
        )

    def on_time_update(self, func):
        """
            Registers a callback function for notification when the time is
            updated.

            Args:
                func(callable):     function call when the time is updated

            Returns:
                int:                a callback ID or cid to allow pulling the
                                    callback when no longer necessary.
        """

        logger.debug(
            "Before connecting the caller id for time_update with value \"" +
            str(self.next_cid) + "\"."
        )
        logger.debug(
            "Contents of the callback dictionary before connecting \"" +
            str(self.callbacks) + "\"."
        )

        cid = self.next_cid
        self.next_cid += 1

        self.callbacks[cid] = func

        logger.debug(
            "After connecting the caller id for time_update with value \"" +
            str(cid) + "\"."
        )
        logger.debug(
            "Contents of the callback dictionary after connecting \"" +
            str(self.callbacks) + "\"."
        )

        return(cid)
