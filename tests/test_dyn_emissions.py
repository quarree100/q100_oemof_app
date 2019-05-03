"""
oemof application for research project quarree100.

SPDX-License-Identifier: GPL-3.0-or-later
"""

import oemof.solph as solph
import pandas as pd
import numpy as np
from customized import add_contraints


def test_dyn_emission_example():

    number_timesteps = 11
    date_time_index = pd.date_range('1/1/2012', periods=number_timesteps,
                                    freq='H')

    es = solph.EnergySystem(timeindex=date_time_index)

    # create electricity bus
    bel = solph.Bus(label='label_bel')

    # add bgas and bel to energysystem
    es.add(bel)

    # create source object representing the electricity net
    elec_fossil = solph.Source(
        label='elec_net_fossil',
        outputs={bel: solph.Flow(variable_costs=10,
                                 emission_factor=[0.7, 0.7, 0.7, 0.7, 0.1, 0.5,
                                                  1, 1.3, 0.7, 0.7, 0.7])})

    # create source object representing the electricity net
    es.add(solph.Source(label='elec_net_green',
                        outputs={bel: solph.Flow(
                            variable_costs=30,
                            emission_factor=np.full(11, 0.01)
                        )}))

    # create simple sink object representing the electrical demand
    es.add(solph.Sink(label='demand_el',
                      inputs={bel: solph.Flow(
                          actual_value=[5, 6, 7, 8, 9, 10, 9, 8, 7, 6, 5],
                          fixed=True, nominal_value=1)}))

    es.add(elec_fossil)

    om = solph.Model(energysystem=es)

    # actual adding of emission constraint
    add_contraints.emission_limit_dyn(om, limit=15)

    om.solve(solver='cbc', solve_kwargs={'tee': False})

test_dyn_emission_example()
