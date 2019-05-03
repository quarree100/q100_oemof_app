# -*- coding: utf-8 -*-
"""
Example that shows how to use custom component `GenericOffsetTransformer`.

This file is part of project oemof (github.com/oemof/oemof). It's copyrighted
by the contributors recorded in the version control history of the file,
available from its original location oemof/tests/test_scripts/test_solph/
test_generic_offsettransformer/test_generic_offsettransformer.py

SPDX-License-Identifier: GPL-3.0-or-later
"""

import os
import pandas as pd
import oemof.solph as solph
import matplotlib.pyplot as plt
from oemof.network import Node
from oemof.outputlib import processing, views
import heatpipe
import numpy as np


# date for heat sink
data = pd.Series(np.arange(1,101,1))

# select periods
periods = len(data)-1

# create an energy system
idx = pd.date_range('1/1/2017', periods=periods, freq='H')
es = solph.EnergySystem(timeindex=idx)
Node.registry = es

# heat bus start (source)
b_heat_0 = solph.Bus(label='b_heat_0')
# heat bus end (sink)
b_heat_1 = solph.Bus(label='b_heat_1')

solph.Source(label='source_th',
             outputs={b_heat_1: solph.Flow(variable_costs=10000)})

solph.Sink(label='demand_th', inputs={
    b_heat_1: solph.Flow(
        fixed=True, actual_value=data, nominal_value=4)})



solph.Source(label='source_el', outputs={
    b_heat_0: solph.Flow(variable_costs=1)})

# calculate coeffiencies and parameters
P_input_max = 100   # nominal power of input flow
P_input_min = 0    # minimal power of input flow

# generic heatpipe
hp = heatpipe.Heatpipe(
    label='heat_pipe',
    inputs={b_heat_0: solph.Flow()},
    outputs={b_heat_1: solph.Flow(nominal_value=None,
                                  investment=solph.Investment(ep_costs=10000,
                                                              maximum=300),
                                  )},
    effiency=[1 for k in range(0, periods)],
    heat_loss_factor=0.0002,
    length=200.0,
    heat_loss=0.2
    )

# create an optimization problem and solve it
om = solph.Model(es)

# solve model
om.solve(solver='cbc', solve_kwargs={'tee': True})

# create result object
results = processing.results(om)

data = views.node(results, 'b_heat_1')['sequences'].sum(axis=0).to_dict()

electricity_bus = views.node(results, 'b_heat_0')["sequences"]
heat_bus = views.node(results, 'b_heat_1')["sequences"]
heat_pipe_eval = views.node(results, 'heat_pipe')["sequences"]

# plot the time series (sequences) of a specific component/bus
if plt is not None:
    electricity_bus.plot(kind='line', drawstyle='steps-post', legend='right')
    plt.legend()
    plt.show()
    heat_bus.plot(kind='line', drawstyle='steps-post')
    plt.legend()
    heat_pipe_eval.plot(kind='line', drawstyle='steps-post')
    plt.legend()
    plt.show()

df_ges = pd.concat([electricity_bus, heat_bus], axis=1)

elec_array = views.node(results, 'b_heat_0')['sequences'].values[:, 0]
heat_array = views.node(results, 'b_heat_1')['sequences'].values[:, 1]

cop = np.divide(heat_array, elec_array, out=np.zeros_like(heat_array),
                where=elec_array != 0)
plt.plot(idx, cop)
plt.show()
