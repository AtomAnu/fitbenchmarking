"""
Test file to test the fitting_problem file.
"""

from collections import OrderedDict
import numpy as np
from unittest import TestCase

from fitbenchmarking.parsing.fitting_problem import FittingProblem
from fitbenchmarking.utils import exceptions


class TestFittingProblem(TestCase):
    """
    Class to test the FittingProblem class
    """

    def test_sanitised_name(self):
        fitting_problem = FittingProblem()
        expected = "test_1"
        fitting_problem.name = "test 1"
        self.assertEqual(fitting_problem.sanitised_name, expected)
        fitting_problem.name = "test,1"
        self.assertEqual(fitting_problem.sanitised_name, expected)

    def test_verify_problem(self):
        """
        Test that verify only passes if all required values are set.
        """
        fitting_problem = FittingProblem()
        with self.assertRaises(exceptions.FittingProblemError):
            fitting_problem.verify()
            self.fail('verify() passes when no values are set.')

        fitting_problem.starting_values = [
            OrderedDict([('p1', 1), ('p2', 2)])]
        with self.assertRaises(exceptions.FittingProblemError):
            fitting_problem.verify()
            self.fail('verify() passes starting values are set.')

        fitting_problem.data_x = np.array([1, 2, 3, 4, 5])
        with self.assertRaises(exceptions.FittingProblemError):
            fitting_problem.verify()
            self.fail('verify() passes when data_x is set.')

        fitting_problem.data_y = np.array([1, 2, 3, 4, 5])
        with self.assertRaises(exceptions.FittingProblemError):
            fitting_problem.verify()
            self.fail('verify() passes when data_y is set.')

        fitting_problem.function = lambda x, p1, p2: p1 + p2
        try:
            fitting_problem.verify()
        except exceptions.FittingProblemError:
            self.fail('verify() fails when all required values set.')

        fitting_problem.data_x = [1, 2, 3]
        with self.assertRaises(exceptions.FittingProblemError):
            fitting_problem.verify()
            self.fail('verify() passes for x values not numpy.')

    def test_eval_f(self):
        """
        Test that eval_f is running the correct function
        """
        fitting_problem = FittingProblem()
        self.assertRaises(exceptions.FittingProblemError,
                          fitting_problem.eval_f,
                          x=2,
                          params=[1, 2, 3])
        fitting_problem.function = lambda x, p1: x + p1
        x_val = np.array([1, 8, 11])
        eval_result = fitting_problem.eval_f(x=x_val,
                                             params=[5])
        self.assertTrue(all(eval_result == np.array([6, 13, 16])))

        fitting_problem.data_x = np.array([20, 21, 22])
        eval_result = fitting_problem.eval_f(params=[5])
        self.assertTrue(all(eval_result == np.array([25, 26, 27])))

    def test_eval_r(self):
        """
        Test that eval_r is correct
        """
        fitting_problem = FittingProblem()
        self.assertRaises(exceptions.FittingProblemError,
                          fitting_problem.eval_r,
                          params=[1, 2, 3],
                          x=2)

        fitting_problem.function = lambda x, p1: x + p1
        x_val = np.array([1, 8, 11])
        y_val = np.array([6, 10, 20])

        eval_result = fitting_problem.eval_r(x=x_val,
                                             y=y_val,
                                             params=[5])
        self.assertTrue(all(eval_result == np.array([0, -3, 4])))

        e_val = np.array([2, 4, 1])
        eval_result = fitting_problem.eval_r(x=x_val,
                                             y=y_val,
                                             e=e_val,
                                             params=[5])
        self.assertTrue(all(eval_result == np.array([0, -0.75, 4])))

        fitting_problem.data_x = np.array([20, 21, 22])
        fitting_problem.data_y = np.array([20, 30, 35])
        eval_result = fitting_problem.eval_r(params=[5])
        self.assertTrue(all(eval_result == np.array([-5, 4, 8])))

        fitting_problem.data_e = np.array([2, 5, 10])
        eval_result = fitting_problem.eval_r(params=[5])
        self.assertTrue(all(eval_result == np.array([-2.5, 0.8, 0.8])))

    def test_eval_r_norm(self):
        """
        Test that eval_r_norm is correct
        """
        fitting_problem = FittingProblem()
        fitting_problem.function = lambda x, p1: x + p1
        x_val = np.array([1, 8, 11])
        y_val = np.array([6, 10, 20])
        e_val = np.array([0.5, 10, 0.1])

        eval_result = fitting_problem.eval_r_norm(params=[5],
                                                  x=x_val,
                                                  y=y_val,
                                                  e=e_val)
        self.assertEqual(eval_result, 1600.09)

        fitting_problem.data_x = x_val
        fitting_problem.data_y = y_val
        eval_result = fitting_problem.eval_r_norm(params=[5])
        self.assertEqual(eval_result, 25)

    def test_eval_j(self):
        """
        Test that eval_j is correct
        """
        def f(x, p1, p2):
            return p1 * np.exp(p2 * x)

        def J(x, p):
            return np.column_stack((-np.exp(p[1] * x),
                                    -x * p[0] * np.exp(p[1] * x)))

        fitting_problem = FittingProblem()
        fitting_problem.function = f
        fitting_problem.data_x = np.array([1, 2, 3, 4, 5])
        fitting_problem.data_y = np.array([1, 2, 4, 8, 16])
        params = [6, 0.1]

        eval_result = fitting_problem.eval_j(params=params)
        actual = J(x=fitting_problem.data_x, p=params)
        self.assertTrue(np.isclose(actual, eval_result).all())

    def test_eval_starting_params(self):
        """
        Test that eval_starting_params returns the correct result
        """
        fitting_problem = FittingProblem()
        self.assertRaises(exceptions.FittingProblemError,
                          fitting_problem.eval_starting_params,
                          param_set=0)
        fitting_problem.function = lambda x, p1: x + p1
        fitting_problem.starting_values = [OrderedDict([('p1', 3)]),
                                           OrderedDict([('p1', 7)])]
        fitting_problem.data_x = np.array([1])
        eval_result = fitting_problem.eval_starting_params(0)
        self.assertTrue(all(eval_result == np.array([4])))
        eval_result = fitting_problem.eval_starting_params(1)
        self.assertTrue(all(eval_result == np.array([8])))

    def test_get_function_params(self):
        """
        Tests that the function params is formatted correctly
        """
        fitting_problem = FittingProblem()
        expected_function_def = 'a=1, b=2.0, c=3.3, d=4.99999'
        fitting_problem.starting_values = [
            OrderedDict([('a', 0), ('b', 0), ('c', 0), ('d', 0)])]
        params = [1, 2.0, 3.3, 4.99999]
        function_def = fitting_problem.get_function_params(params=params)
        self.assertEqual(function_def, expected_function_def)

    def test_correct_data(self):
        """
        Tests that correct data gives the expected result
        """
        fitting_problem = FittingProblem()
        x_data = np.array([-0.5, 0.0, 1.0, 0.5, 1.5, 2.0, 2.5, 3.0, 4.0])
        y_data = np.array([0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0])
        e_data = np.array([1.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 9.0])
        start_x = 0.5
        end_x = 2.5
        expected_x_data = np.array([0.5, 1.0, 1.5, 2.0, 2.5])
        expected_y_data = np.array([3.0, 2.0, 4.0, 5.0, 6.0])
        expected_e_data = np.array([40.0, 30.0, 50.0, 60.0, 70.0])

        fitting_problem.data_x = x_data
        fitting_problem.data_y = y_data
        fitting_problem.data_e = e_data
        fitting_problem.start_x = start_x
        fitting_problem.end_x = end_x

        fitting_problem.correct_data(True)
        self.assertTrue(
            np.isclose(fitting_problem.data_x[fitting_problem.sorted_index],
                       expected_x_data).all())
        self.assertTrue(
            np.isclose(fitting_problem.data_y[fitting_problem.sorted_index],
                       expected_y_data).all())
        self.assertTrue(
            np.isclose(fitting_problem.data_e[fitting_problem.sorted_index],
                       expected_e_data).all())

        fitting_problem.correct_data(False)
        self.assertTrue(
            np.isclose(fitting_problem.data_x[fitting_problem.sorted_index],
                       expected_x_data).all())
        self.assertTrue(
            np.isclose(fitting_problem.data_y[fitting_problem.sorted_index],
                       expected_y_data).all())
        self.assertIs(fitting_problem.data_e, None)
