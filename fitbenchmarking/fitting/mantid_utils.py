"""
Utility functions used in the mantid fitting process.
"""
# Copyright &copy; 2016 ISIS Rutherford Appleton Laboratory, NScD
# Oak Ridge National Laboratory & European Spallation Source
#
# This file is part of Mantid.
# Mantid is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# Mantid is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# File change history is stored at:
# <https://github.com/mantidproject/fitbenchmarking>.
# Code Documentation is available at: <http://doxygen.mantidproject.org>

from __future__ import (absolute_import, division, print_function)

import numpy as np
import mantid.simpleapi as msapi
from fitting.plotting import plot_helper


def parse_result(fit_result, t_start, t_end):
    """
    Function that takes the raw result from the mantid fitting algorithm
    and refines it.

    @param fit_result :: result object from the mantid fitting algorithm
    @param t_start :: time the fitting started
    @param t_end :: time the fitting completed

    @returns :: the processed status (str), fit workspace (mantid wks),
                parameters, errors on them [arrays] and runtime (float).
    """

    status = 'failed'
    fit_wks, params, errors, runtime = None, None, None, np.nan
    if not fit_result is None:
        status = fit_result.OutputStatus
        fit_wks = fit_result.OutputWorkspace
        params = fit_result.OutputParameters.column(1)[:-1]
        errors = fit_result.OutputParameters.column(2)[:-1]
        runtime = t_end - t_start

    return status, fit_wks, params, errors, runtime


def optimum(fit_wks, minimizer_name, best_fit):
    """
    Function that stores the best fit of the given data into
    a object ready for plotting.

    @param fit_wks :: mantid workspace holding the fit data
    @param minimizer_name :: name of the minimizer used in fitting
    @param best_fit :: the previous best_fit object

    @returns :: the new best_fit object
    """

    tmp = msapi.ConvertToPointData(fit_wks)
    best_fit = plot_helper.data(minimizer_name, tmp.readX(1), tmp.readY(1))

    return  best_fit


def wks_cost_function(prob, use_errors=True):
    """
    Helper function that prepares the data workspace used by mantid
    for fitting.

    @param prob :: object holding the problem information
    @param use_errors :: whether to use errors or not

    @returns :: the fitting data in workspace format and the
                cost function used in fitting
    """

    if use_errors:
        data_e = setup_errors(prob)
        wks = msapi.CreateWorkspace(DataX=prob.data_x, DataY=prob.data_y,
                                    DataE=data_e)
        cost_function = 'Least squares'
    else:
        wks = msapi.CreateWorkspace(DataX=prob.data_x, DataY=prob.data_y)
        cost_function = 'Unweighted least squares'

    return wks, cost_function


def function_definitions(prob):
    """
    Transforms the prob.equation field into a function that can be
    understood by the mantid fitting algorithm.

    @param prob :: object holding the problem infomation

    @returns :: a function definitions string with functions that
                mantid understands
    """

    if prob.starting_values:
        # NIST data requires prior formatting
        nb_start_vals = len(prob.starting_values[0][1])
        function_defs = parse_nist_function_definitions(prob, nb_start_vals)
    else:
        # Neutron data does not require any
        function_defs = []
        function_defs.append(prob.equation)

    return function_defs


def ignore_invalid(prob, cost_function):
    """
    Helper function that sets the whether the mantid fitting algorithm
    ignores invalid data or not. This depends on the cost function.

    @param prob :: object holding the problem information
    @param const_function :: cost function used in fitting

    @returns :: boolean depending on whether to ignore invalid data or not
    """

    ignore_invalid = cost_function == 'Least squares'
    if 'WISH17701' in prob.name:
        ignore_invalid = False

    return ignore_invalid


def parse_nist_function_definitions(prob, nb_start_vals):
    """
    Helper function that parses the NIST function definitions and
    transforms them into a mantid-redeable format.

    @param prob :: object holding the problem information
    @param nb_start_vals :: the number of starting points for a given
                            function definition

    @returns :: the formatted function definition (str)
    """

    function_defs = []
    for start_idx in range(0, nb_start_vals):
        start_val_str = ''
        for param in prob.starting_values:
            start_val_str += ('{0}={1},'.format(param[0], param[1][start_idx]))

        function_defs.append("name=UserFunction, Formula={0}, {1}".
                             format(prob.equation, start_val_str))

    return function_defs


def setup_errors(prob):
    """
    Gets errors on the data points from the problem object if there are
    any. If not, the errors are approximated by taking the square root
    of the absolute y-value, since we cannot know how the data was
    obtained and this is a reasonable approximation.

    @param prob :: object holding the problem information

    @returns :: array of errors of particular problem
    """

    data_e = None
    if prob.data_pattern_obs_errors is None:
        data_e = np.sqrt(abs(prob.data_y))
    else:
        data_e = prob.data_pattern_obs_errors

    return data_e
