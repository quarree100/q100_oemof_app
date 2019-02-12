"""
oemof application for research project quarree100

Copyright (c) 2018 Quarree100 AB-3 Project-Team

SPDX-License-Identifier: GPL-3.0-or-later
"""

import setup_solve_model
import postprocessing
import config as cfg
import os

# getting path to data from ini file
path_to_data = os.path.join(os.path.expanduser("~"),
                            cfg.get('paths', 'data'))

filename = os.path.join(
    os.path.expanduser("~"), path_to_data, 'Parameter.xlsx')

# reading data from excel file with data read function
node_data = setup_solve_model.nodes_from_excel(filename)

# setting up energy system
e_sys = setup_solve_model.setup_es(excel_nodes=node_data)

# optimising the energy system
results = setup_solve_model.solve_es(energysystem=e_sys, excel_nodes=node_data)

# plot the buses
postprocessing.plot_buses(res=results, es=e_sys)

# plot the investments in transformer
postprocessing.plot_trans_invest(res=results, es=e_sys)

# plot the storage SoC(t)
postprocessing.plot_storages_soc(res=results, es=e_sys)

# plot the installed storage capacities
postprocessing.plot_storages_invest(res=results, es=e_sys)

# expoprt the results to excel
postprocessing.export_excel(res=results, es=e_sys)
