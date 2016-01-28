import sys
from core import isopach_file
from command_line import cli

if __name__ == '__main__':
    parser = cli.setup_parser()
    args = parser.parse_args()

    # If no filenames are given, run the gui application
    if len(args.filelist) == 0:
        # Gui import is slow, so it is only done if we are going to use it.
        from desktop import gui
        ashcalc_application = gui.App()
        sys.exit()

    # Otherwise, prepare model settings then process the files.
    model_settings = cli.ModelSettings()
    cli.set_model_settings_from_arguments(model_settings, args)
    for filename in args.filelist:
        isopachs, comments = isopach_file.read(filename)
        results = cli.fit_isopachs(isopachs, model_settings)
        cli.print_output(filename, results, model_settings, comments)
