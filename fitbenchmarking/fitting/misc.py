"""
General utility functions for calculating some attributes of the fit.
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

import numpy as np
import mantid
from utils import test_result


def compute_chisq(differences):
    """
    Simple function that calculates the sum of the differences squared
    between the data and the fit.

    @param differences :: differences between the actual data and the
                          fit points.

    @returns :: the sum of the square of each element in differences
    """
    chi_sq = np.sum(np.square(differences))

    return chi_sq


def create_result_entry(problem, status, chi_sq, runtime, minimizer,
                        ini_function_def, fin_function_def):
    """
    Helper function that creates a result object after fitting a problem
    with a certain function and minimzier.

    @param problem :: problem object containing info that was fitted
    @param status :: status of the fit, i.e. success or failure
    @param chi_sq :: the chi squared of the fit
    @param runtime :: the runtime of the fit
    @param minimizer :: the minimizer used for this particular fit
    @param ini_function_def :: the initial function definition for the fit
    @param fin_function_def :: the final function definition for the fit

    @returns :: the result object
    """

    # Create empty fitting result object
    result = test_result.FittingTestResult()

    # Populate result object
    result.problem = problem
    result.fit_status = status
    result.chi_sq = chi_sq
    result.runtime = runtime
    result.minimizer = minimizer
    result.ini_function_def = ini_function_def
    result.fin_function_def = fin_function_def

    return result


def prepare_algorithm_prerequisites(algorithm, problem, use_errors):
    """
    Prepare the required data structures and function definitions for each
    algorithm.

    @param algorithm :: algorithm used in fitting the problem, can be
                        e.g. mantid, numpy etc.
    @param problem :: a problem object containing information used in fitting
    @param use_errors :: wether or not to use errors

    @returns :: prerequisites, depending on the algorithm.
    """

    if algorithm == 'mantid':
        wks_mtd, cost_function = mantid.wks_cost_function(problem, use_errors)
        function_definitions = mantid.function_definitions(problem)
        return wks_mtd, cost_function, function_definitions
    else:
        raise NameError("Sorry, the specified algorithm is not supported yet.")