# Contributing

Please open issues to discuss enhancements and bugs that you may encounter with
pyNeuroML. Pull requests with enhancements and bug fixes are welcome.

## Code style

1. We use [flake8](https://pypi.org/project/flake8/) to ensure that the code
   follows a consistent style as part of continuous integration on Travis.
   Currently, the information from flake8 is informative only.

2. The source code uses spaces, and each tab is equivalent to 4 spaces.

3. We use the [reStructuredText (reST)
   format](https://stackoverflow.com/a/24385103/375067) for Python docstrings.
   Please document your code when opening pull requests.

## Pull Request Process

1. Please contribute pull requests against the `development` branch.
2. Please ensure that the automated build for your pull request passes.
3. Please pay attention to the results from flake8 and make any modifications
   to ensure a consistent code style.

## Pre-commit

A number of [pre-commit](https://pre-commit.com/) hooks are used to improve code-quality.
Please run the following code to set up the pre-commit hooks:

    $ pre-commit install
