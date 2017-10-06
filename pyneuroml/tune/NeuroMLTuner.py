'''

    Still under developemnt!!

    Subject to change without notice!!

'''

from neurotune import optimizers
from neurotune import evaluators
from neurotune import utils
from matplotlib import pyplot as plt
from pyelectro import analysis

import os
import os.path
import time
import re

import argparse

from pyneuroml import pynml

import pprint
pp = pprint.PrettyPrinter(indent=4)

from collections import OrderedDict
from NeuroMLController import NeuroMLController


DEFAULTS = {'simTime':             500,
            'dt':                  0.025,
            'analysisStartTime':   0,
            'populationSize':      20,
            'maxEvaluations':      20,
            'numSelected':         10,
            'numOffspring':        20,
            'mutationRate':        0.5,
            'numElites':           1,
            'numParallelEvaluations':1,
            'cleanup':             True,
            'seed':                12345,
            'simulator':           'jNeuroML',
            'knownTargetValues':   '{}',
            'nogui':               False,
            'showPlotAlready':     True,
            'verbose':             False,
            'dryRun':              False,
            'extraReportInfo':     None} 
            
            
def process_args():
    """ 
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(
                description=("A script which can be run to tune a NeuroML 2 model against a number of target properties. Work in progress!"))

                        
    parser.add_argument('prefix', 
                        type=str,
                        metavar='<prefix>', 
                        help="Prefix for optimisation run")

    parser.add_argument('neuromlFile', 
                        type=str,
                        metavar='<neuromlFile>', 
                        help="NeuroML2 file containing model")

    parser.add_argument('target', 
                        type=str,
                        metavar='<target>', 
                        help="Target in NeuroML2 model")
                        
    parser.add_argument('parameters', 
                        type=str,
                        metavar='<parameters>', 
                        help="List of parameter to adjust")
                        
    parser.add_argument('maxConstraints', 
                        type=str,
                        metavar='<max_constraints>', 
                        help="Max values for parameters")
                        
    parser.add_argument('minConstraints', 
                        type=str,
                        metavar='<min_constraints>', 
                        help="Min values for parameters")
                        
    parser.add_argument('targetData', 
                        type=str,
                        metavar='<targetData>', 
                        help="List of name/value pairs for properties extracted from data to judge fitness against")
                        
    parser.add_argument('weights', 
                        type=str,
                        metavar='<weights>', 
                        help="Weights to assign to each target name/value pair")
                        
    parser.add_argument('-simTime', 
                        type=float,
                        metavar='<simTime>', 
                        default=DEFAULTS['simTime'],
                        help="Simulation duration")
                        
    parser.add_argument('-dt', 
                        type=float,
                        metavar='<dt>', 
                        default=DEFAULTS['dt'],
                        help="Simulation timestep")
                        
    parser.add_argument('-analysisStartTime', 
                        type=float,
                        metavar='<analysisStartTime>', 
                        default=DEFAULTS['analysisStartTime'],
                        help="Analysis start time")
                        
    parser.add_argument('-populationSize', 
                        type=int,
                        metavar='<populationSize>', 
                        default=DEFAULTS['populationSize'],
                        help="Population size")
                        
    parser.add_argument('-maxEvaluations', 
                        type=int,
                        metavar='<maxEvaluations>', 
                        default=DEFAULTS['maxEvaluations'],
                        help="Maximum evaluations")
                        
    parser.add_argument('-numSelected', 
                        type=int,
                        metavar='<numSelected>', 
                        default=DEFAULTS['numSelected'],
                        help="Number selected")
                        
    parser.add_argument('-numOffspring', 
                        type=int,
                        metavar='<numOffspring>', 
                        default=DEFAULTS['numOffspring'],
                        help="Number offspring")
                        
            
    parser.add_argument('-mutationRate', 
                        type=float,
                        metavar='<mutationRate>', 
                        default=DEFAULTS['mutationRate'],
                        help="Mutation rate")
                        
    parser.add_argument('-numElites', 
                        type=int,
                        metavar='<numElites>', 
                        default=DEFAULTS['numElites'],
                        help="Number of elites")
                        
    parser.add_argument('-numParallelEvaluations', 
                        type=int,
                        metavar='<numParallelEvaluations>', 
                        default=DEFAULTS['numParallelEvaluations'],
                        help="Number of evaluations to run in parallel")
                        
    parser.add_argument('-seed', 
                        type=int,
                        metavar='<seed>', 
                        default=DEFAULTS['seed'],
                        help="Seed for optimiser")
                        
    parser.add_argument('-simulator', 
                        type=str,
                        metavar='<simulator>', 
                        default=DEFAULTS['simulator'],
                        help="Simulator to run")
                        
    parser.add_argument('-knownTargetValues', 
                        type=str,
                        metavar='<knownTargetValues>', 
                        help="List of name/value pairs which represent the known values of the target parameters")
                        
    parser.add_argument('-nogui', 
                        action='store_true',
                        default=DEFAULTS['nogui'],
                        help="Should GUI elements be supressed?")
                        
    parser.add_argument('-showPlotAlready', 
                        action='store_true',
                        default=DEFAULTS['showPlotAlready'],
                        help="Should generated plots be suppressed until show() called?")
                        
    parser.add_argument('-verbose', 
                        action='store_true',
                        default=DEFAULTS['verbose'],
                        help="Verbose mode")
                        
    parser.add_argument('-dryRun', 
                        action='store_true',
                        default=DEFAULTS['dryRun'],
                        help="Dry run; just print setup information")
                        
    parser.add_argument('-extraReportInfo', 
                        type=str,
                        metavar='<extraReportInfo>', 
                        default=DEFAULTS['extraReportInfo'],
                        help='Extra tag/value pairs can be put into the report.json:  -extraReportInfo=["tag":"value"]')
                        
    parser.add_argument('-cleanup', 
                        action='store_true',
                        default=DEFAULTS['cleanup'],
                        help="Should (some) generated files, e.g. *.dat, be deleted as optimisation progresses?")
                        
    return parser.parse_args()
                       
                        
def run_optimisation(**kwargs): 
    a = build_namespace(**kwargs)
    return _run_optimisation(a)


def _run_optimisation(a):  
                         
                      
    if isinstance(a.parameters, str): a.parameters = parse_list_arg(a.parameters)
    if isinstance(a.min_constraints, str): a.min_constraints = parse_list_arg(a.min_constraints)
    if isinstance(a.max_constraints, str): a.max_constraints = parse_list_arg(a.max_constraints)
    if isinstance(a.target_data, str): a.target_data = parse_dict_arg(a.target_data)
    if isinstance(a.weights, str): a.weights = parse_dict_arg(a.weights)
    if isinstance(a.known_target_values, str): a.known_target_values = parse_dict_arg(a.known_target_values)
    if isinstance(a.extra_report_info, str): a.extra_report_info = parse_dict_arg(a.extra_report_info)
    
    pynml.print_comment_v("=====================================================================================")
    pynml.print_comment_v("Starting run_optimisation with: ")
    keys = sorted(a.__dict__.keys())
    
    for key in keys:
        value = a.__dict__[key]
        pynml.print_comment_v("  %s = %s%s"%(key,' '*(30-len(key)),value))
    pynml.print_comment_v("=====================================================================================")
    
    if a.dry_run: 
        pynml.print_comment_v("Dry run; not running optimization...")
        return
    
    ref = a.prefix
    
    run_dir = "NT_%s_%s"%(ref, time.ctime().replace(' ','_' ).replace(':','.' ))
    os.mkdir(run_dir)

    my_controller = NeuroMLController(ref, 
                                      a.neuroml_file, 
                                      a.target, 
                                      a.sim_time, 
                                      a.dt, 
                                      simulator = a.simulator, 
                                      generate_dir=run_dir,
                                      num_parallel_evaluations = a.num_parallel_evaluations,
                                      cleanup = a.cleanup)

    peak_threshold = 0

    analysis_var = {'peak_delta':     0,
                    'baseline':       0,
                    'dvdt_threshold': 0, 
                    'peak_threshold': peak_threshold}

    sim_var = OrderedDict()



    #make an evaluator, using automatic target evaluation:
    my_evaluator=evaluators.NetworkEvaluator(controller=my_controller,
                                            analysis_start_time=a.analysis_start_time,
                                            analysis_end_time=a.sim_time,
                                            parameters=a.parameters,
                                            analysis_var=analysis_var,
                                            weights=a.weights,
                                            targets=a.target_data)


    #make an optimizer
    my_optimizer = optimizers.CustomOptimizerA(a.max_constraints,
                                             a.min_constraints,
                                             my_evaluator,
                                             population_size = a.population_size,
                                             max_evaluations = a.max_evaluations,
                                             num_selected =    a.num_selected,
                                             num_offspring =   a.num_offspring,
                                             num_elites =      a.num_elites,
                                             mutation_rate =   a.mutation_rate,
                                             seeds =           None,
                                             verbose =         a.verbose)

    start = time.time()
    #run the optimizer
    best_candidate, fitness = my_optimizer.optimize(do_plot =     False, 
                                                    seed=         a.seed,
                                                    summary_dir = run_dir)

    secs = time.time()-start
    
    reportj = {}
    info = "Ran %s evaluations (pop: %s) in %f seconds (%f mins total; %fs per eval)\n\n"%(a.max_evaluations, a.population_size, secs, secs/60.0, (secs/a.max_evaluations))
    report = "----------------------------------------------------\n\n"+ info
             
             
    reportj['comment'] = info
    reportj['time'] = secs

    for key,value in zip(a.parameters,best_candidate):
        sim_var[key]=value


    best_candidate_t, best_candidate_v = my_controller.run_individual(sim_var, show=False, cleanup=False)

    best_candidate_analysis = analysis.NetworkAnalysis(best_candidate_v,
                                               best_candidate_t,
                                               analysis_var,
                                               start_analysis=a.analysis_start_time,
                                               end_analysis=a.sim_time)

    best_cand_analysis_full = best_candidate_analysis.analyse()
    best_cand_analysis = best_candidate_analysis.analyse(a.weights.keys())

    report+="---------- Best candidate ------------------------------------------\n"
    
    report+=pp.pformat(best_cand_analysis_full)+"\n\n"
    
    report+="TARGETS: \n"
    report+=pp.pformat(a.target_data)+"\n\n"
    report+="TUNED VALUES:\n"
    report+=pp.pformat(best_cand_analysis)+"\n\n"
    
    
    report+="FITNESS: %f\n\n"%fitness
    report+="FITTEST: %s\n\n"%pp.pformat(dict(sim_var))
    
    pynml.print_comment_v(report)
    
    reportj['fitness']=fitness
    reportj['fittest vars']=dict(sim_var)
    reportj['best_cand_analysis_full']=best_cand_analysis_full
    reportj['best_cand_analysis']=best_cand_analysis
    reportj['parameters']=a.parameters
    reportj['analysis_var']=analysis_var
    reportj['target_data']=a.target_data
    reportj['weights']=a.weights
    
    reportj['analysis_start_time']=a.analysis_start_time
    
    reportj['population_size']=a.population_size
    reportj['max_evaluations']=a.max_evaluations
    reportj['num_selected']=a.num_selected
    reportj['num_offspring']=a.num_offspring
    reportj['mutation_rate']=a.mutation_rate
    reportj['num_elites']=a.num_elites
    reportj['seed']=a.seed
    reportj['simulator']=a.simulator
    
    reportj['sim_time']=a.sim_time
    reportj['dt']=a.dt
    
    reportj['run_directory'] = run_dir
    reportj['reference'] = ref
    
    if a.extra_report_info:
        for key in a.extra_report_info:
            reportj[key] = a.extra_report_info[key]
    
    
    report_file = open("%s/report.json"%run_dir,'w')
    report_file.write(pp.pformat(reportj))
    report_file.close()
    
    plot_file = open("%s/plotgens.py"%run_dir,'w')
    plot_file.write('from neurotune.utils import plot_generation_evolution\nimport os\n')
    plot_file.write('\n')
    plot_file.write('parameters = %s\n'%a.parameters)
    plot_file.write('\n')
    plot_file.write("curr_dir = os.path.dirname(__file__) if len(os.path.dirname(__file__))>0 else '.'\n")
    plot_file.write("plot_generation_evolution(parameters, individuals_file_name = '%s/ga_individuals.csv'%curr_dir)\n")
    plot_file.close()

    if not a.nogui:
        added =[]
        #print("Plotting saved data from %s which are relevant for targets: %s"%(best_candidate_v.keys(), a.target_data.keys()))
        
        fig = plt.figure()
        fig.canvas.set_window_title("Simulation of fittest individual from run: %s"%ref)
        
        for tref in best_candidate_v.keys():  ##################a.target_data.keys():
            ref = tref.split(':')[0]
            if not ref in added:
                added.append(ref)
                #pynml.print_comment(" - Adding plot of: %s"%ref)
                plt.plot(best_candidate_t,best_candidate_v[ref], label="%s - %i evaluations"%(ref,a.max_evaluations))

        plt.legend()

        #plt.ylim(-80.0,80.0)
        plt.xlim(0.0,a.sim_time)
        plt.title("Models %s"%a.prefix)
        plt.xlabel("Time (ms)")
        plt.ylabel("Membrane potential(mV)")

        utils.plot_generation_evolution(sim_var.keys(), 
                                        individuals_file_name = '%s/ga_individuals.csv'%run_dir, 
                                        target_values=a.known_target_values,
                                        show_plot_already = a.show_plot_already,
                                        title_prefix=ref)
        
        if a.show_plot_already:
            plt.show()
    
    return reportj


def run_2stage_optimization(prefix, 
                            neuroml_file,
                            target,
                            parameters,
                            max_constraints_1,
                            max_constraints_2,
                            min_constraints_1,
                            min_constraints_2,
                            delta_constraints,
                            weights_1,
                            weights_2,
                            target_data_1,
                            target_data_2,
                            sim_time,
                            dt,
                            population_size_1,
                            population_size_2,
                            max_evaluations_1,
                            max_evaluations_2,
                            num_selected_1,
                            num_selected_2,
                            num_offspring_1,
                            num_offspring_2,
                            mutation_rate,
                            num_elites,
                            simulator,
                            nogui,
                            show_plot_already,
                            seed,
                            known_target_values,
                            dry_run = False,
                            extra_report_info = {},
                            num_parallel_evaluations = 1,
                            cleanup = True):

        mut_rat_1 = mutation_rate[0] if isinstance(mutation_rate, list) else mutation_rate
        
        report1 = run_optimisation(prefix = "%s_STAGE1"%prefix, 
                         neuroml_file =     neuroml_file,
                         target =           target,
                         parameters =       parameters,
                         max_constraints =  max_constraints_1,
                         min_constraints =  min_constraints_1,
                         weights =          weights_1,
                         target_data =      target_data_1,
                         sim_time =         sim_time,
                         dt =               dt,
                         population_size =  population_size_1,
                         max_evaluations =  max_evaluations_1,
                         num_selected =     num_selected_1,
                         num_offspring =    num_offspring_1,
                         mutation_rate =    mut_rat_1,
                         num_elites =       num_elites,
                         simulator =        simulator,
                         nogui =            nogui,
                         show_plot_already = False,
                         seed =             seed,
                         known_target_values = known_target_values,
                         dry_run =          dry_run,
                         extra_report_info = extra_report_info,
                         num_parallel_evaluations = num_parallel_evaluations,
                         cleanup = cleanup)
                         
        
        for pi in range(len(parameters)):
            param = parameters[pi]
            if max_constraints_2[pi] == 'x':
                max_constraints_2[pi] = report1['fittest vars'][param]*(1+delta_constraints)
            if min_constraints_2[pi] == 'x':
                min_constraints_2[pi] = report1['fittest vars'][param]*(1-delta_constraints)
                
        mut_rat_2 = mutation_rate[1] if isinstance(mutation_rate, list) else mutation_rate
               
        report2 = run_optimisation(prefix = "%s_STAGE2"%prefix, 
                         neuroml_file =     neuroml_file,
                         target =           target,
                         parameters =       parameters,
                         max_constraints =  max_constraints_2,
                         min_constraints =  min_constraints_2,
                         weights =          weights_2,
                         target_data =      target_data_2,
                         sim_time =         sim_time,
                         dt =               dt,
                         population_size =  population_size_2,
                         max_evaluations =  max_evaluations_2,
                         num_selected =     num_selected_2,
                         num_offspring =    num_offspring_2,
                         mutation_rate =    mut_rat_2,
                         num_elites =       num_elites,
                         simulator =        simulator,
                         nogui =            nogui,
                         show_plot_already = show_plot_already,
                         seed =             seed,
                         known_target_values = known_target_values,
                         dry_run =          dry_run,
                         extra_report_info = extra_report_info,
                         num_parallel_evaluations = num_parallel_evaluations) 
                
        
        return report1, report2
                         
        

        
def main(args=None):
    if args is None:
        args = process_args()
    run_optimisation(a=args)
    
    
'''
    Input:    string of form ["ADAL-AIBL":2.5,"I1L-I1R":0.5]
    returns:  {}
'''
def parse_dict_arg(dict_arg):
    if not dict_arg: return None
    ret = {}
    entries = str(dict_arg[1:-1]).split(',')
    for e in entries:
        if len(e) > 0:
            key = e[:e.rfind(':')]
            value = e[e.rfind(':')+1:]
            try:
                ret[key] = float(value)
            except: 
                ret[key] = value
    #print("Command line argument %s parsed as: %s"%(dict_arg,ret))
    return ret


def parse_list_arg(str_list_arg):
    if not str_list_arg: return None
    ret = []
    entries = str(str_list_arg[1:-1]).split(',')
    for e in entries:    
        try:
            ret.append(float(e))
        except ValueError:
            ret.append(e)
    #print("Command line argument %s parsed as: %s"%(str_list_arg,ret))
    return ret
    
    
def build_namespace(a=None,**kwargs):
    
    if a is None:
        a = argparse.Namespace()
    
    # Add arguments passed in by keyword.  
    for key,value in kwargs.items():
        setattr(a,key,value)
    
    # Add defaults for arguments not provided.  
    for key,value in DEFAULTS.items():
        new_key = convert_case(key)
        if not hasattr(a,key) and not hasattr(a,new_key):
            setattr(a,key,value)
    
    # Change all values to under_score from camelCase.  
    for key,value in a.__dict__.items():
        new_key = convert_case(key)
        if new_key != key:
            setattr(a,new_key,value)
            delattr(a,key)

    return a

def convert_case(name):
    """Converts from camelCase to under_score"""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

if __name__ == '__main__':
    main()

