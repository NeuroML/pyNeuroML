# Contributing

Please open issues to discuss enhancements and bugs that you may encounter with
pyNeuroML. Pull requests with enhancements and bug fixes are welcome.

## Virtual environments and editable installs

It is best to use [virtual environments](https://docs.python.org/3/tutorial/venv.html) when developing Python packages.
This ensures that one uses a clean environment that includes the necessary
dependencies and does not affect the overall system installation.

For quick development, consider using [editable installs](https://setuptools.pypa.io/en/latest/userguide/development_mode.html).

PyNeuroML includes a number of scripts that provide the various command line tools.
When making changes to the code, one must re-install the package to ensure that
these command line tools are up to date:


    pip install -e .   # for an editable install


The dependencies are broken down in the `setup.cfg` file. To get a complete development environment, one can run:


    pip install -e .[dev]   # an editable install with all development dependecies installed


## Code style

1. The source code uses spaces, and each tab is equivalent to 4 spaces.

2. We use the [reStructuredText (reST)
   format](https://stackoverflow.com/a/24385103/375067) for Python docstrings.
   Please document your code when opening pull requests.
   All methods/functions/modules *must* include docstrings that explain the parameters.

3. We use [ruff](https://pypi.org/project/ruff/) to format and lint our code. (See the section on pre-commit below.)

4. Please use [type hints](https://docs.python.org/3/library/typing.html) wherever applicable.
   You can set up type checkers such as [mypy](https://mypy.readthedocs.io/) to use type hints in your development environment/IDE.


        pip install mypy


### Pre-commit

A number of [pre-commit](https://pre-commit.com/) hooks are used to improve code-quality.
Please run the following code to set up the pre-commit hooks:

    $ pre-commit install

The hooks will be run at each `git commit`.
Please see `.pre-commit-config.yaml` for information on what hooks we run.


### Commit messages

Writing good commit messages makes things easy to follow.
Please see these posts:

- [How to write a Git commit message](https://cbea.ms/git-commit/)
- While not compulsory, we prefer [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/)


## Tests

Bug fixes and new features should include unit tests to test for correctness.
One can base new tests off the current ones included in the `tests/` directory.
To see how tests are run, please see the [GitHub Actions configuration file](https://github.com/NeuroML/pyNeuroML/blob/development/.github/workflows/ci.yml).

We use [pytest](https://docs.pytest.org/) for unit testing.
One can run it from the root of the repository:

    pytest


To run specific tests, one can use the `-k` flag:


    pytest -k "..."


## Pull Request Process

1. Please contribute pull requests against the `development` branch.
2. Please ensure that the automated build for your pull request passes.
3. Please write good commit messages (see the section above).

### Updating your pull request branch

Over time, as pull requests are reviewed, the `development` branch continues to move on with other changes.
Sometimes, it can be useful/necessary to pull in these changes to the pull request branch, using the following steps.

Add the upstream pyNeuroML repository as a remote:


    git remote add upstream https://github.com/NeuroML/pyNeuroML.git


Update your local copy of the `development` branch, and the remote copy in your fork:


    git checkout development
    git pull upstream development
    git push


Pull in changes from development to your branch:


    git checkout <feature branch being used for PR>
    git merge development


If there are merge conflicts, you will need to [resolve these](https://git-scm.com/book/en/v2/Git-Branching-Basic-Branching-and-Merging#_basic_merge_conflicts), since merging the feature branch in the pull request will also result in these.
After any merge conflicts have been resolved (or if there aren't any), you can
push your branch to your fork to update the pull request:


    git push

## Man pages

We auto-generate [man pages](https://en.wikipedia.org/wiki/Man_page) for all
the command line tools using
[help2man](https://directory.fsf.org/wiki/Help2man).  To regenerate these:

    pip install -e . # ensure latest version of package tools are installed
    cd man/man1/
    ./generate-man-pages.sh

One can preview the man pages:

    man -l <path to man page file>

If all looks well, check in the man pages and commit:

    git add .
