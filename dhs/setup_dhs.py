"""
oemof application for research project quarree100.

Based on the excel_reader example of oemof_examples repository:
https://github.com/oemof/oemof-examples

SPDX-License-Identifier: GPL-3.0-or-later
"""

import os
from oemof.tools import logger
from oemof.tools import economics
import oemof.solph as solph
import oemof.outputlib as outputlib
import logging
import pandas as pd
import numpy as np
from customized import add_contraints
from customized import heatpipe
from simpledbf import Dbf5
import pprint as pp
from matplotlib import pyplot as plt
from collections import namedtuple


class Label(namedtuple('solph_label', ['tag1', 'tag2', 'tag3', 'tag4'])):
    __slots__ = ()

    def __str__(self):
        """The string is used within solph as an ID, so it hast to be unique"""
        return '_'.join(map(str, self._asdict().values()))


def add_buses(it, labels):

    for i, b in it.iterrows():

        labels['l_3'] = 'bus'

        if b['active']:
            labels['l_2'] = b['label_2']
            l_bus = Label(labels['l_1'], labels['l_2'], labels['l_3'],
                          labels['l_4'])
            bus = solph.Bus(label=l_bus)
            nodes.append(bus)

            busd[l_bus] = bus

            if b['excess']:
                labels['l_3'] = 'excess'
                nodes.append(
                    solph.Sink(label=Label(labels['l_1'], labels['l_2'],
                                           labels['l_3'], labels['l_4']),
                               inputs={busd[l_bus]: solph.Flow(
                                   variable_costs=b['excess costs'])}))

            if b['shortage']:
                labels['l_3'] = 'shortage'
                nodes.append(
                    solph.Source(label=Label(labels['l_1'], labels['l_2'],
                                             labels['l_3'], labels['l_4']),
                                 outputs={busd[l_bus]: solph.Flow(
                                     variable_costs=b['shortage costs'])}))


def add_sources(it, labels):

    for i, cs in it.iterrows():
        labels['l_3'] = 'source'

        if cs['active']:
            labels['l_2'] = cs['label_2']
            outflow_args = {}

            if cs['cost_series']:
                print('error: noch nicht angepasst!')

            else:
                outflow_args['variable_costs'] = cs['variable costs']

            if cs['emission_series']:
                print('error: noch nicht angepasst!')

            else:
                outflow_args['emission_factor'] = \
                    np.full(num_ts, cs['emissions'])

            nodes.append(
                solph.Source(
                    label=Label(labels['l_1'], labels['l_2'], labels['l_3'],
                                labels['l_4']),
                    outputs={busd[(
                        labels['l_1'], cs['label_2'], 'bus',
                        labels['l_4'])]: solph.Flow(**outflow_args)}))


def add_demand(it, labels):

    for i, de in it.iterrows():
        labels['l_3'] = 'demand'

        if de['active']:
            labels['l_2'] = de['label_2']
            # set static inflow values
            inflow_args = {'nominal_value': de['scalingfactor'],
                           'fixed': de['fixed'],
                           'actual_value': houses_series[
                               labels['l_2']][labels['l_4']]}

            # create
            nodes.append(
                solph.Sink(label=Label(labels['l_1'], labels['l_2'],
                                       labels['l_3'], labels['l_4']),
                           inputs={
                               busd[(labels['l_1'], labels['l_2'], 'bus',
                                     labels['l_4'])]: solph.Flow(
                                        **inflow_args)}))


def add_transformer(it, labels):

    for i, t in it.iterrows():
        labels['l_2'] = None

        if t['active']:
            labels['l_3'] = t['label_3']

            # Transformer with 1 Input and 1 Output
            if t['type'] == "1-in_1-out":

                b_in_1 = busd[(labels['l_1'], t['in_1'], 'bus', labels['l_4'])]
                b_out_1 = busd[(labels['l_1'], t['out_1'], 'bus',
                                labels['l_4'])]

                if t['invest']:

                    if t['eff_out_1'] == 'series':
                        print('noch nicht angepasst!')

                    # calculation epc
                    epc_t = economics.annuity(capex=t['capex'], n=t['n'],
                                              wacc=rate) * f_invest

                    # create
                    nodes.append(
                        solph.Transformer(
                            label=Label(labels['l_1'], labels['l_2'],
                                        labels['l_3'], labels['l_4']),
                            inputs={b_in_1: solph.Flow()},
                            outputs={b_out_1: solph.Flow(
                                variable_costs=t['variable_costs'],
                                summed_max=t['in_1_sum_max'],
                                investment=solph.Investment(
                                    ep_costs=epc_t + t['service'] * f_invest,
                                    maximum=t['max_invest'],
                                    minimum=t['min_invest']))},
                            conversion_factors={
                                b_out_1: t['eff_out_1']}))

                else:
                    # create
                    if t['eff_out_1'] == 'series':
                        print('noch nicht angepasst!')
                        # for col in nd['timeseries'].columns.values:
                        #     if col.split('.')[0] == t['label']:
                        #         t[col.split('.')[1]] = nd['timeseries'][
                        #             col]

                    nodes.append(
                        solph.Transformer(
                            label=Label(labels['l_1'], labels['l_2'],
                                        labels['l_3'], labels['l_4']),
                            inputs={b_in_1: solph.Flow()},
                            outputs={b_out_1: solph.Flow(
                                nominal_value=t['installed'],
                                summed_max=t['in_1_sum_max'],
                                variable_costs=t['variable_costs'])},
                            conversion_factors={b_out_1: t['eff_out_1']}))


# defining general stuff
nd = {}

# some general data
num_ts = 200
f_invest = num_ts / 8760
rate = 0.01
emission_limit = 10000000

# pv parameters
capex_pv = 100
n_pv = 20

nodes = []  #
busd = {}   # all buses needs to be in the dict

d_labels = {'l_1': '',
            'l_2': '',
            'l_3': '',
            'l_4': ''}

# Assembly Energy System
# get data houses
# getting path to data from IFAM owncloud
path_to_data = os.path.join(
    os.path.expanduser("~"),
    'ownCloud/FhG-owncloud-Quarree-AB3/AB-3.3/oemof_dhs_data/Test_data/')

# getting the data for the houses from qgis
filename_dbf_points = os.path.join(path_to_data,
                                   'gis/points_houses.dbf')


df_houses = Dbf5(filename_dbf_points).to_dataframe()

# add to nodes_data
nd['houses'] = df_houses

# getting data for the technologies of the houses
xls = pd.ExcelFile(os.path.join(path_to_data,'data_houses.xlsx'))
houses_nodes = {'bus': xls.parse('Buses'),
                'source': xls.parse('Sources'),
                'demand': xls.parse('Demand'),
                'transformer': xls.parse('Transformer')
                }

nd['houses_nodes'] = houses_nodes

#  data for demand series of houses
xls = pd.ExcelFile(os.path.join(path_to_data,'Timeseries_houses.xlsx'))

houses_series = {'heat': xls.parse('heat'),
                 'electricity': xls.parse('electricity'),
                 'pv': xls.parse('pv')}

nd['houses_series'] = houses_series

# add nodes of houses

for r, c in nd['houses'].iterrows():

    d_labels['l_1'] = 'house'
    d_labels['l_4'] = c['ID']

    for key, item in nd['houses_nodes'].items():

        if key == 'bus':
            add_buses(item, d_labels)

        if key == 'source':
            add_sources(item, d_labels)

        if key == 'demand':
            add_demand(item, d_labels)

        if key == 'transformer':
            add_transformer(item, d_labels)

    # add pv when there is pv potential
    if c['pv_pot']:
        # add pv source series
        d_labels['l_2'] = 'elec-pv'
        d_labels['l_3'] = 'bus'

        l_bus_pv = Label(d_labels['l_1'], d_labels['l_2'], d_labels['l_3'],
                         d_labels['l_4'])

        d_labels['l_3'] = 'pv-source'

        epc_pv = economics.annuity(capex=capex_pv, n=n_pv,
                                   wacc=rate) * f_invest

        nodes.append(solph.Source(
            label=Label(d_labels['l_1'], d_labels['l_2'], d_labels['l_3'],
                        d_labels['l_4']),
            outputs={busd[l_bus_pv]: solph.Flow(
                actual_value=houses_series['pv'][c['ID']],
                investment=solph.Investment(ep_costs=epc_pv,
                                            maximum=c['pv_max']),
                fixed=True)}))

    # add existing heat generators
    


# GENERATION
# getting the data for the generations sites from qgis
filename_dbf_points = os.path.join(path_to_data,
                                   'gis/points_generation.dbf')
df_generation = Dbf5(filename_dbf_points).to_dataframe()

# add to nodes_data
nd['generation'] = df_generation

xls = pd.ExcelFile(os.path.join(path_to_data, 'data_generation.xlsx'))
generation_nodes = {'bus': xls.parse('Buses'),
                    'source': xls.parse('Sources'),
                    'demand': xls.parse('Demand'),
                    'transformer': xls.parse('Transformer')
                    }

nd['generation_nodes'] = generation_nodes

# add nodes of generation side

for l, m in nd['generation'].iterrows():

    d_labels['l_1'] = 'generation'
    d_labels['l_4'] = m['ID']

    for key, item in nd['generation_nodes'].items():

        if key == 'bus':
            add_buses(item, d_labels)

        if key == 'source':
            add_sources(item, d_labels)

        if key == 'demand':
            add_demand(item, d_labels)

        if key == 'transformer':
            add_transformer(item, d_labels)


# add nodes of Infrastructure
# knots (buses)
filename_dbf_points = os.path.join(
    path_to_data, 'gis/points_dhs.dbf')
nd['dhs_knots'] = Dbf5(filename_dbf_points).to_dataframe()

for n, o in nd['dhs_knots'].iterrows():
    d_labels['l_1'] = 'infrastructure'
    d_labels['l_2'] = 'heat'
    d_labels['l_3'] = 'bus'
    d_labels['l_4'] = o['ID']

    l_bus = Label(d_labels['l_1'], d_labels['l_2'], d_labels['l_3'],
                  d_labels['l_4'])
    bus = solph.Bus(label=l_bus)
    nodes.append(bus)

    busd[l_bus] = bus

# heatpipes
filename_dbf_points = os.path.join(
    path_to_data, 'gis/lines_test.dbf')
nd['dhs_pipes'] = Dbf5(filename_dbf_points).to_dataframe()

for p, q in nd['dhs_pipes'].iterrows():

    d_labels['l_1'] = 'infrastructure'
    d_labels['l_2'] = 'heat'
    d_labels['l_3'] = 'pipe'

    epc_p = economics.annuity(capex=q['costs']*q['length'],
                            n=q['lifetime'], wacc=rate) * f_invest

    # connection of houses
    if q['start'][:1] == "H" or q['end'][:1] == "H":

        if q['start'][:1] == "H":
            start = q['end']
            end = q['start']
            b_in = busd[(d_labels['l_1'], d_labels['l_2'], 'bus', start)]
            b_out = busd[('house', d_labels['l_2'], 'bus', end)]

        else:
            start = q['start']
            end = q['end']
            b_in = busd[(d_labels['l_1'], d_labels['l_2'], 'bus', start)]
            b_out = busd[('house', d_labels['l_2'], 'bus', end)]

        d_labels['l_4'] = start + '-' + end

        l_pipe = Label(d_labels['l_1'], d_labels['l_2'], d_labels['l_3'],
                        d_labels['l_4'])

        nodes.append(heatpipe.HeatPipeline(
            label=l_pipe,
            inputs={b_in: solph.Flow()},
            outputs={b_out: solph.Flow(
                nominal_value=None, investment=solph.Investment(
                    ep_costs=epc_p, maximum=q['cap_max']))},
            heat_loss_factor=q['l_factor'],
            length=q['length'],
        ))

    # connection energy generation site
    if q['start'][:1] == "G" or q['end'][:1] == "G":

        if q['start'][:1] == "G":
            start = q['start']
            end = q['end']
            b_in = busd[('generation', d_labels['l_2'], 'bus', start)]
            b_out = busd[(d_labels['l_1'], d_labels['l_2'], 'bus', end)]

        else:
            start = q['end']
            end = q['start']
            b_in = busd[('generation', d_labels['l_2'], 'bus', start)]
            b_out = busd[(d_labels['l_1'], d_labels['l_2'], 'bus', end)]

        d_labels['l_4'] = start + '-' + end

        l_pipe = Label(d_labels['l_1'], d_labels['l_2'], d_labels['l_3'],
                        d_labels['l_4'])

        nodes.append(heatpipe.HeatPipeline(
            label=l_pipe,
            inputs={b_in: solph.Flow()},
            outputs={b_out: solph.Flow(
                nominal_value=None, investment=solph.Investment(
                    ep_costs=epc_p, maximum=q['cap_max']))},
            heat_loss_factor=q['l_factor'],
            length=q['length'],
        ))

    # connection of knots with 2 pipes in each direction
    if q['start'][:1] == "K" and q['end'][:1] == "K":

        start = q['start']
        end = q['end']
        b_in = busd[(d_labels['l_1'], d_labels['l_2'], 'bus', start)]
        b_out = busd[(d_labels['l_1'], d_labels['l_2'], 'bus', end)]

        d_labels['l_4'] = start + '-' + end

        l_pipe = Label(d_labels['l_1'], d_labels['l_2'], d_labels['l_3'],
                        d_labels['l_4'])

        nodes.append(heatpipe.HeatPipeline(
            label=l_pipe,
            inputs={b_in: solph.Flow()},
            outputs={b_out: solph.Flow(
                nominal_value=None, investment=solph.Investment(
                    ep_costs=epc_p, maximum=q['cap_max']))},
            heat_loss_factor=q['l_factor'],
            length=q['length']
        ))

        start = q['end']
        end = q['start']
        b_in = busd[(d_labels['l_1'], d_labels['l_2'], 'bus', start)]
        b_out = busd[(d_labels['l_1'], d_labels['l_2'], 'bus', end)]

        d_labels['l_4'] = start + '-' + end

        l_pipe = Label(d_labels['l_1'], d_labels['l_2'], d_labels['l_3'],
                       d_labels['l_4'])

        nodes.append(heatpipe.HeatPipeline(
            label=l_pipe,
            inputs={b_in: solph.Flow()},
            outputs={b_out: solph.Flow(
                nominal_value=None, investment=solph.Investment(
                    ep_costs=epc_p, maximum=q['cap_max']))},
            heat_loss_factor=q['l_factor'],
            length=q['length']
        ))


print('Nodes created')

# Setup and Solve Energy System

# Initialise the Energy System
logger.define_logging()
logging.info('Initialize the energy system')

date_time_index = pd.date_range('1/1/2018', periods=num_ts, freq='H')
esys = solph.EnergySystem(timeindex=date_time_index)

logging.info('Create oemof objects')

# add nodes and flows to energy system
esys.add(*nodes)

print('Energysystem has been created')

print("*********************************************************")
print("The following objects have been created from excel sheet:")
for n in esys.nodes:
    oobj =\
        str(type(n)).replace("<class 'oemof.solph.", "").replace("'>", "")
    print(oobj + ':', n.label)
print("*********************************************************")


logging.info('Optimise the energy system')

# initialise the operational model
om = solph.Model(esys)

# Global CONSTRAINTS: CO2 Limit
add_contraints.emission_limit_dyn(om, limit=emission_limit)

logging.info('Solve the optimization problem')
# if tee_switch is true solver messages will be displayed
om.solve(solver='cbc', solve_kwargs={'tee': False})

# plot the Energy System
try:
    import pygraphviz
    import graph_model as gm
    from oemof.graph import create_nx_graph
    import networkx as nx
    grph = create_nx_graph(esys)
    pos = nx.drawing.nx_agraph.graphviz_layout(grph, prog='neato')
    gm.plot_graph(pos, grph)
    plt.show()
    logging.info('Energy system Graph OK')
except ImportError:
    logging.info('Module pygraphviz not found: Graph was not plotted.')


# postprocessing

logging.info('Store the energy system with the results.')
# add results to the energy system to make it possible to store them.
esys.results['main'] = outputlib.processing.results(om)
esys.results['meta'] = outputlib.processing.meta_results(om)

# store energy system with results
# e_sys.dump(dpath=path_to_results, filename='results_val_1')

# print the solver results
print('********* Meta results *********')
pp.pprint(esys.results['meta'])
print('')

esys.results['main'] = outputlib.processing.results(om)
results = esys.results['main']

esys.groups.keys()
s_h1 = esys.groups["house_electricity_source_H1"]

print('********* LABEL *********')
print(repr(s_h1.label))
print(str(s_h1.label))
print('')
print(str(s_h1.label))
print(type(s_h1))

s_h1_el_seq = outputlib.views.node(results, s_h1)['sequences']
