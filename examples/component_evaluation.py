from pyneuroml import pynml

from matplotlib import pyplot as plt

def main(args=None):
    """Main"""
    
    vs = [(v-100)*0.001 for v in range(200)]
    nml_doc = pynml.read_neuroml2_file('../examples/IM.channel.nml')
    
    for ct in nml_doc.ComponentType:
        
        ys = []
        for v in vs:
            req_variables = {'v':'%sV'%v}
            vals = pynml.evaluate_component(ct,req_variables=req_variables)
            print vals
            if 'x' in vals:
                ys.append(vals['x'])
            if 't' in vals:
                ys.append(vals['t'])

        ax = pynml.generate_plot([vs],[ys],          
                         "Some traces from %s"%ct.name,
                         show_plot_already=False )       
                         
        print vals
        
    plt.show()

if __name__ == "__main__":
    main()
