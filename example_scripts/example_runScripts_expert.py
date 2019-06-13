"""
Script that runs the fitbenchmarking tool with various problems and minimizers
for an expert user. This script will show exactly what fitbenchmarking is doing
at each stage to enable a user to customize their problem to their needs.
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
# File change history is stored at: <https://github.com/mantidproject/mantid>.
# Code Documentation is available at: <http://doxygen.mantidproject.org>


from __future__ import (absolute_import, division, print_function)
import os
import sys


# Avoid reaching the maximum recursion depth by setting recursion limit
# This is useful when running multiple data set benchmarking
# Otherwise recursion limit is reached and the interpreter throws an error
sys.setrecursionlimit(10000)

# Insert path to where the scripts are located, relative to
# the example_scripts folder
current_path = os.path.dirname(os.path.realpath(__file__))
fitbenchmarking_folder = os.path.abspath(os.path.join(current_path, os.pardir))
scripts_folder = os.path.join(fitbenchmarking_folder, 'fitbenchmarking')
sys.path.insert(0, scripts_folder)

from fitting_benchmarking import do_benchmarking
from utils import misc
from utils import create_dirs
from results_output import save_tables, generate_tables, \
    create_acc_tbl, create_runtime_tbl
from resproc import visual_pages

# SPECIFY THE SOFTWARE/PACKAGE CONTAINING THE MINIMIZERS YOU WANT TO BENCHMARK
# software = ['mantid', 'scipy', 'mantid']
software = ['mantid', 'scipy']
software_options = {'software': software}

# User defined minimizers
# custom_minimizers = {"mantid": ["BFGS",
#                                 "Damped GaussNewton"],
#                      "scipy": ["lm", "trf"]}
custom_minimizers = None

# SPECIFY THE MINIMIZERS YOU WANT TO BENCHMARK, AND AS A MINIMUM FOR THE SOFTWARE YOU SPECIFIED ABOVE
if len(sys.argv) > 1:
    # Read custom minimizer options from file
    software_options['minimizer_options'] = current_path + sys.argv[1]
elif custom_minimizers:
    # Custom minimizer options:
    software_options['minimizer_options'] = custom_minimizers
else:
    # Using default minimizers from
    # fitbenchmarking/fitbenchmarking/minimizers_list_default.json
    software_options['minimizer_options'] = None

# Benchmark problem directories
benchmark_probs_dir = os.path.join(fitbenchmarking_folder,
                                   'benchmark_problems')

"""
Modify results_dir to specify where the results of the fit should be saved
If left as None, they will be saved in a "results" folder in the working dir
If the full path is not given results_dir is created relative to the working dir
"""
results_dir = None

# Whether to use errors in the fitting process
use_errors = True

# Parameters of how the final tables are colored
# e.g. lower that 1.1 -> light yellow, higher than 3 -> dark red
# Change these values to suit your needs
color_scale = [(1.1, 'ranking-top-1'),
               (1.33, 'ranking-top-2'),
               (1.75, 'ranking-med-3'),
               (3, 'ranking-low-4'),
               (float('nan'), 'ranking-low-5')]


# ADD WHICH PROBLEM SETS TO TEST AGAINST HERE
# Do this, in this example file, by selecting sub-folders in benchmark_probs_dir
# "Muon_data" works for mantid minimizers
# problem_sets = ["Neutron_data", "NIST/average_difficulty"]
problem_sets = ["NIST/average_difficulty"]
for sub_dir in problem_sets:
    # generate group group_name/name used for problem set
    group_name = sub_dir.replace('/', '_')

    # Problem data directory
    data_dir = os.path.join(benchmark_probs_dir, sub_dir)

    print('\nRunning the benchmarking on the {} problem set\n'.format(group_name))

    # Processes software_options dictionary into Fitbenchmarking format
    minimizers, software = misc.get_minimizers(software_options)

    # Sets up the problem groups specified by the user by providing
    # a respective data directory.
    problem_groups = misc.setup_fitting_problems(data_dir, group_name)

    results_dir = create_dirs.results(results_dir)
    group_results_dir = create_dirs.group_results(results_dir, group_name)

    # All parameters inputted by the user are stored in an object
    user_input = misc.save_user_input(software, minimizers, group_name,
                                      group_results_dir, use_errors)

    # Loops through group of problems and benchmark them
    prob_results = do_benchmarking(user_input, problem_groups, group_name)

    print('\nProducing output for the {} problem set\n'.format(group_name))
    for idx, group_results in enumerate(prob_results):
        # Creates the results directory where the tables are located
        tables_dir = create_dirs.restables_dir(results_dir, group_name)

        if isinstance(software, list):
            minimizers = sum(minimizers, [])

        # Creates the problem names with links to the visual display pages
        # in rst
        linked_problems = visual_pages.create_linked_probs(group_results,
                                                           group_name, results_dir)

        # Generates accuracy and runtime normalised tables and summary tables
        norm_acc_rankings, norm_runtimes, sum_cells_acc, sum_cells_runtime = generate_tables(group_results, minimizers)

        # Creates an accuracy table
        acc_tbl = create_acc_tbl(minimizers, linked_problems, norm_acc_rankings, use_errors, color_scale)

        # Creates an runtime table
        runtime_tbl = create_runtime_tbl(minimizers, linked_problems, norm_runtimes, use_errors, color_scale)

        # Saves accuracy minimizer results
        save_tables(tables_dir, acc_tbl, use_errors, group_name, 'acc')

        # Saves runtime minimizer results
        save_tables(tables_dir, runtime_tbl, use_errors, group_name, 'runtime')

    print('\nCompleted benchmarking for {} problem set\n'.format(sub_dir))