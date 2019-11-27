"""
Implements a controller for GSL
https://www.gnu.org/software/gsl/
using the pyGSL python interface
https://sourceforge.net/projects/pygsl/
"""
import numpy as np

from pygsl import multifit_nlin, multiminimize, errno
from pygsl import _numobj as numx

from scipy.optimize._numdiff import approx_derivative

from fitbenchmarking.fitting.controllers.base_controller import Controller


class GSLController(Controller):
    """
    Controller for the GSL fitting software
    """
    def __init__(self, problem, use_errors):
        """
        Initializes variable used for temporary storage
        """
        super(GSLController, self).__init__(problem, use_errors)
        
        self._solver = None
        self._residual_methods = None
        self._function_methods_no_jac = None
        self._function_methods_with_jac = None
        self._gradient_tol = None
        self._abserror = None
        self._relerror = None
        self._maxits = None


    def _prediction_error(self, p, data=None):
        f = self.problem.eval_f(x=self.data_x,
                                params=p,
                                function_id=self.function_id)
        f = f - self.data_y
        if self.use_errors:
            f = f / self.data_e
        return f

    def _jac(self, p, data=None):
        j = approx_derivative(self._prediction_error,
                              p)
        return j

    def _fdf(self, p, data=None):
        f = self._prediction_error(p)
        df = self._jac(p)
        return f, df

    def _chi_squared(self, p, data=None):
        f = self._prediction_error(p)
        return np.dot(f, f)

    def _jac_chi_squared(self, p, data=None):
        j = approx_derivative(self._chi_squared,
                              p)
        return j

    def _chi_squared_fdf(self, p, data=None):
        f = self._chi_squared(p)
        df = self._jac_chi_squared(p)
        return f, df

    def setup(self):
        """
        Setup for GSL
        """
        data = numx.array([self.data_x,
                           self.data_y,
                           self.data_e])
        n = len(self.data_x)
        p = len(self.initial_params)
        pinit = numx.array(self.initial_params)

        self._residual_methods = ['lmsder',
                                  'lmder']
        self._function_methods_no_jac = ['nmsimplex',
                                         'nmsimplex2']
        self._function_methods_with_jac = ['conjugate_pr',
                                           'conjugate_fr',
                                           'vector_bfgs',
                                           'vector_bfgs2',
                                           'steepest_descent']

        # set up the system
        if self.minimizer in self._residual_methods:
            mysys = multifit_nlin.gsl_multifit_function_fdf(
                self._prediction_error,
                self._jac,
                self._fdf,
                data,
                n,
                p)
            self._solver = getattr(multifit_nlin, self.minimizer)(mysys, n, p)
        elif self.minimizer in self._function_methods_no_jac:
            mysys = multiminimize.gsl_multimin_function(self._chi_squared,
                                                        data,
                                                        p)
            self._solver = getattr(multiminimize, self.minimizer)(mysys, p)
        elif self.minimizer in self._function_methods_with_jac:
            mysys = multiminimize.gsl_multimin_function_fdf(
                self._chi_squared,
                self._jac_chi_squared,
                self._chi_squared_fdf,
                data,
                p)
            self._solver = getattr(multiminimize, self.minimizer)(mysys, p)
        else:
            raise RuntimeError("An undefined GSL minimizer was selected")

        # Set up initialization parameters
        #
        # These have been chosen to be consistent with the parameters
        # used in Mantid.
        initial_steps = 1.0 * numx.array(np.ones(p))
        step_size = 0.1
        tol = 1e-4
        self._gradient_tol = 1e-3
        self._abserror = 1e-4
        self._relerror = 1e-4
        self._maxits = 500

        if self.minimizer in self._residual_methods:
            self._solver.set(pinit)
        elif self.minimizer in self._function_methods_no_jac:
            self._solver.set(pinit, initial_steps)
        else:
            self._solver.set(pinit, step_size, tol)

    def fit(self):
        """
        Run problem with GSL
        """
        self.success = False

        for _ in range(self._maxits):
            status = self._solver.iterate()
            # check if the method has converged
            if self.minimizer in self._residual_methods:
                x = self._solver.getx()
                dx = self._solver.getdx()
                status = multifit_nlin.test_delta(dx, x,
                                                  self._abserror,
                                                  self._relerror)
            elif self.minimizer in self._function_methods_no_jac:
                simplex_size = self._solver.size()
                status = multiminimize.test_size(simplex_size,
                                                 self._abserror)
            else:  # must be in function_methods_with_jac
                gradient = self._solver.gradient()
                status = multiminimize.test_gradient(gradient,
                                                     self._gradient_tol)
            if status == errno.GSL_SUCCESS:
                self.success = True
                break
            elif status != errno.GSL_CONTINUE:
                raise ValueError("GSL couldn't find a solution")
        else:
            raise ValueError("Maximum number of iterations exceeded!")

    def cleanup(self):
        """
        Convert the result to a numpy array and populate the variables results
        will be read from
        """
        if self.success:
            self.final_params = self._solver.getx()
            self.results = self.problem.eval_f(x=self.data_x,
                                               params=self.final_params,
                                               function_id=self.function_id)
