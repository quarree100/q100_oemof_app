"""
oemof application for research project quarree100

Copyright (c) 2018 Quarree100 AB-3 Project-Team

SPDX-License-Identifier: GPL-3.0-or-later
"""

import setup_solve_model
import postprocessing
import config as cfg
import os
import oemof.outputlib as outputlib

# getting path to data from ini file
path_to_data = os.path.join(os.path.expanduser("~"),
                            cfg.get('paths', 'data'))

path_to_results = os.path.join(os.path.expanduser("~"),
                            cfg.get('paths', 'results'))

filename = os.path.join(
    os.path.expanduser("~"), path_to_data, 'Parameter_AB1.xlsx')

# reading data from excel file with data read function
node_data = setup_solve_model.nodes_from_excel(filename)

# setting up energy system
e_sys = setup_solve_model.setup_es(excel_nodes=node_data)

# optimising the energy system
results = setup_solve_model.solve_es(energysystem=e_sys, excel_nodes=node_data)

# add results to the energy system to make it possible to store them.
e_sys.results['main'] = results

# store energy system with results
e_sys.dump(dpath=path_to_results, filename='test_results')

# plot the buses
postprocessing.plot_buses(res=results, es=e_sys)

# plot the investments in transformer
# postprocessing.plot_trans_invest(res=results, es=e_sys)

# plot the storage SoC(t)
postprocessing.plot_storages_soc(res=results, es=e_sys)

# plot the installed storage capacities
# postprocessing.plot_storages_invest(res=results, es=e_sys)

# expoprt the results to excel
# postprocessing.export_excel(res=results, es=e_sys)
