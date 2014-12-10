import numpy as np
import pandas as pd
from scipy import integrate, interpolate, special
import sympy as sym

import models

# represent endogenous variables mu and theta as a deferred vector
V = sym.DeferredVector('V')


class ShootingSolver(object):
    """Solves a model using forward shooting."""

    __numeric_input_types = None

    __numeric_jacobian = None

    __numeric_profit = None

    __numeric_quantities = None

    __numeric_span_of_control = None

    __numeric_system = None

    __numeric_type_resource = None

    __numeric_wage = None

    __integrator = None

    _modules = [{'ImmutableMatrix': np.array, 'erf': special.erf}, 'numpy']

    def __init__(self, model):
        """
        Create an instance of the ShootingSolver class.

        """
        self.model = model

    @property
    def _numeric_input_types(self):
        """
        Vectorized function for numerical evaluation of the input type
        complementarity.

        :getter: Return current function for evaluating the complementarity.
        :type: function

        """
        if self.__numeric_input_types is None:
            self.__numeric_input_types = sym.lambdify(self._symbolic_args,
                                                      self._symbolic_input_types,
                                                      self._modules)
        return self.__numeric_input_types

    @property
    def _numeric_jacobian(self):
        """
        Vectorized function for numerical evaluation of model Jacobian.

        :getter: Return current function for evaluating the Jacobian.
        :type: function

        """
        if self.__numeric_jacobian is None:
            self.__numeric_jacobian = sym.lambdify(self._symbolic_args,
                                                   self._symbolic_jacobian,
                                                   self._modules)
        return self.__numeric_jacobian

    @property
    def _numeric_profit(self):
        """
        Vectorized function for numerical evaluation of profits.

        :getter: Return current function for evaluating profits.
        :type: function

        """
        if self.__numeric_profit is None:
            self.__numeric_profit = sym.lambdify(self._symbolic_args,
                                                 self._symbolic_profit,
                                                 self._modules)
        return self.__numeric_profit

    @property
    def _numeric_quantities(self):
        """
        Vectorized function for numerical evaluation of the quantity
        complementarity.

        :getter: Return current function for evaluating the complementarity.
        :type: function

        """
        if self.__numeric_quantities is None:
            self.__numeric_quantities = sym.lambdify(self._symbolic_args,
                                                     self._symbolic_quantities,
                                                     self._modules)
        return self.__numeric_quantities

    @property
    def _numeric_span_of_control(self):
        """
        Vectorized function for numerical evaluation of the resource
        complementarity.

        :getter: Return current function for evaluating the complementarity.
        :type: function

        """
        if self.__numeric_span_of_control is None:
            self.__numeric_span_of_control = sym.lambdify(self._symbolic_args,
                                                          self._symbolic_span_of_control,
                                                          self._modules)
        return self.__numeric_span_of_control

    @property
    def _numeric_system(self):
        """
        Vectorized function for numerical evaluation of model system.

        :getter: Return current function for evaluating the system.
        :type: function

        """
        if self.__numeric_system is None:
            self.__numeric_system = sym.lambdify(self._symbolic_args,
                                                 self._symbolic_system,
                                                 self._modules)
        return self.__numeric_system

    @property
    def _numeric_type_resource(self):
        """
        Vectorized function for numerical evaluation of the resource
        complementarity.

        :getter: Return current function for evaluating the complementarity.
        :type: function

        """
        if self.__numeric_type_resource is None:
            self.__numeric_type_resource = sym.lambdify(self._symbolic_args,
                                                        self._symbolic_type_resource,
                                                        self._modules)
        return self.__numeric_type_resource

    @property
    def _numeric_wage(self):
        """
        Vectorized function for numerical evaluation of wages.

        :getter: Return current function for evaluating wages.
        :type: function

        """
        if self.__numeric_wage is None:
            self.__numeric_wage = sym.lambdify(self._symbolic_args,
                                               self._symbolic_wage,
                                               self._modules)
        return self.__numeric_wage

    @property
    def _solution(self):
        """
        Solution to the model represented as a NumPy array.

        :getter: Return the array represnting the current solution
        :setter: Set a new array defining the solution.
        :type: numpy.ndarray

        """
        return self.__solution

    @_solution.setter
    def _solution(self, value):
        """Set a new value for the solution array."""
        self.__solution = value

    @property
    def _symbolic_args(self):
        """
        Symbolic arguments used when lambdifying symbolic Jacobian and system.

        :getter: Return the list of symbolic arguments.
        :type: list

        """
        return self._symbolic_variables + self._symbolic_params

    @property
    def _symbolic_equations(self):
        """
        Symbolic expressions defining the right-hand side of a system of ODEs.

        :getter: Return the list of symbolic expressions.
        :type: list

        """
        return [self.model.matching.mu_prime, self.model.matching.theta_prime]

    @property
    def _symbolic_input_types(self):
        """
        Symbolic expression for complementarity between input types.

        :getter: Return the current expression for the complementarity.
        :type: sympy.Basic

        """
        Fxy = self.model.matching.input_types
        return Fxy.subs({'mu': V[0], 'theta': V[1]})

    @property
    def _symbolic_jacobian(self):
        """
        Symbolic expressions defining the Jacobian of a system of ODEs.

        :getter: Return the symbolic Jacobian.
        :type: sympy.Basic

        """
        return self._symbolic_system.jacobian([V[0], V[1]])

    @property
    def _symbolic_params(self):
        """
        Symbolic parameters passed as arguments when lambdifying symbolic
        Jacobian and system.

        :getter: Return the list of symbolic parameter arguments.
        :type: list

        """
        return sym.var(list(self.model.params.keys()))

    @property
    def _symbolic_profit(self):
        """
        Symbolic expression defining profit.

        :getter: Return the symbolic expression for profits.
        :type: sympy.Basic

        """
        profit = self.model.matching.profit
        return profit.subs({'mu': V[0], 'theta': V[1]})

    @property
    def _symbolic_quantities(self):
        """
        Symbolic expression for complementarity between input quantities.

        :getter: Return the current expression for the complementarity.
        :type: sympy.Basic

        """
        Flr = self.model.matching.quantities
        return Flr.subs({'mu': V[0], 'theta': V[1]})

    @property
    def _symbolic_span_of_control(self):
        """
        Symbolic expression for span-of-control complementarity.

        :getter: Return the current expression for the complementarity.
        :type: sympy.Basic

        """
        Fyl = self.model.matching.span_of_control
        return Fyl.subs({'mu': V[0], 'theta': V[1]})

    @property
    def _symbolic_system(self):
        """
        Symbolic matrix defining the right-hand side of a system of ODEs.

        :getter: Return the symbolic matrix.
        :type: sympy.Matrix

        """
        system = sym.Matrix(self._symbolic_equations)
        return system.subs({'mu': V[0], 'theta': V[1]})

    @property
    def _symbolic_type_resource(self):
        """
        Symbolic expression for complementarity between worker type and
        firm resources.

        :getter: Return the current expression for the complementarity.
        :type: sympy.Basic

        """
        Fxr = self.model.matching.type_resource
        return Fxr.subs({'mu': V[0], 'theta': V[1]})

    @property
    def _symbolic_variables(self):
        """
        Symbolic variables passed as arguments when lambdifying symbolic
        Jacobian and system.

        :getter: Return the list of symbolic variable arguments.
        :type: list

        """
        return [self.model.workers.var, V]

    @property
    def _symbolic_wage(self):
        """
        Symbolic expression defining wages.

        :getter: Return the symbolic expression for wages.
        :type: sympy.Basic

        """
        wage = self.model.matching.wage
        return wage.subs({'mu': V[0], 'theta': V[1]})

    @property
    def integrator(self):
        """
        Integrator for solving a system of ordinary differential equations.

        :getter: Return the current integrator.
        :type: scipy.integrate.ode

        """
        if self.__integrator is None:
            self.__integrator = integrate.ode(f=self.evaluate_rhs,
                                              jac=self.evaluate_jacobian)
        return self.__integrator

    @property
    def model(self):
        """
        Instance of the models.Model class to be solved via forward shooting.

        :getter: Return the current models.Model instance.
        :setter: Set a new models.Model instance.
        :type: models.Model

        """
        return self._model

    @model.setter
    def model(self, model):
        """Set a new Model attribute."""
        self._model = self._validate_model(model)
        self._clear_cache()

    @property
    def solution(self):
        """
        Solution to the model represented as a Pandas DataFrame.

        :getter: Return the DataFrame representing the current solution.
        :type: pandas.DataFrame

        """
        col_names = ['x', 'firm productivity', 'firm size', 'wage', 'profit']
        df = pd.DataFrame(self._solution, columns=col_names)
        if self.model.assortativity == 'positive':
            df.sort('x', inplace=True)
        else:
            pass
        return df.set_index('x')

    def _check_pam(self, step):
        r"""
        Check necessary condition required for a positive assortative
        matching (PAM).

        Parameters
        ----------
        step : numpy.ndarray (shape=(5,))
            Step along a putative solution to the model.

        Returns
        -------
        check : boolean
            Flag indicating whether positive assortative matching condition is
            satisfied for the given step.

        """
        # unpack the step
        x, V = step[0], step[1:3]

        LHS = self.evaluate_input_types(x, V) * self.evaluate_quantities(x, V)
        RHS = (self.evaluate_span_of_control(x, V) *
               self.evaluate_type_resource(x, V))

        if np.isclose(LHS - RHS, 0):
            check = True
        else:
            check = LHS > RHS

        return check

    def _clear_cache(self):
        """Clear cached functions used for numerical evaluation."""
        self.__numeric_input_types = None
        self.__numeric_jacobian = None
        self.__numeric_profit = None
        self.__numeric_quantities = None
        self.__numeric_span_of_control = None
        self.__numeric_system = None
        self.__numeric_type_resource = None
        self.__numeric_wage = None
        self.__integrator = None

    def _converged_firms(self, tol):
        """Check whether solution component for firms has converged."""
        if abs(self.integrator.y[0] - self.model.firms.lower) <= tol:
            converged = True
        else:
            converged = False
        return converged

    def _converged_workers(self, tol):
        """Check whether solution component for workers has converged."""
        if self.model.assortativity == 'positive':
            if abs(self.integrator.t - self.model.workers.lower) <= tol:
                converged = True
            else:
                converged = False
        else:
            if abs(self.integrator.t - self.model.workers.upper) <= tol:
                converged = True
            else:
                converged = False

        return converged

    def _exhausted_firms(self, tol):
        """Check whether firms have been exhausted."""
        if self.integrator.y[0] - self.model.firms.lower < -tol:
            exhausted = True
        else:
            exhausted = False
        return exhausted

    def _guess_firm_size_upper_too_low(self, bound, tol):
        """Check whether guess for upper bound for firm size is too low."""
        return abs(self.integrator.y[1] - bound) <= tol

    def _reset_solution(self, firm_size):
        """
        Reset the initial condition for the integrator and re-initialze the
        solution array.

        Parameters
        ----------
        firm_size : float

        """
        x_lower, x_upper = self.model.workers.lower, self.model.workers.upper
        y_upper = self.model.firms.upper
        initial_V = np.array([y_upper, firm_size])

        if self.model.assortativity == 'positive':
            self.integrator.set_initial_value(initial_V, x_upper)
            wage = self.evaluate_wage(x_upper, initial_V)
            profit = self.evaluate_profit(x_upper, initial_V)
            self._solution = np.hstack((x_upper, initial_V, wage, profit))
        else:
            self.integrator.set_initial_value(initial_V, x_lower)
            wage = self.evaluate_wage(x_lower, initial_V)
            profit = self.evaluate_profit(x_lower, initial_V)
            self._solution = np.hstack((x_lower, initial_V, wage, profit))

    def _update_initial_guess(self, lower, upper):
        """
        Use bisection method to arrive at new initial guess for firm size.

        Parameters
        ----------
        lower : float
            Lower bound on the true initial condition for firm size.
        upper : float
            Upper bound on the true initial condition for firm size.

        Returns
        -------
        guess : float
            New initial guess for firm size.

        """
        err_mesg = 'Upper and lower bounds are identical: check solver tols!'
        assert (upper - lower) > np.finfo('float').eps, err_mesg
        guess = 0.5 * (lower + upper)
        return guess

    def _update_solution(self, step_size):
        """
        Update the solution array.

        Parameters
        ----------
        step_size : float
            Step size for determining next point in the solution.

        """
        if self.model.assortativity == 'positive':
            self.integrator.integrate(self.integrator.t - step_size)
            x, V = self.integrator.t, self.integrator.y
        else:
            self.integrator.integrate(self.integrator.t + step_size)
            x, V = self.integrator.t, self.integrator.y

        assert V[1] > 0.0, "Firm size should be non-negative!"

        # update the putative equilibrium solution
        wage = self.evaluate_wage(x, V)
        profit = self.evaluate_profit(x, V)
        step = np.hstack((x, V, wage, profit))
        self._solution = np.vstack((self._solution, step))

    @staticmethod
    def _validate_model(model):
        """Validate the model attribute."""
        if not isinstance(model, models.Model):
            mesg = ("Attribute 'model' must have type models.Model, not {}.")
            raise AttributeError(mesg.format(model.__class__))
        else:
            return model

    def _validate_solution(self, solution):
        """Validate a putative solution to the model."""
        check = np.apply_along_axis(self._check_pam, axis=1, arr=solution)
        if self.model.assortativity == 'positive' and (not check.all()):
            mesg = ("Approximated solution failed to satisfy required " +
                    "assortativity condition.")
            raise ValueError(mesg)
        elif self.model.assortativity == 'negative' and (check.all()):
            mesg = ("Approximated solution failed to satisfy required " +
                    "assortativity condition.")
            raise ValueError(mesg)
        else:
            pass

    def evaluate_input_types(self, x, V):
        r"""
        Numerically evaluate complementarity between input types.

        Parameters
        ----------
        x : float
            Value for worker skill (i.e., the independent variable).
        V : numpy.array (shape=(2,))
            Array of values for the dependent variables with ordering:
            :math:`[\mu, \theta]`.

        Returns
        -------
        input_types : float
            Complementarity between input types.

        """
        input_types = self._numeric_input_types(x, V, *self.model.params.values())
        return input_types

    def evaluate_jacobian(self, x, V):
        r"""
        Numerically evaluate model Jacobian.

        Parameters
        ----------
        x : float
            Value for worker skill (i.e., the independent variable).
        V : numpy.array (shape=(2,))
            Array of values for the dependent variables with ordering:
            :math:`[\mu, \theta]`.

        Returns
        -------
        jac : numpy.array (shape=(2,2))
            Jacobian matrix of partial derivatives.

        """
        jac = self._numeric_jacobian(x, V, *self.model.params.values())
        return jac

    def evaluate_profit(self, x, V):
        r"""
        Numerically evaluate profit for a firm with productivity V[0] and size
        V[1] when matched with a worker with skill x.

        Parameters
        ----------
        x : float
            Value for worker skill (i.e., the independent variable).
        V : numpy.array (shape=(2,))
            Array of values for the dependent variables with ordering:
            :math:`[\mu, \theta]`.

        Returns
        -------
        profit : float
            Firm's profit.

        """
        profit = self._numeric_profit(x, V, *self.model.params.values())
        assert profit > 0.0, "Profit should be non-negative!"
        return profit

    def evaluate_quantities(self, x, V):
        r"""
        Numerically evaluate quantities complementarity.

        Parameters
        ----------
        x : float
            Value for worker skill (i.e., the independent variable).
        V : numpy.array (shape=(2,))
            Array of values for the dependent variables with ordering:
            :math:`[\mu, \theta]`.

        Returns
        -------
        quantities : float
            Complementarity between quantities

        """
        quantities = self._numeric_quantities(x, V, *self.model.params.values())
        return quantities

    def evaluate_residual(self, x, k=3, ext=2):
        r"""
        The residual is the difference between the derivative of the B-spline
        approximation of the solution trajectory and the right-hand side of the
        original ODE evaluated along the approximated solution trajectory.

        Parameters
        ----------
        x : numpy.ndarray
            Array of values for worker skill at which to interpolate the
            value of the B-spline.
        k : int, optional(default=3)
            Degree of the desired B-spline. Degree must satisfy
            :math:`1 \le k \le 5`.
        ext : int, optional(default=2)
            Controls the value of returned elements for outside the
            original knot sequence provided by traj. For extrapolation, set
            `ext=0`; `ext=1` returns zero; `ext=2` raises a `ValueError`.

        Returns
        -------
        residual : numpy.ndarray
            An array containing the solution residuals.

        """
        # B-spline approximations of the solution and its derivative
        soln = self.interpolate(x, k, 0, ext)
        deriv = self.interpolate(x, k, 1, ext)

        # rhs of ode evaluated along approximate solution
        T = x.size
        rhs_ode = np.vstack(self.evaluate_rhs(x[i], soln[i, :]) for i in range(T))

        # should be roughly zero everywhere (if approximation is good!)
        residual = deriv - rhs_ode

        return residual

    def evaluate_rhs(self, x, V):
        r"""
        Numerically evaluate right-hand side of the system of ODEs.

        Parameters
        ----------
        x : float
            Value for worker skill (i.e., the independent variable).
        V : numpy.array (shape=(2,))
            Array of values for the dependent variables with ordering:
            :math:`[\mu, \theta]`.

        Returns
        -------
        rhs : numpy.array (shape=(2,))
            Right hand side of the system of ODEs.

        """
        rhs = self._numeric_system(x, V, *self.model.params.values()).ravel()
        return rhs

    def evaluate_type_resource(self, x, V):
        r"""
        Numerically evaluate complementarity between worker skill and
        firm resources.

        Parameters
        ----------
        x : float
            Value for worker skill (i.e., the independent variable).
        V : numpy.array (shape=(2,))
            Array of values for the dependent variables with ordering:
            :math:`[\mu, \theta]`.

        Returns
        -------
        resource : float
            Complementarity between worker skill and firm resources.

        """
        resource = self._numeric_type_resource(x, V, *self.model.params.values())
        return resource

    def evaluate_span_of_control(self, x, V):
        r"""
        Numerically evaluate span-of-control complementarity.

        Parameters
        ----------
        x : float
            Value for worker skill (i.e., the independent variable).
        V : numpy.array (shape=(2,))
            Array of values for the dependent variables with ordering:
            :math:`[\mu, \theta]`.

        Returns
        -------
        span_of_control : float
            Span-of-control complementarity.

        """
        span_of_control = self._numeric_span_of_control(x, V, *self.model.params.values())
        return span_of_control

    def evaluate_wage(self, x, V):
        r"""
        Numerically evaluate wage for a worker with skill level x when matched
        to a firm with productivity V[0] with size V[1].

        Parameters
        ----------
        x : float
            Value for worker skill (i.e., the independent variable).
        V : numpy.array (shape=(2,))
            Array of values for the dependent variables with ordering:
            :math:`[\mu, \theta]`.

        Returns
        -------
        wage : float
            Worker's wage.

        """
        wage = self._numeric_wage(x, V, *self.model.params.values())
        assert wage > 0.0, "Wage should be non-negative!"
        return wage

    def interpolate(self, x, k=3, der=0, ext=2):
        r"""
        Parametric B-spline interpolation of the model solution.

        Parameters
        ----------
        x : numpy.ndarray
            Values for worker skill (i.e., the independent variable) at which
            to interpolate the solution.
        k : int, optional(default=3)
            Degree of the desired B-spline. Degree must satisfy
            :math:`1 \le k \le 5`.
        der : int, optional(default=0)
            The order of derivative of the spline to compute (must be less
            than or equal to `k`).
        ext : int, optional(default=2) Controls the value of returned elements
            for outside the original knot sequence provided by traj. For
            extrapolation, set `ext=0`; `ext=1` returns zero; `ext=2` raises a
            `ValueError`.

        Returns
        -------
        interp_traj: ndarray (float)
            The interpolated trajectory.

        """
        # array of parameter values
        u = self.solution.index.values

        # build list of input arrays
        X = [self.solution['firm productivity'].values,
             self.solution['firm size'].values]

        # construct the B-spline representation (s=0 forces interpolation!)
        tck, t = interpolate.splprep(X, u=u, k=k, s=0)

        # evaluate the B-spline (returns a list)
        out = interpolate.splev(x, tck, der, ext)

        # convert to a 2D array
        interp_traj = np.array(out).T

        return interp_traj

    def solve(self, guess_firm_size_upper, tol=1e-6, number_knots=100,
              integrator='dopri5', message=False, **kwargs):
        """
        Solve for assortative matching equilibrium.

        Parameters
        ----------
        guess_firm_size_upper : float
            Upper bound on the range of possible values for the initial
            condition for firm size.
        tol : float (default=1e-6)
            Convergence tolerance.
        number_knots : int (default=100)
            Number of knots to use in approximating the solution. The number of
            knots determines the step size used by the ODE solver.
        integrator: string (default='dopri5')
            Integrator to use in appoximating the solution. Valid options are:
            'dopri5', 'lsoda', 'vode', 'dop853'. See `scipy.optimize.ode` for
            complete description of each solver.
        message : boolean (default=False)
            Flag indicating whether or not to print progress messages.
        **kwargs : dict
            Dictionary of optional, solver specific, keyword arguments. setter
            `scipy.optimize.ode` for details.

        Notes
        -----
        Rather than returning a result, this method modifies the `_solution`
        attribute of the `Solver` class. To final solution is stored as a
        `pandas.DataFrame` in the `solution` attribute.

        """

        # relevant bounds
        x_lower = self.model.workers.lower
        x_upper = self.model.workers.upper

        # initialize integrator
        self.integrator.set_integrator(integrator, **kwargs)

        # initialize the solution
        firm_size_lower = 0.0
        firm_size_upper = guess_firm_size_upper
        guess_firm_size = 0.5 * (firm_size_upper + firm_size_lower)
        self._reset_solution(guess_firm_size)

        # step size insures that never step beyond x_lower
        step_size = (x_upper - x_lower) / (number_knots - 1)
        assert step_size > 0

        while self.integrator.successful():

            if self._guess_firm_size_upper_too_low(guess_firm_size_upper, tol):
                if message:
                    mesg = ("Failure! Need to increase initial guess for " +
                            "upper bound on firm size!")
                    print(mesg)
                break

            self._update_solution(step_size)

            if self._converged_workers(tol) and self._converged_firms(tol):
                self._validate_solution(self._solution)
                mesg = "Success! All workers and firms are matched"
                print(mesg)
                break

            elif (not self._converged_workers(tol)) and self._exhausted_firms(tol):
                if message:
                    mesg = ("Exhausted firms: initial guess of {} for firm " +
                            "size is too low.")
                    print(mesg.format(guess_firm_size))
                firm_size_lower = guess_firm_size

            elif self._converged_workers(tol) and self._exhausted_firms(tol):
                if message:
                    mesg = ("Exhausted firms: Initial guess of {} for firm " +
                            "size was too low!")
                    print(mesg.format(guess_firm_size))
                firm_size_lower = guess_firm_size

            elif self._converged_workers(tol) and (not self._exhausted_firms(tol)):
                if message:
                    mesg = ("Exhausted workers: initial guess of {} for " +
                            "firm size is too high!")
                    print(mesg.format(guess_firm_size))
                firm_size_upper = guess_firm_size

            else:
                continue

            guess_firm_size = self._update_initial_guess(firm_size_lower,
                                                         firm_size_upper)
            self._reset_solution(guess_firm_size)
