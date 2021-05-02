# AshCalc

AshCalc is an easy-to-use tool that allows volcanologists to estimate the
volume of an eruption from isopach data describing the tephra deposits.
Volumes can be estimated using the exponential, power-law or Weibull models and
the results and quality of the fit can be plotted and compared.  For full
details, see the following (open access) paper:

> Daggitt ML, Mather TA, Pyle DM, Page S (2014) _AshCalc–a new tool
> for the comparison of the exponential, power-law and Weibull models
> of tephra deposition._
> Journal of Applied Volcanology 3:7. doi: [10.1186/2191-5040-3-7](http://www.appliedvolc.com/content/3/1/7)

AshCalc is distributed as a series of Python modules under the open source MIT
license. The software includes:
 
 * a graphical user interface
 * a command line interface
 * the Python source code for the calculations, which is extensible and should be easy to integrate into other projects.

![AshCalc graphical user interface](images/gui.png?raw=true "AshCalc graphical
interface")

For each model the outputs of AshCalc include:

 * Total estimated tephra volume
 * Model equations
 * Model error
 * Model parameters
 * Regression parameters (Exponential and Power law models).


## Setting up AshCalc

### Executables

Executables for Windows and Ubuntu are available from the [Releases](https://github.com/MatthewDaggitt/AshCalc/releases) page.

### Running from source

For detailed instructions, download the [AshCalc user
manual](http://static-content.springer.com/esm/art%3A10.1186%2F2191-5040-3-7/MediaObjects/13617_2013_13_MOESM3_ESM.docx).

AshCalc can be installed by downloading and unzipping onto a folder on your
local machine.  Alternatively, _git_ users can simply clone the repository as follows:

```bash
git clone https://github.com/MatthewDaggitt/AshCalc
```

AshCalc requires Python 3 and a number of additional packages (e.g. numpy).
The extra packages can be added to an existing Python 3 installation using
_pip_ by running the command below in the AshCalc directory:

```bash
pip install -r requirements.txt
```

The recommended method for a new installation of Python 3 is to use the [Anaconda Python distribution](https://www.continuum.io/downloads).  This is a free software package that contains all the necessary tools to use Python for scientific data analysis.  It is available for Windows, Mac and Linux and includes options for creating 'virtual environments' that allow specific versions of Python packages to be used for different projects.  The [AshCalc user manual](http://static-content.springer.com/esm/art%3A10.1186%2F2191-5040-3-7/MediaObjects/13617_2013_13_MOESM3_ESM.docx) describes how to set this up.


## Running AshCalc

AshCalc can be run by opening a terminal window in the AshCalc directory and
entering the following:

```bash
python3 ashcalc.py
```

This will open the graphical user interface, which allows interactive tweaking
of input parameters and visualisation of the output.  AshCalc also has
a command line interface.  This is useful for automatic processing of multiple
files.  Run the following to see instructions:

```bash
python3 ashcalc.py --help
```

The example command below will fit a 3-segment exponential model to all the
_csv_ files in the directory and creates plots of the fit.

```bash
python3 ashcalc.py *.csv --plot --model exponential --segments 3
```

Results are printed to the terminal and can be captured using the redirect
command.

```bash
python3 ashcalc.py *.csv > my_results.txt
```

## The VHub version of AshCalc

A cut-down version of AshCalc is also installed on [VHub](https://vhub.org/resources/ashcalc). It requires no download or setup, but it won't plot error surfaces for the Weibull model and has much coarser-grained controls.
