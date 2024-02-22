from __future__ import print_function
from matplotlib import pyplot as plt
from pyneuroml import pynml


def main(args=None):
    """Main"""

    vs = [(v - 100) * 0.001 for v in range(200)]

    for f in ["IM.channel.nml", "Kd.channel.nml"]:
        nml_doc = pynml.read_neuroml2_file(f)

        for ct in nml_doc.ComponentType:
            ys = []
            for v in vs:
                req_variables = {"v": "%sV" % v, "vShift": "10mV"}
                vals = pynml.evaluate_component(ct, req_variables=req_variables)
                print(vals)
                if "x" in vals:
                    ys.append(vals["x"])
                if "t" in vals:
                    ys.append(vals["t"])
                if "r" in vals:
                    ys.append(vals["r"])

            ax = pynml.generate_plot(
                [vs],
                [ys],
                "Some traces from %s in %s" % (ct.name, f),
                show_plot_already=False,
            )
            print(vals)

    plt.show()


if __name__ == "__main__":
    main()
