import sympy as sp
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from scipy import stats

import eeckhoutKircher2013

def A(x, y, params):
    """Inner production function.

    Arugments:

        x: Worker type.
        y: Firm type.

    """ 
    sigma_A = params['sigma_A']
    omega_A = params['omega_A']
    
    if sigma_A == 1.0:
        out = x**omega_A * y**(1 - omega_A)
    else:
        out = ((omega_A * x**((sigma_A - 1) / sigma_A) + 
               (1 - omega_A) * y**((sigma_A - 1) / sigma_A))**(sigma_A / (sigma_A - 1))) 
    return out
 
def B(l, r, params):
    """Inner production function.
    
    Arguments:

        l: Quantity of labor of type x.
        r: Fraction of proprietary resources devoted to a worker
           with type x (can be normalized to unity for convenience).

    """ 
    sigma_B = params['sigma_B']
    omega_B = params['omega_B']
    
    if sigma_B == 1.0:
        out = l**omega_B * r**(1 - omega_B)
    else:
        out = ((omega_B * l**((sigma_B - 1) / sigma_B) + 
               (1 - omega_B) * r**((sigma_B - 1) / sigma_B))**(sigma_B / (sigma_B - 1)))
    return out

def F(x, y, l, r, params):
    """Nested CES version of production technology.

    Arguments:

        x:      worker type
        y:      firm type
        l:      quantity of labor of type x
        r:      fraction of proprietary resources devoted to a worker
                with type x (can be normalized to unity for convenience)
  
    The first two arguments x and y are quality variables describing 
    the worker and firm types, while the latter two aruments are 
    quantity variables describing the level of inputs.

    """
    # extract params
    alpha  = params['alpha']
    beta   = params['beta']
    
    return A(x, y, params)**alpha * B(l, r, params)**beta
        
########## Suppose more workers than firms, vary sigma_A ##########

# initial model parameters
params = {'omega_A':0.5, 'omega_B':0.5, 'sigma_A':0.5, 'sigma_B':1.0, 
          'alpha':1.0, 'beta':1.0}

# describe the workers
mu, sigma = 0, 1
worker_types = stats.lognorm(sigma, scale=np.exp(mu)) 
x_lower = worker_types.ppf(0.01) 
x_upper = worker_types.ppf(0.99)
x_measure = 1
workers = eeckhoutKircher2013.Workers(worker_types, x_lower, x_upper, x_measure)

# describe the firms
firm_prods = stats.lognorm(sigma, scale=np.exp(mu)) 
y_lower = firm_prods.ppf(0.01)
y_upper = firm_prods.ppf(0.99)
y_measure = x_measure / 2.0
firms = eeckhoutKircher2013.Firms(firm_prods, y_lower, y_upper, y_measure)

# create an object representing the model
model = eeckhoutKircher2013.Model(params, workers, firms, F)

# want to solve for equilibrium for different values of sigma_A
sigma_As = [0.5] #[0.05, 0.25, 0.5, 0.75, 0.95]

# create an empty dictionary in which to store output
sigma_A_dict = {}

for val in sigma_As:
    # change value of the parameter sigma_A
    model.param_dict['sigma_A'] = val
    
    # recompute partial derivatives
    model.derivatives_dict = model.compute_partialDerivatives()
    
    # dictionary of keyword arguments to pass to solver
    kwargs = {'max_order_ns':12, 'max_order_s':5, 'with_jacobian':False}

    # compute the equilibrium
    model.solve_forwardShoot(5e0, 0, h=1e-3, tol=1.5e-3, mesg=True, pandas=True,
                             max_iter=1e6, integrator='lsoda', **kwargs)

    # use sigma_A value as dict key!
    sigma_A_dict[val] = model.equilibrium
    
    print 'Done with sigma_A =', val
    
##### Plot the results #####

fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(12, 12))
fig.subplots_adjust(top=0.9)

# plot model equilibrium
tmp_data = model.equilibrium

# generate the plots
axes[0,0].plot(tmp_data['$\\mu(x)$'], tmp_data['$\\theta(x)$'], color='r')
axes[0,1].plot(tmp_data.index, tmp_data['$\\mu(x)$'], color='r')
axes[1,0].plot(tmp_data['$\\mu(x)$'], tmp_data['Profits, $\\pi(\\mu(x))$'], color='r')
axes[1,1].plot(tmp_data.index, tmp_data['Wages, $w(x)$'], color='r')

# set plot options
axes[0,0].set_xlabel('Firm productivity, $y$')
axes[0,0].set_xlim(y_lower, y_upper)
axes[0,0].set_ylabel(r'$\theta(y)$', rotation='horizontal', fontsize=15)
axes[0,0].set_ylim(0, 10)
axes[0,0].grid()

axes[0,1].set_xlabel('Worker type, $x$')
axes[0,1].set_xlim(x_lower, x_upper)
axes[0,1].set_ylabel(r'$\mu(x)$', rotation='horizontal', fontsize=15)
axes[0,1].grid()

axes[1,0].set_xlabel('Firm productivity, $y$')
axes[1,0].set_xlim(y_lower, y_upper)
axes[1,0].set_ylabel(r'$\pi(y)$', rotation='horizontal', fontsize=15)
axes[1,0].grid()

axes[1,1].set_xlabel('Worker type, $x$')
axes[1,1].set_xlim(x_lower, x_upper)
axes[1,1].set_ylabel(r'$w(x)$', rotation='horizontal', fontsize=15)
axes[1,1].grid()

fig.suptitle(r'Equilibria when firm productivity and worker type are $U\sim[%i,%i]$, $\sigma_A=%.2f$, and $\omega_B=%.1f$' 
             %(x_lower, x_upper, params['sigma_A'], params['omega_B']), y=0.925, fontsize=15)
plt.show()