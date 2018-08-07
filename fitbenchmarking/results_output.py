"""
Produce output tables from fitting benchmarking results, in different
formats such as RST and plain text.
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

import os, logging, glob
import numpy as np
import mantid.simpleapi as msapi
from docutils.core import publish_string

import post_processing as postproc
from logging_setup import logger

# Some naming conventions for the output files
BENCHMARK_VERSION_STR = 'v3.8'
FILENAME_SUFFIX_ACCURACY = 'acc'
FILENAME_SUFFIX_RUNTIME = 'runtime'
FILENAME_EXT_TXT = 'txt'
FILENAME_EXT_HTML = 'html'

# Directory of this script (e.g. in source)
SCRIPT_DIR = os.path.dirname(__file__)


def save_results_tables(minimizers, results_per_test, group_name,
                        use_errors, color_scale=None, results_dir=None):
    """
    Prints out results for a group of fit problems in accuracy and runtime
    tables as a text file or html file, in rst format.

    @param minimizers :: list of minimizer names
    @param results_per_test :: result objects
    @param problems_obj :: definitions of the test problems
    @param group_name :: name of this group of problems (example
                         'NIST "lower difficulty"', or 'Neutron data')
    @param use_errors :: whether to use observational errors
    @param simple_text :: whether to print the tables in a simple text format
    @param rst :: whether to print the tables in rst format. They are printed
                  to the standard outputs and to files following specific
                  naming conventions
    @param save_to_file :: If rst=True, whether to save the tables to files
                           following specific naming conventions
    @param color_scale :: threshold-color pairs. This is used for RST tables.
                          The number of levels must be consistent with the
                          style sheet used in the documentation pages
                          (5 at the moment).
    @param results_dir :: directory where all the results are stored
    """

    tables_dir = make_result_tables_directory(results_dir, group_name)
    linked_problems = build_indiv_linked_problems(results_per_test, group_name,
                                                  results_dir)

    accuracy_tbl, runtime_tbl = \
    postproc.calc_accuracy_runtime_tbls(results_per_test, minimizers)
    norm_acc_rankings, norm_runtimes, sum_cells_acc, sum_cells_runtime = \
    postproc.calc_norm_summary_tables(accuracy_tbl, runtime_tbl)

    # Save accuracy table for this group of fit problems
    tbl_acc_indiv = build_rst_table(minimizers, linked_problems,
                                    norm_acc_rankings,
                                    comparison_type='accuracy',
                                    comparison_dim='',
                                    using_errors=use_errors,
                                    color_scale=color_scale)
    save_tables(tables_dir, tbl_acc_indiv, use_errors, group_name,
                FILENAME_SUFFIX_ACCURACY)
    # Save runtime table for this group of fit problems
    tbl_runtime_indiv = build_rst_table(minimizers, linked_problems,
                                        norm_runtimes,
                                        comparison_type='runtime',
                                        comparison_dim='',
                                        using_errors=use_errors,
                                        color_scale=color_scale)

    save_tables(tables_dir, tbl_acc_indiv, use_errors, group_name,
                FILENAME_SUFFIX_RUNTIME)

    logging.shutdown()


def save_tables(tables_dir, table_data, use_errors, group_name, metric):
    """
    Helper function that saves rst tables in all the formats available
    """

    save_table_to_file(results_dir=tables_dir, table_data=table_data,
                       errors=use_errors, group_name=group_name,
                       metric_type=metric,
                       file_extension=FILENAME_EXT_TXT)
    save_table_to_file(results_dir=tables_dir, table_data=table_data,
                       errors=use_errors, group_name=group_name,
                       metric_type=metric,
                       file_extension=FILENAME_EXT_HTML)



def build_indiv_linked_problems(results_per_test, group_name, results_dir):
    """
    Makes a list of linked problem names which would be used for the
    rows of the first column of the tables of individual results.

    @param results_per_test :: results as produces by the fitting tests
    @param group_name :: name of the group (NIST, Neutron data, etc.) this
                         problem is part of

    @returns :: list of problems with their description link tags
    """

    prev_name = ''
    prob_count = 1
    linked_problems = []

    for test_idx, prob_results in enumerate(results_per_test):
        name = results_per_test[test_idx][0].problem.name
        if name == prev_name:
            prob_count += 1
        else:
            prob_count = 1
        prev_name = name
        name_index = name + ' ' + str(prob_count)
        name = '`' + name_index + ' ' + \
               build_visual_display_page(prob_results, group_name, results_dir)
        linked_problems.append(name)

    return linked_problems


def setup_nist_VDpage_misc(linked_name, function_def, results_dir):
    """
    Helper function that sets up the directory, function details table
    and see also link for the NIST data
    """
    support_pages_dir = os.path.join(results_dir, "nist", "tables",
                                     "support_pages")
    details_table = fit_details_rst_table(function_def)
    see_also_link = 'See also:\n ' + linked_name + \
                    '\n on NIST website\n\n'

    return support_pages_dir, details_table, see_also_link


def setup_neutron_VDpage_misc(function_def, results_dir):
    """
    Helper function that sets up the directory, function details table
    and see also link for the NEUTRON data
    """
    support_pages_dir = os.path.join(results_dir, "neutron", "tables",
                                     "support_pages")
    details_table = fit_details_rst_table(function_def)
    see_also_link = ''

    return support_pages_dir, details_table, see_also_link


def setup_VDpage_misc(group_name, problem_name, res_obj, results_dir):
    """
    Setup miscellaneous data for visual display page.
    """
    # Group specific path and other misc stuff
    if 'nist' in group_name:
        support_pages_dir, fit_function_details_table, see_also_link = \
        setup_nist_VDpage_misc(res_obj.problem.linked_name,
                               res_obj.function_def,
                               results_dir)
    elif 'neutron' in group_name:
        support_pages_dir, fit_function_details_table, see_also_link = \
        setup_neutron_VDpage_misc(res_obj.function_def, results_dir)

    file_name = (group_name + '_' + problem_name).lower()
    file_path = os.path.join(support_pages_dir, file_name)

    return (support_pages_dir, file_path, fit_function_details_table,
            see_also_link)


def get_figures_path(support_pages_dir, problem_name):

    figures_dir = os.path.join(support_pages_dir, "figures")
    figure_data = os.path.join(figures_dir, "Data_Plot_" + problem_name +
                               "_1" + ".png")
    figure_fit = os.path.join(figures_dir, "Fit_for_" + problem_name +
                              "_1" + ".png")
    figure_start = os.path.join(figures_dir, "start_for_" + problem_name +
                                "_1" + ".png")

    # If OS is Windows, then need to add prefix 'file:///'
    if os.name == 'nt':
        figure_data = 'file:///' + figure_data
        figure_fit = 'file:///' + figure_fit
        figure_start = 'file:///' + figure_start

    return figure_data, figure_fit, figure_start



def build_visual_display_page(prob_results, group_name, results_dir):
    """
    Builds a page containing details of the best fit for a problem.
    @param prob_results:: the list of results for a problem
    @param group_name :: the name of the group, e.g. "nist_lower"
    """

    # Get the best result for a group
    gb = min((result for result in prob_results),
             key=lambda result: result.fit_chi_sq)

    # Remove commas and replace space with underscore in problem name
    problem_name = gb.problem.name.replace(',', '')
    problem_name = problem_name.replace(' ','_')

    # Set up miscellaneous stuff and generate rst_link
    support_pages_dir, file_path, fit_function_details_table, see_also_link = \
    setup_VDpage_misc(group_name, problem_name, gb, results_dir)

    rst_file_path = file_path.replace('\\', '/')
    rst_link = "<file:///" + '' + rst_file_path + "." + \
                FILENAME_EXT_HTML + ">`__"

    # Get paths to figures
    figure_data, figure_fit, figure_start = \
    get_figures_path(support_pages_dir, problem_name)

    # Create and save rst page
    rst_text = create_rst_page(gb.problem.name, figure_data, figure_start,
                               figure_fit, fit_function_details_table,
                               gb.minimizer, see_also_link)
    save_VDpages(rst_text, problem_name, file_path)

    return rst_link


def generate_rst_title(problem_name):
    """
    Helper function that generates a title for an rst page, containing
    the name of the problem.
    """

    title = '=' * len(problem_name) + '\n'
    title += problem_name + '\n'
    title += '=' * len(problem_name) + '\n\n'

    return title


def generate_rst_data_plot(figure_data):
    """
    Helper function that generates an rst figure of the data plot png image
    contained at path figure_data.
    """

    data_plot = 'Data Plot' + '\n'
    data_plot += ('-' * len(data_plot)) + '\n\n'
    data_plot += '*Plot of the data considered in the problem*\n\n'
    data_plot += ('.. image:: ' + figure_data + '\n' +
                  '   :align: center' + '\n\n')

    return data_plot


def generate_rst_starting_plot(figure_start):
    """
    Helper function that generates an rst figure of the starting guess plot
    png image contained at path figure_start.
    """
    starting_plot = 'Plot of the initial starting guess' + '\n'
    starting_plot += ('-' * len(starting_plot)) + '\n\n'
    starting_plot += ('.. figure:: ' + figure_start  + '\n' +
                      '   :align: center' + '\n\n')

    return starting_plot


def generate_rst_solution_plot(figure_fit, fit_function_details_table,
                               minimizer):
    """
    Helper function that generates an rst figure of the fitted problem
    png image contained at path figure_fit.
    """

    solution_plot = 'Plot of the solution found' + '\n'
    solution_plot += ('-' * len(solution_plot)) + '\n\n'
    solution_plot += '*Minimizer*: ' + minimizer + '\n\n'
    solution_plot += '*Functions*:\n\n'
    solution_plot += fit_function_details_table
    solution_plot += ('.. figure:: ' + figure_fit + '\n' +
                      '   :align: center' + '\n\n')

    return solution_plot


def create_rst_page(name, figure_data, figure_start, figure_fit, details_table,
                    minimizer, see_also_link):
    """
    Creates an rst page containing a title and 3 figures, with a detailed
    table about the fit on the last figure.
    """

    space = "|\n|\n|\n\n"
    title = generate_rst_title(name)
    data_plot = generate_rst_data_plot(figure_data)
    starting_plot = generate_rst_starting_plot(figure_start)
    solution_plot = generate_rst_solution_plot(figure_fit, details_table,
                                               minimizer)

    rst_text = title + space + data_plot + starting_plot + solution_plot + \
               space + see_also_link

    return rst_text


def save_VDpages(rst_text, prob_name, file_path):
    """
    Helper function that saves the rst page into text and html after
    converting it to html.
    """

    html = publish_string(rst_text, writer_name='html')
    with open(file_path + '.' + FILENAME_EXT_TXT, 'w') as visual_rst:
        print(html, file=visual_rst)
        logger.info('Saved {prob_name}.{extension} to {working_directory}'.
                     format(prob_name=prob_name, extension=FILENAME_EXT_TXT,
                            working_directory=file_path))

    with open(file_path + '.' + FILENAME_EXT_HTML, 'w') as visual_html:
        print(html, file=visual_html)
        logger.info('Saved {prob_name}.{extension} to {working_directory}'.
                     format(prob_name=prob_name, extension=FILENAME_EXT_HTML,
                            working_directory=file_path))

def fit_details_rst_table(functions_str):
    """
    Builds an rst table containing the functional form and the parameters
    given the function definition string of the problem.
    """
    functions = functions_str.split(';')
    func_names = []
    func_params = []

    for function in functions:

        # If string contains UserFunction then it means it is a nist problem
        # Otherwise it is a neutron problem
        if 'UserFunction' in function:
            func_names, func_params = parse_nist_function_def(function)

        else:
            func_names, func_params = \
            parse_neutron_function_def(function, func_names, func_params)

    name_header_dim, params_header_dim = \
    fit_details_table_hdims(func_names, func_params)
    header = generate_fit_det_header(name_header_dim, params_header_dim)
    body = generate_fit_det_body(func_names, func_params,
                                 name_header_dim, params_header_dim)
    tbl = header + body + '\n'

    return tbl


def parse_nist_function_def(function):
    """
    Helper function that parses the function definition of a nist problem
    and returns the function name and parameters.
    """
    first_comma = function.find(',')
    second_comma = function.find(',', first_comma + 1)
    function_name = function[first_comma+10:second_comma]
    function_parameters = function[second_comma+2:]
    function_parameters = function_parameters.replace(',', ', ')

    return [function_name], [function_parameters]


def parse_neutron_function_def(function, function_names, function_parameters):
    """
    Helper function that parses the function definition of a neutron problem
    and returns the function name and parameters.
    """
    first_comma = function.find(',')
    if first_comma != -1:
        function_names.append(function[5:first_comma])
        function_parameters.append(function[first_comma+1:])
    else:
        function_names.append(function[5:])
        function_parameters.append('None')

    for idx in range(0, len(function_parameters)):
        function_parameters[idx] = function_parameters[idx].replace(',', ', ')

    return function_names, function_parameters


def fit_details_table_hdims(function_names, function_parameters):
    """
    Helper function that resolves the header dimensions of the fit details
    table present in the rst visual display page.
    """

    name_header_dim = max(len(name) for name in function_names)
    params_header_dim = max(len(parameter) for parameter in function_parameters)

    if name_header_dim < 4:
        name_header_dim = 4
    if params_header_dim < 10:
        params_header_dim = 10

    return name_header_dim, params_header_dim


def generate_fit_det_header(name_dim, params_dim):
    """
    Generates header of table containing the fit details.
    """

    header = ''
    header += '+-' + '-'*name_dim + '-+-' + '-'*params_dim + '-+\n'
    header += ('| ' + 'Form' + ' '*(name_dim-4) + ' ' +
               '| ' + 'Parameters' + ' '*(params_dim-10) + ' |\n')
    header += '+=' + '='*name_dim + '=+=' + '='*params_dim + '=+\n'

    return header


def generate_fit_det_body(func_names, func_params, name_dim, params_dim):
    """
    Generates the body of table containing fit details.
    """

    body = ''
    for idx in range(0, len(func_names)):

        body += ('| ' + func_names[idx] +
                 ' '*(name_dim-len(func_names[idx])) + ' ' +
                 '| ' + func_params[idx] +
                 ' '*(params_dim-len(func_params[idx])) + ' |\n')
        body += '+-' + '-'*name_dim + '-+-' + '-'*params_dim + '-+\n'

    return body


def build_rst_table(columns_txt, rows_txt, cells, comparison_type,
                    comparison_dim, using_errors, color_scale=None):
    """"
    Builds an RST table as a string, given the list of column and row headers,
    and a 2D numpy array with values for the cells.
    This can be tricky/counterintuitive, see:
    http://docutils.sourceforge.net/docs/dev/rst/problems.html

    @param columns_txt :: the text for the columns, one item per column
    @param rows_txt :: the text for the rows (will go in the leftmost column)
    @param cells :: a 2D numpy array with as many rows as items have been given
    in rows_txt, and as many columns as items have been given in columns_txt

    @param comparison_type :: whether this is a 'summary', or a full 'accuracy',
                              or 'runtime' table.
    @param comparison_dim :: dimension (accuracy / runtime)
    @param using_errors :: whether this comparison uses errors in the cost
                           function (weighted or unweighted), required to link
                           the table properly

    @param color_scale :: list with pairs of threshold value - color,
                          to produce color tags for the cells
    """

    columns_txt = display_name_for_minimizers(columns_txt)
    items_link = build_items_links(comparison_type, comparison_dim,
                                   using_errors)
    cell_len = calc_cell_len_rst_table(columns_txt, items_link, cells,
                                       color_scale)

    # The first column tends to be disproportionately long if it has a link
    first_col_len = calc_first_col_len(cell_len, rows_txt)
    tbl_header_top, tbl_header_text, tbl_header_bottom = \
    build_rst_table_header_chunks(first_col_len, cell_len, columns_txt)

    tbl_header = tbl_header_top + '\n' + tbl_header_text + '\n' + \
                 tbl_header_bottom + '\n'

    # The footer is in general the delimiter between rows,
    # including the last one
    tbl_footer = tbl_header_top + '\n'
    tbl_body = create_rst_table_body(cells, items_link, rows_txt, first_col_len,
                                     cell_len, color_scale, tbl_footer)

    return tbl_header  + tbl_body


def create_rst_table_body(cells, items_link, rows_txt, first_col_len, cell_len,
                          color_scale, tbl_footer):
    """
    Creates the body of the rst table that holds all the fitting results.
    """

    tbl_body = ''
    for row in range(0, cells.shape[0]):
        # Pick either individual or group link
        link = None
        if isinstance(items_link, list):
            link = items_link[row]
        else:
            link = items_link

        tbl_body += '|' + rows_txt[row].ljust(first_col_len, ' ') + '|'
        for col in range(0, cells.shape[1]):
            tbl_body += format_cell_value_rst(cells[row, col], cell_len,
                                              color_scale, link) + '|'
        tbl_body += '\n'
        tbl_body += tbl_footer

    return tbl_body


def display_name_for_minimizers(names):
    """
    Converts minimizer names into their "display names". For example
    to rename DTRS to "Trust region" or similar
    """

    display_names = names
    # Quick fix for DTRS name in version 3.8 - REMOVE
    for idx, minimizer in enumerate(names):
        if 'DTRS' == minimizer:
            display_names[idx] = 'Trust Region'

    return display_names


def build_items_links(comparison_type, comp_dim, using_errors):
    """
    Figure out the links from rst table cells to other pages/sections of pages.

    @param comparison_type :: whether this is a 'summary', or a full 'accuracy',
                              or 'runtime' table.
    @param comp_dim :: dimension (accuracy / runtime)
    @param using_errors :: whether using observational errors in cost functions

    @returns :: link or links to use from table cells.
    """
    if 'summary' == comparison_type:
        items_link = ['Minimizers_{0}_comparison_in_terms_of_{1}_nist_lower'.
                      format(weighted_suffix_string(using_errors), comp_dim),
                      'Minimizers_{0}_comparison_in_terms_of_{1}_nist_average'.
                      format(weighted_suffix_string(using_errors), comp_dim),
                      'Minimizers_{0}_comparison_in_terms_of_{1}_nist_higher'.
                      format(weighted_suffix_string(using_errors), comp_dim),
                      'Minimizers_{0}_comparison_in_terms_of_{1}_cutest'.
                      format(weighted_suffix_string(using_errors), comp_dim),
                      'Minimizers_{0}_comparison_in_terms_of_{1}_neutron_data'.
                      format(weighted_suffix_string(using_errors), comp_dim),
                      ]
    elif 'accuracy' == comparison_type or 'runtime' == comparison_type:
        if using_errors:
            items_link = 'FittingMinimizersComparisonDetailedWithWeights'
        else:
            items_link = 'FittingMinimizersComparisonDetailed'
    else:
        items_link = ''

    return items_link


def calc_cell_len_rst_table(columns_txt, items_link, cells, color_scale=None):
    """
    Calculate ascii character width needed for an RST table,
    using the length of the longest table cell.

    @param columns_txt :: list of the contents of the column headers
    @param items_link :: the links from rst table cells to other
                         pages/sections of pages
    @param cells :: the values of the results
    @param color_scale :: whether a color_scale is used or not
    @returns :: the length of the longest cell in a table
    """

    # The length of the longest header (minimizer name)
    max_header = len(max((col for col in columns_txt), key=len))
    # The value of the longest (once formatted) value in the table
    max_value = max(("%.4g" % cell for cell in np.nditer(cells)), key=len)

    # The length of the longest link reference
    # (angular bracket content present in summary tables)
    max_item = None
    if isinstance(items_link, list):
        max_item = max(items_link, key=len)
    else:
        items_link

    # Set cell length equal to the length of:
    # the longest combination of value, test name, and colour (plus padding)
    padding = 2
    cell_len = len(format_cell_value_rst(value=float(max_value),
                                         color_scale=color_scale,
                                         items_link=max_item).strip()) + padding
    # If the header is longer than any cell's contents,
    # i.e. is a group results table, use that length instead
    if cell_len < max_header:
        cell_len = max_header

    return cell_len


def calc_first_col_len(cell_len, rows_txt):
    """
    Calculate the first column length as it tends to be higher that all
    other columns.
    """

    first_col_len = cell_len
    for row_name in rows_txt:
        name_len = len(row_name)
        if name_len > first_col_len:
            first_col_len = name_len

    return first_col_len


def build_rst_table_header_chunks(first_col_len, cell_len, columns_txt):
    """
    Prepare the horizontal and vertical lines in the RST headers.

    @param first_col_len :: length (in characters) of the first column
    @param cell_len :: length of all other cells
    """

    tbl_header_top = '+'
    tbl_header_text = '|'
    tbl_header_bottom = '+'

    # First column in the header for the name of the test or statistics
    tbl_header_top += '-'.ljust(first_col_len, '-') + '+'
    tbl_header_text += ' '.ljust(first_col_len, ' ') + '|'
    tbl_header_bottom += '='.ljust(first_col_len, '=') + '+'
    for col_name in columns_txt:
        tbl_header_top += '-'.ljust(cell_len, '-') + '+'
        tbl_header_text += col_name.ljust(cell_len, ' ') + '|'
        tbl_header_bottom += '='.ljust(cell_len, '=') + '+'

    return tbl_header_top, tbl_header_text, tbl_header_bottom


def format_cell_value_rst(value, width=None, color_scale=None, items_link=None):
    """
    Build the content string for a table cell, adding style/color tags
    if required.

    @param value :: the value of the result
    @param width :: the width of the longest table cell
    @param color_scale :: the colour scale used
    @param items_link :: the links from rst table cells to other
                         pages/sections of pages
    @returns :: the (formatted) contents of a cell

    """
    if not color_scale:
        if not items_link:
            value_text = ' {0:.4g}'.format(value)
        else:
            value_text = ' :ref:`{0:.4g} <{1}>`'.format(value, items_link)
    else:
        color = ''
        for color_descr in color_scale:
            if value <= color_descr[0]:
                color = color_descr[1]
                break
        if not color:
            color = color_scale[-1][1]
        value_text = " :{0}:`{1:.4g}`".format(color, value)

    if width is not None:
        value_text = value_text.ljust(width, ' ')

    return value_text


def save_table_to_file(results_dir, table_data, errors, group_name, metric_type,
                       file_extension):
    """
    Saves a group results table or overall results table to a given file type.

    @param table_data :: the results table
    @param errors :: whether to use observational errors
    @param group_name :: name of this group of problems
                         (example 'NIST "lower difficulty"', or 'Neutron data')
    @param metric_type :: the test type of the table data
                          (e.g. runtime, accuracy)
    @param file_extension :: the file type extension (e.g. html)
    """


    file_name = ('comparison_{weighted}_{version}_{metric_type}_{group_name}.'
                 .format(weighted=weighted_suffix_string(errors),
                         version=BENCHMARK_VERSION_STR, metric_type=metric_type,
                         group_name=group_name))
    file_name = os.path.join(results_dir, file_name)

    if file_extension == 'html':
        rst_content = '.. include:: ' + \
                      str(os.path.join(SCRIPT_DIR, 'color_definitions.txt'))
        rst_content += '\n' + table_data
        table_data = publish_string(rst_content, writer_name='html')

    with open(file_name + file_extension, 'w') as tbl_file:
        print(table_data, file=tbl_file)

    logger.info('Saved {file_name}{extension} to {working_directory}'.
                 format(file_name=file_name, extension=file_extension,
                        working_directory=results_dir))




def weighted_suffix_string(use_errors):
    """
    Produces a suffix weighted/unweighted. Used to generate names of
    output files.
    """
    values = {True: 'weighted', False: 'unweighted'}
    return values[use_errors]


def make_result_tables_directory(results_dir, group_name):

    """
    Creates the results directory where the tables are located.
    e.g. fitbenchmarking/results/neutron/Tables/
    """

    if 'nist' in group_name:
        group_results_dir = os.path.join(results_dir, 'nist')
        if not os.path.exists(group_results_dir):
            os.makedirs(group_results_dir)
        tables_dir = os.path.join(group_results_dir, "tables", group_name)


    elif 'neutron' in group_name:
        group_results_dir = os.path.join(results_dir, 'neutron')
        if not os.path.exists(group_results_dir):
            os.makedirs(group_results_dir)
        tables_dir = os.path.join(group_results_dir, "tables")


    if not os.path.exists(tables_dir):
        os.makedirs(tables_dir)

    return tables_dir
