'''
This file will handle all interaction with the options configuration file.
'''

import configparser

import os


class Options(object):
    """
    An options class to store and handle all options for fitbenchmarking
    """

    DEFAULTS = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                            'default_options.ini'))

    def __init__(self, file_name=None):
        """
        Initialise the options from a file if file is given.
        Priority is values in the file, failing that, values are taken from
        DEFAULTS (stored in ./default_options.ini)

        :param file_name: The options file to load
        :type file_name: str
        """
        self._results_dir = ''
        config = configparser.ConfigParser(converters={'list': read_list,
                                                       'str': str})

        config.read(self.DEFAULTS)
        if file_name is not None:
            config.read(file_name)

        minimizers = config['MINIMIZERS']
        self.minimizers = {}
        for key in minimizers.keys():
            self.minimizers[key] = minimizers.getlist(key)

        fitting = config['FITTING']
        self.num_runs = fitting.getint('num_runs')
        self.software = fitting.getlist('software')
        self.use_errors = fitting.getboolean('use_errors')

        plotting = config['PLOTTING']
        self.make_plots = plotting.getboolean('make_plots')
        self.colour_scale = plotting.getlist('colour_scale')
        self.colour_scale = [(float(cs.split(',', 1)[0].strip()),
                              cs.split(',', 1)[1].strip())
                             for cs in self.colour_scale]
        self.comparison_mode = plotting.getstr('comparison_mode')
        self.table_type = plotting.getlist('table_type')
        self.results_dir = plotting.getstr('results_dir')

    @property
    def results_dir(self):
        return self._results_dir

    @results_dir.setter
    def results_dir(self, value):
        self._results_dir = os.path.abspath(value)


def read_list(s):
    return str(s).split('\n')
