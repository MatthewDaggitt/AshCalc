# AshCalc

AshCalc is a series of python modules for calculating the three most common models for estimating the volume of tephra deposits:

 * the Exponential model
 * the Power law model
 * the Weibull model
 
Daggit, Mather, Pyle and Page have published a  [paper](http://www.appliedvolc.com/content/3/1/7) on AshCalc in the Journal of Applied Volconology describing it in further detail, as well as demonstrating that it accurately produces previously published results from publically available data.

The aim of AshCalc is to be an easy-to-use tool distributed
under an open source license for volcanologists to compare
the suitability of the three models for their data. AshCalc
consists of:
 
 * a graphical user interface
 * a command line interface
 * the python source code for the calculations, which is extensible and should be easy to integrate into other projects.

![AshCalc graphical user interface](/images/gui.jpg?raw=true "Optional Title")

For each model the outputs of AshCalc include:

 * Total estimated tephra volume
 * Model equations
 * Model error
 * Model parameters
 * Regression parameters (Exponential and Power law models).



## Setting up AshCalc

AshCalc can be installed by cloning the repository into a folder locally. 

```bash
git clone https://github.com/MatthewDaggitt/AshCalc
```
Two options exist to install the requirements. Either the required Python3 modules (numpy, scipy etc.) can be installed using "pip":

```bash
pip install -r requirements.txt
```
Or you can download a full Python stack such as Anaconda. This may be a better alternative if on Windows.

TO-DO A brief description of getting Anaconda up and running


## Running AshCalc

After navigating to the AshCalc folder, the program can be run as follows from a terminal:

```bash
python3 ashcalc.py
```

If no further arguments are passed to the program then the graphical user interface will start by default. Otherwise the command-line tool will process the arguments and provide output directly to the terminal.

TO-DO: Describe the workings of the command-line tool.

## The VHub version of AshCalc

For those struggling to setup AshCalc, there is also a cut-down version of AshCalc available on [VHub](https://vhub.org/resources/ashcalc). It has the advantage that it requires no download or setup, but it won't plot error surfaces for the Weibull model and has much coarser-grained controls.