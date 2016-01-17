from textwrap import dedent
import numpy as np
import matplotlib.pyplot as plt
from core.isopach import Isopach
from core.models import exponential, weibull, power_law
from desktop import settings


class ModelSettings(object):
    """
    Provides interface for setting and providing preferred model and model
    settings.  Initial default values come from settings.py file.
    """
    def __init__(self):
        self.model = 'exponential'
        self.exp_segments = settings.EXP_DEFAULT_NUMBER_OF_SEGMENTS
        self.exp_max_segments = settings.EXP_MAX_NUMBER_OF_SEGMENTS
        self.pow_proximal_limit = settings.POW_DEFAULT_PROXIMAL_LIMIT
        self.pow_distal_limit = settings.POW_DEFAULT_DISTAL_LIMIT
        self.wei_number_of_runs = settings.WEI_DEFAULT_NUMBER_OF_RUNS
        self.wei_iterations_per_run = settings.WEI_DEFAULT_ITERATIONS_PER_RUN
        self.wei_lambda_lower_bound = settings.WEI_DEFAULT_LAMBDA_LOWER_BOUND
        self.wei_lambda_upper_bound = settings.WEI_DEFAULT_LAMBDA_UPPER_BOUND
        self.wei_k_lower_bound = settings.WEI_DEFAULT_K_LOWER_BOUND
        self.wei_k_upper_bound = settings.WEI_DEFAULT_K_UPPER_BOUND

    def set_model(self, model):
        """
        Set the model to use.
        """
        model = model.lower()
        model_names = ['weibull', 'power_law', 'exponential']
        if model not in model_names:
            raise ValueError('Model must be one of: {}'.format(
                             " ".join(model_names)))
        self.model = model

    def set_exponential_parameters(self, exp_segments):
        """
        Set the number of exponential segments (int).
        """
        if exp_segments > self.exp_max_segments:
            raise ValueError('Maximum number of segements is {}'.format(
                             self.exp_max_segments))
        self.exp_segments = exp_segments

    def set_power_law_parameters(self, proximalLimitKM, distalLimitKM):
        """
        Set the proximal and distal limits (in kilometers) of integration
        (float).
        """
        if (proximalLimitKM < 0) or (distalLimitKM < 0):
            raise ValueError('Distance limits must be greater than 0')
        self.pow_proximal_limit = proximalLimitKM
        self.pow_distal_limit = distalLimitKM

    def set_weibull_parameters(self, numberOfRuns, iterationsPerRun, limits):
        """
        Set the number of runs (int), iterations per run (int) and
        lower and upper bounds for lambda and k ((int, int), (int, int)).
        """
        if not (isinstance(limits[0], tuple) or
                isinstance(limits[1], tuple) or
                isinstance(limits, tuple)):
            raise ValueError('Bounds should have following form '
                             '((min_lambda, max_lambda), (min_k, max_k)).')
        self.wei_number_of_runs = numberOfRuns
        self.wei_iterations_per_run = iterationsPerRun
        self.wei_lambda_lower_bound = limits[0][0]
        self.wei_lambda_upper_bound = limits[0][1]
        self.wei_k_lower_bound = limits[1][0]
        self.wei_k_upper_bound = limits[1][1]

    def get_params(self):
        """
        Return list of appropriate parameters based on the chosen model
        setting.
        """
        if self.model == 'exponential':
            return [self.exp_segments]
        elif self.model == 'power_law':
            return [self.pow_proximal_limit, self.pow_distal_limit]
        elif self.model == 'weibull':
            limits = ((self.wei_lambda_lower_bound,
                       self.wei_lambda_upper_bound),
                      (self.wei_k_lower_bound,
                       self.wei_k_upper_bound))
            return [self.wei_number_of_runs, self.wei_iterations_per_run,
                    limits]

    def get_as_text(self):
        """
        Return pretty representation of settings values for use in plots or
        other outputs.
        """
        if self.model == 'exponential':
            text = """\
                Model: Exponential
                Number of segments: {}""".format(self.exp_segments)
        elif self.model == 'power_law':
            text = """\
                Model: Power Law
                Proximal limit: {}
                Distal limit: {}""".format(self.pow_proximal_limit,
                                           self.pow_distal_limit)
        elif self.model == 'weibull':
            text = """\
                Model: Weibull
                Number of runs: {}
                Iterations per run: {}
                Lambda bounds: {}, {}
                k bounds: {}, {}""".format(self.wei_number_of_runs,
                                           self.wei_iterations_per_run,
                                           self.wei_lambda_lower_bound,
                                           self.wei_lambda_upper_bound,
                                           self.wei_k_lower_bound,
                                           self.wei_k_upper_bound)
        return dedent(text)


def fit_isopachs(isopachs, model_settings):
    """
    ([list of Isopach], AshCalcModelSettings) -> dictionary of results.

    Runs the model to fit the isopachs and return the results.
    """
    params = model_settings.get_params()
    if model_settings.model == 'exponential':
        results = exponential.exponentialModelAnalysis(isopachs, *params)
    elif model_settings.model == 'power_law':
        results = power_law.powerLawModelAnalysis(isopachs, *params)
    elif model_settings.model == 'weibull':
        results = weibull.weibullModelAnalysis(isopachs, *params)
    return results


def load_isopachs(filename):
    """
    Read a list of isopachs from comma separated text file, with columns of
    thickness in metres, square root area in kilometres.

    :return list of Isopach objects:
    """
    isopachs = []
    with open(filename, 'r') as f:
        for line in f:
            thicknessM, sqrtAreaKM = line.split(',')
            isopachs.append(Isopach(float(thicknessM), float(sqrtAreaKM)))
    return isopachs


def create_results_plot(title, results, model_settings):
    """
    Plot log thickness versus square root area plot, with results and
    regression lines included.

    Returns figure object for further changes.
    """
    volume = results['estimatedTotalVolume']
    thickness_function = results['thicknessFunction']
    sqrt_area = np.array([isopach.sqrtAreaKM 
                          for isopach in results['isopachs']])
    thickness = np.array([isopach.thicknessM
                          for isopach in results['isopachs']])

    fig = plt.figure()
    plt.semilogy(sqrt_area, thickness, 'x')
    xmin, xmax = plt.xlim()
    area_values = np.linspace(xmin, xmax)
    plt.plot(area_values, thickness_function(area_values))
    plt.xlabel('Square root of area (km)')
    plt.ylabel('Thickness (m)')
    ax = plt.gca()
    text = model_settings.get_as_text()
    text += '\n\nVolume: {:.1f}'.format(volume)
    plt.text(0.05, 0.05, text, transform=ax.transAxes)
    plt.title(title)
    plt.savefig('test_{}.png'.format(model_settings.model))

