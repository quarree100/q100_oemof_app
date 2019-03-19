"""
oemof application for research project quarree100

Copyright (c) 2018 Quarree100 AB-3 Project-Team

SPDX-License-Identifier: GPL-3.0-or-later
"""

import setup_solve_model
import postprocessing
import graph_model
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
from matplotlib import pyplot as plt

# getting path to data from ini file
path_to_data = os.path.join(os.path.expanduser("~"),
                            cfg.get('paths', 'data'))

# getting path to data from IFAM owncloud
# path_to_data = 'ownCloud/FhG-owncloud-Quarree-AB3/oemof_AB1/Daten/'

# path_to_results = os.path.join(os.path.expanduser("~"),
#                             cfg.get('paths', 'results'))

filename = os.path.join(
    os.path.expanduser("~"), path_to_data, 'Parameter_AB1_dynamic.xlsx')

# reading data from excel file with data read function
node_data = setup_solve_model.nodes_from_excel(filename)

# setting up energy system
e_sys = setup_solve_model.setup_es(excel_nodes=node_data)


'''

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
om.solve(solver='cbc', solve_kwargs={'tee': True})

logging.info('Store the energy system with the results.')
# add results to the energy system to make it possible to store them.
e_sys.results['main'] = outputlib.processing.results(om)
e_sys.results['meta'] = outputlib.processing.meta_results(om)

# store energy system with results
# e_sys.dump(dpath=path_to_results, filename='test_results')

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

print('Total Emission [kg]')
print(om.total_emissions())
# plot the investments in transformer
# postprocessing.plot_trans_invest(res=results, es=e_sys)

# plot the storage SoC(t)
# postprocessing.plot_storages_soc(res=results, es=e_sys)

# plot the installed storage capacities
# postprocessing.plot_storages_invest(res=results, es=e_sys)

# expoprt the results to excel
# postprocessing.export_excel(res=results, es=e_sys)

                               
'''

# plotting Energy System
graph_model.draw_graph(grph=graph_model.create_nx_graph(e_sys), 
                       plot=True, layout='neato', node_size=1000,
                       node_color={
                               'b_el_ez': '#0049db',
                               'b_el_bhkw': '#0049db',
                               'b_el_bhkw_2': '#0049db',
                               'b_el_buy': '#0049db',
                               'b_el_sell': '#0049db',
                               'b_gas_buy': '#f2e60e',
                               'b_gas_bhkw': '#f2e60e',
                               'b_heat_gen': '#f95c8b',
                               'b_heat_grid': '#f95c8b',
                               'b_heat_35': '#f95c8b',})
                               