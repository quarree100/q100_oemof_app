"""
oemof application for research project quarree100

Copyright (c) 2018 Quarree100 AB-3 Project-Team

SPDX-License-Identifier: GPL-3.0-or-later
"""

import setup_solve_model
import postprocessing
import config as cfg
import os
import pprint as pp
from oemof.tools import logger
from oemof.tools import economics
import oemof.solph as solph
import oemof.outputlib as outputlib
import logging
import pandas as pd
import numpy as np
from customized import add_contraints
from matplotlib import pyplot as pltf   

# getting path to data from ini file
path_to_data = os.path.join(os.path.expanduser("~"),
                            cfg.get('paths', 'data'))

# getting path to data from IFAM owncloud
# path_to_data = 'ownCloud/FhG-owncloud-Quarree-AB3/oemof_AB1/Daten/'

path_to_results = os.path.join(os.path.expanduser("~"),
                               cfg.get('paths', 'results'))

filename = os.path.join(
    os.path.expanduser("~"), path_to_data, 'Parameter_AB1_dynamic.xlsx')

# reading data from excel file with data read function
node_data = setup_solve_model.nodes_from_excel(filename)

# setting up energy system
e_sys = setup_solve_model.setup_es(excel_nodes=node_data)

# optimising the energy system
# e_sys = setup_solve_model.solve_es(energysystem=e_sys, excel_nodes=node_data)

# ###########Optimise the energy system#######################################
logging.info('Optimise the energy system')

# initialise the operational model
om = solph.Model(e_sys)

# Global CONSTRAINTS: CO2 Limit
add_contraints.emission_limit_dyn(
    om, limit=node_data['general']['emission limit'][0])

logging.info('Solve the optimization problem')
# if tee_switch is true solver messages will be displayed
om.solve(solver='cbc', solve_kwargs={'tee': False})

logging.info('Store the energy system with the results.')
# add results to the energy system to make it possible to store them.
e_sys.results['main'] = outputlib.processing.results(om)
e_sys.results['meta'] = outputlib.processing.meta_results(om)

# store energy system with results
e_sys.dump(dpath=path_to_results, filename='results_val_1')

# plot the buses
postprocessing.plot_buses(res=e_sys.results['main'], es=e_sys)

# print the solver results
print('********* Meta results *********')
pp.pprint(e_sys.results['meta'])
print('')

def print_buses(res=None, es=None):

    l_buses = []

    for n in es.nodes:
        type_name =\
            str(type(n)).replace("<class 'oemof.solph.", "").replace("'>", "")
        if type_name == "network.Bus":
            l_buses.append(n.label)

    for n in l_buses:
        print(outputlib.views.node(res, n)['sequences'].sum(axis=0))

print_buses(res=e_sys.results['main'], es=e_sys)

SoC_sequences = outputlib.views.node(e_sys.results['main'], 'storage_heat')["sequences"]
SoC_sequences = SoC_sequences.drop(SoC_sequences.columns[[0, 2]], 1)
SoC_sequences.plot(kind='line', drawstyle="steps-mid", subplots=False,
                   sharey=True)
plt.show()

print('Total Emission [kg]')
print(om.total_emissions())

results = e_sys.results['main']
p_chp_gas = outputlib.views.node(results, 't_boiler')["scalars"][0]
print('Installierte Leistung Kessel [kW]:')
print(p_chp_gas)
p_chp_gas = outputlib.views.node(results, 't_wp_LW35')["scalars"][0]
print('Installierte t_wp_LW35 [kW]:')
print(p_chp_gas)
p_chp_gas = outputlib.views.node(results, 't_wp_W35W70')["scalars"][0]
print('Installierte t_wp_W35W70 [kW]:')
print(p_chp_gas)
p_chp_gas = outputlib.views.node(results, 't_bhkw')["scalars"][0]
print('Installierte t_bhkw [kW]:')
print(p_chp_gas)

p = outputlib.views.node(results, 'storage_heat')["scalars"][1]
print('Installierte Kapazität Wärmespeicher [kWh]:')
print(p)

# # plot the investments in transformer
# postprocessing.plot_trans_invest(res=results, es=e_sys)
#
# # plot the storage SoC(t)
# postprocessing.plot_storages_soc(res=results, es=e_sys)
#
# # plot the installed storage capacities
# postprocessing.plot_storages_invest(res=results, es=e_sys)
#
# # expoprt the results to excel
# postprocessing.export_excel(res=results, es=e_sys)
