# Contributing

Please open issues to discuss enhancements and bugs that you may encounter with
pyNeuroML. Pull requests with enhancements and bug fixes are welcome.

## Virtual environments and editable installs

It is best to use [virtual environments](https://docs.python.org/3/tutorial/venv.html) when developing Python packages.
This ensures that one uses a clean environment that includes the necessary
dependencies and does not affect the overall system installation.

For quick development, consider using [editable installs](https://setuptools.pypa.io/en/latest/userguide/development_mode.html).

## Code style

1. We use [flake8](https://pypi.org/project/flake8/) to ensure that the code
   follows a consistent style as part of continuous integration on Travis.
   Currently, the information from flake8 is informative only.

2. The source code uses spaces, and each tab is equivalent to 4 spaces.

3. We use the [reStructuredText (reST)
   format](https://stackoverflow.com/a/24385103/375067) for Python docstrings.
   Please document your code when opening pull requests.

## Tests

Bug fixes and new features should include unit tests to test for correctness.
One can base new tests off the current ones included in the `tests/` directory.
To see how tests are run, please see the [GitHub Actions configuration file](https://github.com/NeuroML/pyNeuroML/blob/development/.github/workflows/ci.yml).

## Pull Request Process

1. Please contribute pull requests against the `development` branch.
2. Please ensure that the automated build for your pull request passes.
3. Please pay attention to the results from flake8 and make any modifications
   to ensure a consistent code style.

## Pre-commit

A number of [pre-commit](https://pre-commit.com/) hooks are used to improve code-quality.
Please run the following code to set up the pre-commit hooks:

    $ pre-commit install

## Commit messages

Writing good commit messages makes things easy to follow.
Please see these posts:

- [How to write a Git commit message](https://cbea.ms/git-commit/)
- While not compulsory, we prefer [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/)
