"""
Implements the base class for the fitting software controllers.
"""

from abc import ABCMeta, abstractmethod

import numpy as np

from fitbenchmarking.utils.exceptions import ControllerAttributeError


class Controller:
    """
    Base class for all fitting software controllers.
    These controllers are intended to be the only interface into the fitting
    software, and should do so by implementing the abstract classes defined
    here.
    """

    __metaclass__ = ABCMeta

    def __init__(self, problem):
        """
        Initialise the class.
        Sets up data as defined by the problem and use_errors variables,
        and initialises variables that will be used in other methods.

        :param problem: The parsed problem
        :type problem: fitting_problem (see fitbenchmarking.parsers)
        """

        # Problem: The problem object from parsing
        self.problem = problem

        # Data: Data used in fitting. Might be different from problem
        #       if corrections are needed (e.g. startX)
        self.data_x = problem.data_x
        self.data_y = problem.data_y
        self.data_e = problem.data_e

        # Initial Params: The starting values for params when fitting
        self.initial_params = None
        # Staring Valuess: The list of starting parameters
        self.starting_values = problem.starting_values
        # Parameter set: The index of the starting parameters to use
        self.parameter_set = None
        # Minimizer: The current minimizer to use
        self.minimizer = None

        # Final Params: The final values for the params from the minimizer
        self.final_params = None
        # Results: Stores output results using the final parameters in
        #          numpy array
        self.results = None

        # Flag: error handling flag
        self.flag = None

    def prepare(self):
        """
        Check that function and minimizer have been set.
        If both have been set, run self.setup().
        """

        if (self.minimizer is not None) and (self.parameter_set is not None):
            self.initial_params = \
                list(self.starting_values[self.parameter_set].values())
            self.setup()
        else:
            raise ControllerAttributeError('Either minimizer or parameter_set '
                                           'is set to None.')

    def eval_chisq(self, params, x=None, y=None, e=None):
        """
        Computes the chisq value

        :param params: The parameters to calculate residuals for
        :type params: list
        :param x: x data points, defaults to self.data_x
        :type x: numpy array, optional
        :param y: y data points, defaults to self.data_y
        :type y: numpy array, optional
        :param e: error at each data point, defaults to self.data_e
        :type e: numpy array, optional

        :return: The sum of squares of residuals for the datapoints at the
                 given parameters
        :rtype: numpy array
        """
        out = self.problem.eval_r_norm(params=params, x=x, y=y, e=e)
        return out

    def check_attributes(self):
        """
        A helper function which checks all required attributes are set
        in software controllers
        """
        values = {'flag': int}

        for attr_name, attr_type in values.items():
            attr = getattr(self, attr_name)
            if not isinstance(attr, attr_type):
                raise ControllerAttributeError(
                    'Attribute "{}" in the controller is not the expected '
                    'type. Expected "{}", got {}.'.format(
                        attr_name, attr_type, type(attr)))
            valid_flags = [0, 1, 2, 3]
            if attr_name == 'flag' and attr not in valid_flags:
                raise ControllerAttributeError(
                    'Attribute "flag" in the controller must be one of {}.'
                    ' Got: {}.'.format(valid_flags, attr))

    @abstractmethod
    def setup(self):
        """
        Setup the specifics of the fitting

        Anything needed for "fit" should be saved to self.
        """
        raise NotImplementedError

    @abstractmethod
    def fit(self):
        """
        Run the fitting.
        """
        raise NotImplementedError

    @abstractmethod
    def cleanup(self):
        """
        Retrieve the result as a numpy array and store in self.results
        """
        raise NotImplementedError
