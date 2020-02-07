"""
This file calls the pycutest interface for SIF data
"""

from __future__ import print_function

import os
from collections import OrderedDict

import numpy as np
import pycutest

from fitbenchmarking.parsing.base_parser import Parser
from fitbenchmarking.parsing.fitting_problem import FittingProblem
from fitbenchmarking.utils.create_dirs import del_contents_of_dir
from fitbenchmarking.utils.exceptions import ParsingError
from fitbenchmarking.utils.logging_setup import logger

try:
    from tempfile import TemporaryDirectory
except ImportError:
    from backports.tempfile import TemporaryDirectory


# Empty the cache
del_contents_of_dir(os.environ["PYCUTEST_CACHE"])


class CutestParser(Parser):
    """
    Use the pycutest interface to parse SIF files

    This parser has some quirks.
    Due to the complex nature of SIF files, we utilise pycutest to generate the
    function. This function returns the residual `r(f,x,y,e) := (f(x) - y)/e` for some parameters x.
    For consistency we require the value to be `f(x, p)`.

    To avoid having to convert back from the residual in the evaluation, we store
    the data separately and set y to 0.0, and e to 1.0 for all datapoints.
    
    We then accomodate for the missing x argument by caching x against an
    associated function `f_x(p)`.

    As such the function is defined by: `f(x, p) := r(f_x,p,0,1)`

    If a new x is passed, we write a new file and parse it to generate a
    function. We define x to be new if ``not np.isclose(x, cached_x)`` for each
    ``cached_x`` that has already been stored.
    """

    def parse(self):
        """
        Get data into a Fitting Problem via cutest.

        :return: The fully parsed fitting problem
        :rtype: fitbenchmarking.parsing.fitting_problem.FittingProblem
        """
        self.mastsif_dir = TemporaryDirectory()

        # set the MASTSIF environment variable so that pycutest
        # can find the sif files
        os.environ["MASTSIF"] = self.mastsif_dir.name

        self._num_params = None

        # get just the short filename (minus the .SIF)
        fp = FittingProblem()

        # Collect x and create new file with blank y
        fname, fp.data_x, fp.data_y, fp.data_e = self._setup_data()

        self._p = self._import_problem(fname)

        fp.name = self._p.name

        fp.function = self._function  # self._p.objcons
        fp.equation = None
        fp.starting_values = self._get_starting_values()
        fp.start_x = None
        fp.end_x = None

        # Create a list of x and f.
        # If a new x is given we will create and parse a new file
        self._cache = [(fp.data_x, self._p.objcons)]

        return fp

    def _import_problem(self, file_name):
        """
        Import the problem using cutest

        :param file_name: The path to the file
        :type file_name: str
        :return: The parsed problem
        :rtype: pycutest.CUTEstProblem
        """

        problem_ext = os.path.basename(file_name)
        problem, _ = os.path.splitext(problem_ext)

        return pycutest.import_problem(problem)

    def _function(self, x, *params):
        """
        If these x values have been passed in before, then run the function
        Otherwise, create a new problem file, parse and cache the function

        :param x: The data to evaluate at
        :type x: np.array
        :return: The result of evaluating at the given x
        :rtype: np.array
        """
        os.environ["MASTSIF"] = self.mastsif_dir.name

        for cx, cf in self._cache:
            if np.isclose(cx, x).all():
                f = cf
                break
        else:
            fname, _, _, _ = self._setup_data(x)
            p = self._import_problem(fname)
            f = p.objcons
            self._cache.append((x, f))
        _, fx = f(np.asarray(params))

        return fx

    def _get_starting_values(self):

        starting_values = [
            OrderedDict([
                ('f{}'.format(i), self._p.x0[i])
                for i in range(self._num_params)
            ])
        ]

        return starting_values

    def _setup_data(self, x=None):
        """
        Reads datapoints from CUTEst SIF files and rewrites values where needed.
        
        With x=None, read all data from file into x_data, y_data, and e_data,
        then create a new file with y values of 0.0, and e values of 1.0.

        If x is given, create a file with the given x data, 0.0 y values, and
        1.0 e values, and return the path to the file.

        y and e are set here to avoid the function returning residuals that we
        then have to convert every time the function is evaluated.

        :param x: X values to save (used for evaluating at new points)
        :type x: np.array
        :returns: path to new sif file, data_x, data_y, data_e
        :rtype: str, numpy.ndarray, numpy.ndarray, numpy.ndarray
        """

        if self.file.closed:
            with open(self._filename, 'r') as f:
                lines = f.readlines()
        else:
            lines = self.file.readlines()

        if x is not None and len(x.shape) == 0:
            x = np.array([x])

        x_idx, y_idx, e_idx = 0, 0, 0
        data_x, data_y, data_e = None, None, None

        # SIF requires columns of 25 chars, so line[:col_width-1] will be 1
        # column of data
        col_width = 25

        written_x = False

        to_write = []

        for line in lines:

            if "IE M " in line:
                if x is None:
                    data_count = int(line.split()[2])
                    # this will always come before x/y data
                    # so allocate space for these now
                    data_x = np.zeros(data_count)
                    data_y = np.zeros(data_count)
                    data_e = np.zeros(data_count)
                    # initialize index parameters for x and y
                else:
                    line = line[:col_width-1] + str(len(x))
                    data_count = len(x)

            elif "IE MLOWER" in line and x is not None:
                line = line[:col_width-1] + '1\n'

            elif "IE MUPPER" in line and x is not None:
                line = line[:col_width-1] + str(len(x))

            elif "IE N " in line:
                self._num_params = int(line.split()[2])

            elif "RE X" in line:
                if x is None:
                    data_x[x_idx] = float(line.split()[2])
                    x_idx += 1
                else:
                    if written_x:
                        continue

                    line = ''
                    new_lines = []
                    for i, val in enumerate(x):
                        idx = i+1
                        tmp_line_x = ' RE X{}'.format(idx)
                        spacing = ' '*(col_width - (5 + len(str(idx))))
                        tmp_line_x += spacing + str(val)
                        tmp_line_y = ' RE Y{}{}0.0'.format(idx, spacing)
                        tmp_line_e = ' RE E{}{}1.0'.format(idx, spacing)
                        new_lines.extend([tmp_line_x,
                                          tmp_line_y,
                                          tmp_line_e])
                    x_idx = y_idx = e_idx = len(new_lines) / 3
                    line = '\n'.join(new_lines)
                    written_x = True

            elif "RE Y" in line:
                if x is None:
                    data_y[y_idx] = float(line.split()[2])
                    y_idx += 1
                    line = line[:col_width-1] + '0.0'
                else:
                    continue

            elif 'RE E' in line:
                if x is None:
                    data_e[e_idx] = float(line.split()[2])
                    e_idx += 1
                    line = line[:col_width-1] + '1.0'
                else:
                    continue

            to_write.append(line + '\n')

        if x is None:
            x = data_x

        file_path = os.path.join(self.mastsif_dir.name,
                                 '{}.SIF'.format(str(id(x))[-10:]))

        with open(file_path, 'w') as f:
            f.writelines(to_write)

        # check the data is right
        if x_idx != data_count:
            raise ParsingError('Wrong number of x data points. Got {}, '
                               'expected {}'.format(x_idx, data_count))
        if y_idx != data_count:
            raise ParsingError('Wrong number of y data points. Got {}, '
                               'expected {}'.format(y_idx, data_count))
        if e_idx == 0:
            data_e = None
        elif e_idx != data_count:
            raise ParsingError('Wrong number of e data points. Got {}, '
                               'expected {}'.format(e_idx, data_count))

        return file_path, data_x, data_y, data_e
