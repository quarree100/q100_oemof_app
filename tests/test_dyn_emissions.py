"""
oemof application for research project quarree100.

SPDX-License-Identifier: GPL-3.0-or-later
"""

from oemof.tools import logger
import oemof.solph as solph
import oemof.outputlib as outputlib
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from customized import add_contraints


def test_dyn_emission_example():
    logger.define_logging()
    logging.info('Initialize the energy system')

    number_timesteps = 11

    date_time_index = pd.date_range('1/1/2012', periods=number_timesteps,
                                    freq='H')

    es = solph.EnergySystem(timeindex=date_time_index)

    # Create oemof objects
    logging.info('Create oemof objects')

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

    # Optimise the energy system
    logging.info('Optimise the energy system')

    # initialise the operational model
    om = solph.Model(energysystem=es)

    """
    Alterantive way of adding the emission factor:
    
    om.flows['label_bel', 'demand_el'].emission_factor =\
        [0.01 for i in range(0, number_timesteps)]

    om.flows[elec_fossil, bel].emission_factor = [
        0.7, 0.7, 0.7, 0.7, 0.1, 0.5, 1, 1.3, 0.7, 0.7, 0.7]
    
    Or:
    ----
    for i, o in om.flows.keys():
        if i is bel:
            om.flows[i, o].emission_factor =\
                [0.01 for i in range(0, number_timesteps)]
        if i is elec_fossil:
            om.flows[i, o].emission_factor =\
                [0.7, 0.7, 0.7, 0.7, 0.1, 0.5, 1, 1.3, 0.7, 0.7, 0.7]
    """

    # actual adding of emission constraint
    add_contraints.emission_limit_dyn(om, limit=15)

    # printing the emissions factors
    for (i, o) in om.flows:
        if hasattr(om.flows[i, o], 'emission_factor'):
            print('EMISSIONS')
            print(i, o, om.flows[i, o].emission_factor)

    # if tee_switch is true solver messages will be displayed
    logging.info('Solve the optimization problem')
    om.solve(solver='cbc', solve_kwargs={'tee': False})

    # Check and plot the results
    results = outputlib.processing.results(om)

    # get all variables of a specific component/bus
    electricity_bus = outputlib.views.node(results, 'label_bel')["sequences"]

    # plot the time series (sequences) of a specific component/bus
    if plt is not None:
        electricity_bus.plot(kind='line', drawstyle='steps-mid',
                                  legend='right')
        plt.show()

    # print total emissions
    print('Total emissions:')
    print(om.total_emissions())

test_dyn_emission_example()
