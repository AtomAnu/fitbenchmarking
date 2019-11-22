"""
Functions that creates the tables and the visual display pages.
"""

from __future__ import (absolute_import, division, print_function)
from collections import OrderedDict
import logging
import os
import pandas as pd
import numpy as np
import re
import pytablewriter


from fitbenchmarking.utils.logging_setup import logger
from fitbenchmarking.resproc import visual_pages
from fitbenchmarking.utils import create_dirs, options, misc

# Some naming conventions for the output files
FILENAME_SUFFIX_ACCURACY = 'acc'
FILENAME_SUFFIX_RUNTIME = 'runtime'
FILENAME_EXT_TXT = 'txt'
FILENAME_EXT_HTML = 'html'

html_color_scale = ['#fef0d9', '#fdcc8a', '#fc8d59', '#e34a33', '#b30000']


def save_results_tables(software_options, results_per_test, group_name,
                        use_errors, color_scale=None, results_dir=None):
    """
    Saves the results of the fitting to html/rst tables.

    @param software_options :: dictionary containing software used in fitting the problem, list of minimizers and location of json file contain minimizers
    @param minimizers :: array with minimizer names
    @param results_per_test :: results nested array of objects
    @param group_name :: name of the problem group
    @param use_errors :: bool whether to use errors or not
    @param colour_scale :: colour the html table
    @param results_dir :: directory in which the results are saved

    @returns :: html/rst tables with the fitting results
    """

    minimizers, software = misc.get_minimizers(software_options)
    comparison_mode = software_options.get('comparison_mode', None)

    if comparison_mode is None:
        if 'options_file' in software_options:
            options_file = software_options['options_file']
            comparison_mode = options.get_option(options_file=options_file,
                                                 option='comparison_mode')
        else:
            comparison_mode = options.get_option(option='comparison_mode')

        if comparison_mode is None:
            comparison_mode = 'both'

    if isinstance(software, list):
        minimizers = sum(minimizers, [])

    tables_dir = create_dirs.restables_dir(results_dir, group_name)
    linked_problems = \
        visual_pages.create_linked_probs(results_per_test, group_name, results_dir)

    generate_tables(results_per_test, minimizers,
                    linked_problems, color_scale, comparison_mode)

    logging.shutdown()


def generate_tables(results_per_test, minimizers,
                    linked_problems, colour_scale, comparison_mode):
    """
    Generates accuracy and runtime tables, with both normalised and absolute results, and summary tables.

    @param results_per_test :: results nested array of objects
    @param minimizers :: array with minimizer names
    linked_problems ::

    @returns :: data and summary tables of the results as np arrays
    """

    acc_dict, time_dict, html_links = create_results_dict(results_per_test,
                                                          linked_problems)
    acc_tbl = \
        create_tables(acc_dict, minimizers)
    runtime_tbl = \
        create_tables(time_dict, minimizers)
    create_pandas_html(acc_tbl[comparison_mode], runtime_tbl[comparison_mode],
                       minimizers, colour_scale, html_links)
    create_pandas_rst(acc_tbl[comparison_mode], runtime_tbl[comparison_mode],
                      minimizers, colour_scale, linked_problems)


def create_results_dict(results_per_test, linked_problems):
    """
    Generates a dictionary used to create HTML and RST tables.

    @param results_per_test :: results nested array of objects
    linked_problems ::

    @returns :: data and summary tables of the results as np arrays
    """

    count = 1
    prev_name = ''
    template = '<a target="_blank" href="{0}">{1}</a>'
    acc_results = OrderedDict()
    time_results = OrderedDict()
    html_links = []

    for test_idx, prob_results in enumerate(results_per_test):
        name = results_per_test[test_idx][0].problem.name
        if name == prev_name:
            count += 1
        else:
            count = 1
        prev_name = name
        prob_name = name + ' ' + str(count)
        name, url = linked_problems[test_idx].split('<')
        html_links.append(template.format(url, prob_name))
        acc_results[prob_name] = [result.chi_sq for result in results_per_test[test_idx]]
        time_results[prob_name] = [result.runtime for result in results_per_test[test_idx]]
    return acc_results, time_results, html_links


def check_normalised(data, colours):
    data_numpy = data.array.to_numpy()
    data_list = []
    for x in data_numpy:
        if x != "nan":
            norm_stripped = re.findall('\(([^)]+)', x)
            if norm_stripped == []:
                data_list.append(float(x))
            else:
                if norm_stripped[0] != "nan":
                    data_list.append(float(norm_stripped[0]))
                else:
                    data_list.append(np.inf)
        else:
            data_list.append(np.inf)

    data_list = data_list / np.min(data_list)
    data_list = np.select(
        [data_list <= 1.1, data_list <= 1.33,
         data_list <= 1.75, data_list <= 3, data_list > 3],
        colours)
    return data_list


def create_pandas_html(acc_tbl, runtime_tbl,
                       minimizers, colour_scale, html_links):
    """
    Generates a pandas data frame used to create the html tables.

    @param results_per_test :: results nested array of objects
    @param minimizers :: array with minimizer names
    linked_problems ::

    @returns :: data and summary tables of the results as np arrays
    """
    acc_tbl.index = html_links
    runtime_tbl.index = html_links

    def colour_highlight(data):
        '''
        highlight the maximum in a Series or DataFrame
        '''
        data_list = check_normalised(data, html_color_scale)

        return ['background-color: {0}'.format(i) for i in data_list]

    for table in [acc_tbl, runtime_tbl]:
        table_style = table.style.apply(colour_highlight, axis=1)
        f = open("test1.html", "w")
        f.write(table_style.render())
        f.close()


def create_pandas_rst(acc_tbl, runtime_tbl, minimizers, colour_scale,
                      linked_problems):
    """
    Generates pandas dataframes in rst format.

    :param table_data :: dictionary containing results
    :type group_name :: dict
    :param minimizers :: list of minimizers (column headers)
    :type minimizers :: list
    :param colour_scale :: user defined colour scale
    :type colour_scale :: list


    :return :: list(tbl, tbl_norm, tbl_combined) array of fitting results for
                the problem group and the path to the results directory
    :rtype :: [pandas DataFrame, pandas DataFrame, pandas DataFrame]
    """
    rst_colours = [colour[1] for colour in colour_scale]

    acc_tbl.index = linked_problems
    runtime_tbl.index = linked_problems

    def colour_highlight(data):
        '''
        highlight the maximum in a Series or DataFrame
        '''
        data_list = check_normalised(data, rst_colours)
        for i, x in enumerate(data):
            data[i] = ':{}:`{}`'.format(data_list[i], x)

        return data

    for table in [acc_tbl, runtime_tbl]:
        table.apply(colour_highlight, axis=1)
        writer = pytablewriter.RstGridTableWriter()
        writer.table_name = "example_table"
        writer.from_dataframe(table, add_index_column=True)
        writer.write_table()


def create_tables(table_data, minimizers):
    """
    Generates pandas tables.

    :param table_data :: dictionary containing results
    :type group_name :: dict
    :param minimizers :: list of minimizers (column headers)
    :type group_name :: list


    :return :: dict(tbl, tbl_norm, tbl_combined) array of fitting results for
                the problem group and the path to the results directory
    :rtype :: dict{pandas DataFrame, pandas DataFrame, pandas DataFrame}
    """

    tbl = pd.DataFrame.from_dict(table_data, orient='index')
    tbl.columns = minimizers

    tbl_norm = tbl.apply(lambda x: x / x.min(), axis=1)
    tbl_norm = tbl_norm.applymap(lambda x: '{:.4e}'.format(x))
    tbl = tbl.applymap(lambda x: '{:.4e}'.format(x))

    tbl_combined = OrderedDict()
    for table1, table2 in zip(tbl.iterrows(), tbl_norm.iterrows()):
        tbl_combined[table1[0]] = []
        for value1, value2 in zip(table1[1].array, table2[1].array):
            tbl_combined[table1[0]].append('{} ({})'.format(value1, value2))
    tbl_combined = pd.DataFrame.from_dict(tbl_combined, orient='index')
    tbl_combined.columns = minimizers
    results_table = {'abs': tbl, 'rel': tbl_norm, 'both': tbl_combined}
    return results_table
