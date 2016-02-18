# -- coding: utf-8 --
import argparse
import json
from textwrap import dedent
import numpy as np
import matplotlib.pyplot as plt
from core.models import exponential, weibull, power_law
import settings


def setup_parser():
    parser = argparse.ArgumentParser(
        description='Calculate tephra volumes from isopach data using '
                    'exponential, power law or Weibull models.')
    parser.add_argument(
        '--model', type=str, default='exponential',
        choices=['exponential', 'power_law', 'weibull'],
        help='Model used to fit root-area vs thickness curve.')
    # It is possible to set defaults for all the values here, but this is not
    # done as it is preferable to get them from the settings file.
    parser.add_argument(
        'filelist', type=str, nargs='*', default=None, metavar='filename',
        help='CSV file containing thickness versus square root area data.')
    parser.add_argument(
        '--segments', type=int,
        help='Number of segments to fit.  Used with exponential model.')
    parser.add_argument(
        '--proximal_limit', type=float,
        help='Proximal limit of integration.  Used with power_law model')
    parser.add_argument(
        '--distal_limit', type=float,
        help='Distal limit of integration.  Used with power_law model')
    parser.add_argument(
        '--runs', type=int,
        help='Number of runs.  Used with weibull model')
    parser.add_argument(
        '--iterations_per_run', type=int,
        help='Number of iterations per run.  Used with weibull model')
    parser.add_argument(
        '--lambda_lower', type=float,
        help='Lambda parameter lower bound.  Used with weibull model')
    parser.add_argument(
        '--lambda_upper', type=float,
        help='Lambda parameter upper bound.  Used with weibull model')
    parser.add_argument(
        '--k_lower', type=float,
        help='k parameter lower bound.  Used with weibull model')
    parser.add_argument(
        '--k_upper', type=float,
        help='k parameter upper bound.  Used with weibull model')
    parser.add_argument(
        '--plot', action='store_true',
        help='Plot the results as *filename_model.png*')
    parser.add_argument(
        '--json', action='store_true',
        help='Print the results formatted as json')
    return parser


def set_model_settings_from_arguments(model_settings, args):
    """
    Use command line arguments to set model parameters.  If no parameters are
    given, use defaults.  If all are given for model, use all.  If some are
    given, return an error.
    """
    model_settings.set_model(args.model)

    if args.model == 'exponential':
        if args.segments is None:
            return
        else:
            model_settings.set_exponential_parameters(args.segments)
    elif args.model == 'power_law':
        arglist = [args.proximal_limit, args.distal_limit]
        if all_are_none(arglist):
            return
        elif none_are_none(arglist):
            model_settings.set_power_law_parameters(args.proximal_limit,
                                                    args.distal_limit)
        else:
            raise ValueError(
                'Bad parameters.  Set all parameters or set none.')
    elif args.model == 'weibull':
        arglist = [args.runs, args.iterations_per_run, args.lambda_lower,
                   args.lambda_upper, args.k_lower, args.k_upper]
        if all_are_none(arglist):
            return
        elif none_are_none(arglist):
            model_settings.set_weibull_parameters(
                args.runs, args.iterations_per_run,
                ((args.lambda_lower, args.lambda_upper),
                 (args.k_lower, args.k_upper)))

        else:
            raise ValueError(
                'Bad parameters.  Set all parameters or set none.')


def none_are_none(arglist):
    for arg in arglist:
        if arg is None:
            return False
    return True


def all_are_none(arglist):
    for arg in arglist:
        if arg is not None:
            return False
    return True


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

    def get_as_dict(self):
        """
        Return model settings as a dictionary.
        """
        settings = {'model': self.model,
                    'exp_segments': self.exp_segments,
                    'exp_max_segments': self.exp_max_segments,
                    'pow_proximal_limit': self.pow_proximal_limit,
                    'pow_distal_limit': self.pow_distal_limit,
                    'wei_number_of_runs': self.wei_number_of_runs,
                    'wei_iterations_per_run': self.wei_iterations_per_run,
                    'wei_lambda_lower_bound': self.wei_lambda_lower_bound,
                    'wei_lambda_upper_bound': self.wei_lambda_upper_bound,
                    'wei_k_lower_bound': self.wei_k_lower_bound,
                    'wei_k_upper_bound': self.wei_k_upper_bound}
        settings_used_by_models = {'exponential': ['exp_segments',
                                                   'exp_max_segments'],
                                   'power_law': ['pow_proximal_limit',
                                                 'pow_distal_limit'],
                                   'weibull': ['wei_lambda_upper_bound',
                                               'wei_lambda_upper_bound',
                                               'wei_k_upper_bound',
                                               'wei_k_upper_bound']}

        # Drop unused settings
        settings_used = settings_used_by_models[self.model]
        all_settings = settings.keys()
        settings_to_drop = [s for s in all_settings if s not in settings_used]
        for setting in settings_to_drop:
            settings.pop(setting)

        return settings


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


def plot_results_figure(filename, results, model_settings, comments):
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

    # Plot data
    fig = plt.figure()
    plt.semilogy(sqrt_area, thickness, 'x')

    # Plot fitted curve
    xmin, xmax = plt.xlim()

    if model_settings.model == 'power_law':
        model_sqrt_area = np.linspace(model_settings.pow_proximal_limit,
                                      model_settings.pow_distal_limit)
        # Divide by root of pi (see power_law.pi for details)
        model_sqrt_area = model_sqrt_area * np.sqrt(np.pi)
    else:
        model_sqrt_area = np.linspace(xmin, xmax)

    model_thickness = [thickness_function(x) for x in model_sqrt_area]
    plt.semilogy(model_sqrt_area, model_thickness, '-r')

    # Label with axes, title and text model description
    plt.xlabel('Square root of area (km)')
    plt.ylabel('Thickness (m)')
    title = '\n'.join(comments)
    plt.title(title)
    ax = plt.gca()
    text = model_settings.get_as_text()
    text += '\n\nVolume: {:.1f} km3'.format(volume)
    plt.text(0.05, 0.05, text, transform=ax.transAxes)

    plt.savefig('{}_{}.png'.format(filename.replace('.csv', ''),
                                   model_settings.model))


def print_output(filename, results, model_settings, comments):
    """
    Format output and print to screen.
    """
    print('Filename: {}'.format(filename))

    for i, comment in enumerate(comments):
        print('Comment {}: {}'.format(i + 1, comment))

    print(model_settings.get_as_text())
    print(format_results_by_model(results, model_settings.model))


def print_json_output(filename, results, model_settings, comments):
    """
    Format output as json and print to screen.
    """
    all_results = results.copy()

    # Remove results that do not serialize to json
    for key in ['isopachs', 'thicknessFunction']:
        all_results.pop(key)

    all_results.update({'filename': filename,
                        'comments': comments})
    all_results.update(model_settings.get_as_dict())

    print(json.dumps(all_results, sort_keys=True, indent=4,
          separators=(',', ': ')))


def format_results_by_model(results, model):
    """
    Format results dictionary to print different calculated model parameters,
    depending on model used.

    :return Multiline string of model parameter name: values.
    """
    text = ''
    if model == 'exponential':
        for i in range(results['numberOfSegments']):
            text += 'Segment {} Bt: {:.3f}\n'.format(
                    i, results['segmentBts'][i])
            text += 'Segment {} Coefficient: {:.3f}\n'.format(
                    i, results['segmentCoefficients'][i])
            text += 'Segment {} Exponent: {:.3f}\n'.format(
                    i, results['segmentExponents'][i])
            text += 'Segment {} Limit: {:.3f}\n'.format(
                    i, results['segmentLimits'][i + 1])
            text += 'Segment {} Volume: {:.1f}\n'.format(
                    i, results['segmentVolumes'][i])
    elif model == 'power_law':
        text += 'Coefficient: {:.3f}\n'.format(results['coefficient'])
        text += 'Exponent: {:.3f}\n'.format(results['exponent'])
        text += 'Suggested Proximal Limit: {:.1f}\n'.format(
                results['suggestedProximalLimit'])
    elif model == 'weibull':
        text += 'k: {:.3f}\n'.format(results['k'])
        text += 'lambda: {:.0f}\n'.format(results['lambda'])
        text += 'theta: {:.5f}\n'.format(results['theta'])

    text += 'MRSE of fit: {:.03f}\n'.format(results['mrse'])
    text += 'Total Volume: {:.2f}\n'.format(results['estimatedTotalVolume'])
    return text
