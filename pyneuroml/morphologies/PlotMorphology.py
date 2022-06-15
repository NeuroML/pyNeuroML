
import argparse

import re

from matplotlib import pyplot as plt
from matplotlib import rcParams

DEFAULTS = {
    "v": False,
    }


def convert_case(name):
    """Converts from camelCase to under_score"""
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

def build_namespace(a=None, **kwargs):
    if a is None:
        a = argparse.Namespace()

    # Add arguments passed in by keyword.
    for key, value in kwargs.items():
        setattr(a, key, value)

    # Add defaults for arguments not provided.
    for key, value in DEFAULTS.items():
        if not hasattr(a, key):
            setattr(a, key, value)
    # Change all keys to camel case
    for key, value in a.__dict__.copy().items():
        new_key = convert_case(key)
        if new_key != key:
            setattr(a, new_key, value)
            delattr(a, key)
    return a

def process_args():
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description=(
            "A script which can generate plots of morphologies in NeuroML 2"
        )
    )

    parser.add_argument(
        "nmlFile",
        type=str,
        metavar="<NeuroML 2 file>",
        help="Name of the NeuroML 2 file",
    )

    parser.add_argument(
        "-v", action="store_true", default=DEFAULTS["v"], help="Verbose output"
    )


    return parser.parse_args()

def main(args=None):
    if args is None:
        args = process_args()
    run(a=args)

def run(a=None, **kwargs):
    a = build_namespace(a, **kwargs)

    if a.v:
        print("Plotting %s"%a.nml_file)

    from pyneuroml.pynml import read_neuroml2_file
    nml_model = read_neuroml2_file(a.nml_file)

    for cell in nml_model.cells:

        title = "2D plot of %s from %s"%(cell.id, a.nml_file)

        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.axis('equal')

        plt.get_current_fig_manager().set_window_title(title)
        #plt.title(title)

        for seg in cell.morphology.segments:

            p = cell.get_actual_proximal(seg.id)
            d = seg.distal
            if a.v:
                print('\nSegment %s, id: %s has proximal point: %s, distal: %s'%(seg.name, seg.id, p, d))
            width = max(p.diameter, d.diameter)
            plt.plot([p.x, d.x], [p.y,d.y], linewidth=width, color = 'b')


    plt.show()


if __name__ == "__main__":

    main()
