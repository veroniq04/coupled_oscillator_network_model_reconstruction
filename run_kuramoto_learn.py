# -*- coding: utf-8 -*-
"""
Created on Mon Sep 17 15:28:55 2018

@author: mpanaggio
"""

import learn_kuramoto_files as lk
import numpy as np
import importlib as imp
import pandas as pd
import time
imp.reload(lk)

##############################################################################
## define loop parameters

#loop_parameter='coupling_function' # choose from names of variables below
#loop_parameter_list=['lambda x: np.sin(x)', 
#                    'lambda x: np.sin(x-0.5)',
#                    'lambda x: np.sin(2*x)',
#                    'lambda x: np.sin(x-0.2)+0.1*np.cos(2*x)',
#                    'lambda x: np.sign(np.sin(x-0.5))',
#                    'lambda x: signal.sawtooth(2*x)'
#                    ]

loop_parameter='p_erdos_renyi' # choose from names of variables below
loop_parameter_list=[0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9] 

##############################################################################
## define file name
timestr = time.strftime("%Y%m%d-%H%M%S")
filename_suffix=str(loop_parameter) +'_sweep_'+ str(timestr)

##############################################################################
## define model parameters
num_osc=10
mu_freq=0.0  # mean natural frequency
sigma_freq=0.5 # std natural frequency
p_erdos_renyi=0.5  # probability of connection for erdos renyi
random_seed=-1 # -1 to ignore
coupling_function=lambda x: np.sin(x-0.1)  # Gamma from kuramoto model
#coupling_function=lambda x: np.sin(x-0.2)+0.1*np.cos(2*x) # Gamma from kuramoto model

##############################################################################
## define numerical solution parameters
dt=0.1     # time step for numerical solution
tmax=20.0    # maximum time for numerical solution
noise_level=0.0 # post solution noise added
num_repeats=10 # number of restarts for numerical solution
num_attempts=2 # number of times to attempt to learn from data for each network
num_networks=2 # number of different networks for each parameter value
method='euler' #'rk2','rk4','euler',
## Note: the  loop parameter value will overwrite the value above


##############################################################################
## initialize result dataframes
w_df=pd.DataFrame()
f_df=pd.DataFrame()
A_df=pd.DataFrame()
p_df=pd.DataFrame()
error_dict={}
##############################################################################
for k,parameter in zip(range(len(loop_parameter_list)),loop_parameter_list):
## save parameter
    exec(str(loop_parameter)+'='+str(parameter))
    
    for network in range(1,num_networks+1):
    ## create parameter dictionaries
        system_params={'w': lk.random_natural_frequencies(num_osc,mu=mu_freq,sigma=sigma_freq,seed=random_seed),
                'A': lk.random_erdos_renyi_network(num_osc,p_value=p_erdos_renyi,seed=random_seed),
                'K': 1.0,
                'Gamma': coupling_function
                }
        solution_params={'dt':dt,
                         'tmax':tmax,
                         'noise': noise_level,
                         'ts_skip': 1, # don't skip timesteps
                         'num_repeats': num_repeats
                         }
        
        learning_params={'learning_rate': 0.005,
                         'n_epochs': 400, #400
                         'batch_size':500,#500,
                         'n_oscillators':num_osc,
                         'dt': dt,
                         'n_coefficients': 20,
                         'reg':0.0001,
                         'prediction_method': method,
                         }
        
    ## generate training data
        old_phases,new_phases=lk.generate_data(system_params,
                                               solution_params)
        trainX1,trainX2,trainY,testX1,testX2,testY=lk.get_training_testing_data(
                old_phases,new_phases,split_frac=0.8)
    ## learn from data
        for attempt in range(1,num_attempts+1):
            print('******************************************************************')
            print("Loop parameter: "+str(loop_parameter))
            print("Current parameter value: "+str(parameter))
            print('')
            print('Parameter {} out of {}'.format(k+1,len(loop_parameter_list)))
            print('Network {} out of {}'.format(network,num_networks))
            print('Fit attempt {} out of {}'.format(attempt,num_attempts))
            print('')
            print('Now learning parameters:')
            predA,predw,fout,K,error_val=lk.learn_model(learning_params,trainX1,trainX2,trainY,testX1,testX2,testY)
            
            
        ## display results
            print_results=True
            show_plots=False
            w_res=lk.evaluate_w(predw,system_params, print_results=print_results)
            f_res=lk.evaluate_f(testX1,fout,K,system_params, print_results=print_results,show_plots=show_plots)
            A_res=lk.evaluate_A(predA,system_params, proportion_of_max=0.9,print_results=print_results,show_plots=show_plots)
            
            w_res=lk.add_run_info(w_res,['loop_parameter','parameter','attempt','network','method'],[loop_parameter,parameter,attempt,network,method])
            f_res=lk.add_run_info(f_res,['loop_parameter','parameter','attempt','network','method'],[loop_parameter,parameter,attempt,network,method])
            A_res=lk.add_run_info(A_res,['loop_parameter','parameter','attempt','network','method'],[loop_parameter,parameter,attempt,network,method])
        ## save all run information
            p_res=lk.add_run_info(pd.Series(),system_params.keys(),system_params.values(),to_str=True)
            p_res=lk.add_run_info(p_res,solution_params.keys(),solution_params.values())
            p_res=lk.add_run_info(p_res,learning_params.keys(),learning_params.values())
            p_res=lk.add_run_info(p_res,['loop_parameter','parameter','attempt','network','method'],[loop_parameter,parameter,attempt,network,method])
        ## save results to dataframe
            w_df[str(loop_parameter)+' = '+ str(parameter) + ', network ' + str(network) + ', run =' + str(attempt)]=w_res
            f_df[str(loop_parameter)+' = '+ str(parameter) + ', network ' + str(network) + ', run =' + str(attempt)]=f_res
            A_df[str(loop_parameter)+' = '+ str(parameter) + ', network ' + str(network) + ', run =' + str(attempt)]=A_res
            p_df[str(loop_parameter)+' = '+ str(parameter) + ', network ' + str(network) + ', run =' + str(attempt)]=p_res
            error_dict[str(loop_parameter)+' = '+ str(parameter) + ', network ' + str(network) + ', run =' + str(attempt)]=error_val
    ##############################################################################
    ## save results to ssv
        w_df.to_excel('frequency_results_'+ filename_suffix+'.xlsx')
        f_df.to_excel('coupling_function_results_'+ filename_suffix +'.xlsx')
        A_df.to_excel('adjacency_matrix_results_'+ filename_suffix +'.xlsx')
        p_df.to_excel('parameter_information_'+ filename_suffix +'.xlsx')
        pd.DataFrame(pd.Series(error_dict)).T.to_csv('validation_error_results_'+ filename_suffix +'.xlsx')
