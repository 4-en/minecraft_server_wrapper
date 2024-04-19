# setup.py

# Import required modules
from setuptools import setup, find_packages

# entry point:
# ./src/mcs_wrapper/wrapper.py main
entry_points = {
    'console_scripts': ['mcs_wrapper = mcs_wrapper.wrapper:main']
}

# Setup
setup(
    name='mcs_wrapper',
    version='0.1.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    entry_points=entry_points,
    install_requires=[
        'requests',
        'openai'
    ]
)