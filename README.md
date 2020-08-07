After cloning this repository on your local machine, please follow the following step in order for the script to work correctly.
This steps only assume that you have a working version of Python 3 installed on your local machine.
In order to follow, open the terminal and move to the project's directory 

1. Create a virtual environment 

(for Linux and macOS)

python3 -m pip install --user --upgrade pip
python3 -m pip install --user virtualenv
python3 -m venv DataCollector_environment

(for Windows)

py -m pip install --upgrade pip
py -m pip install --user virtualenv
py -m venv DataCollector_environment

2. Activate the virtual environment 

(for Linux and macOS)

source DataCollector_environment/bin/activate

(for Windows)

.\DataCollector_environment\Scripts\activate

3. Install the required libraries

pip install -r requirements.txt

