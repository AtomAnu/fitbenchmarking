"""
Script that runs the fitbenchmarking tool with various problems and minimizers.
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
import glob
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

from fitting_benchmarking import do_fitting_benchmark as fitBenchmarking
from results_output import save_results_tables as printTables


# SOFTWARE YOU WANT TO BENCHMARK
software = 'scipy'

# Benchmark problem directories
benchmark_probs_dir = os.path.join(fitbenchmarking_folder, 'benchmark_problems')

"""
Modify results_dir to specify where the results of the fit should be saved
If left as None, they will be saved in a "results" folder in the working dir
When specifying a results_dir, please GIVE THE FULL PATH
If the full path is not given and the results_dir name is valid
../fitbenchmarking/fitbenchmarking/ is taken as the path
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
# CURRENTLY TESTING AGAINST "neutron", "nist"
# problem_sets = ["neutron", "nist"]
problem_sets = [
    'NIST_average_diff',
    'NIST_low_diff',
    'Neutron_data',
    'NIST_high_diff']
for group_label in problem_sets:
    results_dir = None
    print('\nRunning the benchmarking on {} problem set\n'.format(group_label))

    # Problem data directories
    data_dir = os.path.join(benchmark_probs_dir, group_label)
    # Running the benchmarking
    results_per_group, results_dir = \
        fitBenchmarking(group_name=group_label, software=software,
                        data_dir=data_dir,
                        use_errors=use_errors, results_dir=results_dir)
# else:
#     raise RuntimeError("Invalid run_data, please check if the array"
#                        "contains the correct names!")

    print('\nProducing output {} problem set\n'.format(group_label))
    for idx, group_results in enumerate(results_per_group):
        # Display the runtime and accuracy results in a table
        printTables(software, group_results,
                    group_name=group_label, use_errors=use_errors,
                    color_scale=color_scale, results_dir=results_dir)

    print('\nCompleted benchmarking for {} problem set\n'.format(group_label))
