import argparse
import sys
from core import cli


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
    parser.add_argument('--segments', type=int,
            help='Number of segments to fit.  Used with exponential model.')
    parser.add_argument('--proximal_limit', type=float,
            help='Proximal limit of integration.  Used with power_law model')
    parser.add_argument('--distal_limit', type=float,
            help='Distal limit of integration.  Used with power_law model')
    parser.add_argument('--runs', type=int,
            help='Number of runs.  Used with weibull model')
    parser.add_argument('--iterations_per_run', type=int,
            help='Number of iterations per run.  Used with weibull model')
    parser.add_argument('--lambda_lower', type=float,
            help='Lambda parameter lower bound.  Used with weibull model')
    parser.add_argument('--lambda_upper', type=float,
            help='Lambda parameter upper bound.  Used with weibull model')
    parser.add_argument('--k_lower', type=float,
            help='k parameter lower bound.  Used with weibull model')
    parser.add_argument('--k_upper', type=float,
            help='k parameter upper bound.  Used with weibull model')
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
                   args.lambda_upper, args.k_lower, args.k_upper,
                   args.proximal_limit, args.distal_limit]
        if all_are_none(arglist):
            return
        elif none_are_none(arglist):
            model_settings.set_weibull_parameters(args.proximal_limit,
                                                  args.distal_limit)
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


if __name__ == '__main__':
    parser = setup_parser()
    args = parser.parse_args()

    # If no filenames are given, run the gui application
    if len(args.filelist) == 0:
        # Gui import is slow, so it is only done if we are going to use it.
        from desktop import gui
        ashcalc_application = gui.App()
        sys.exit()
    
    # Otherwise, prepare model settings then process the files.
    model_settings = cli.ModelSettings()
    set_model_settings_from_arguments(model_settings, args)
    for filename in args.filelist:
        isopachs = cli.load_isopachs(filename)
        results = cli.fit_isopachs(isopachs, model_settings)
        print('Filename: {}'.format(filename))
        print(model_settings.get_as_text())
        print('Volume: {:.2f}'.format(results['estimatedTotalVolume']))
