"""
oemof application for research project quarree100.

Based on the excel_reader example of oemof_examples repository:
https://github.com/oemof/oemof-examples

SPDX-License-Identifier: GPL-3.0-or-later
"""

from oemof.tools import logger
from oemof.tools import economics
import oemof.solph as solph
import oemof.outputlib as outputlib
import logging
import pandas as pd
import numpy as np
from customized import add_contraints


def nodes_from_excel(filename):

    xls = pd.ExcelFile(filename)

    nodes_data = {'buses': xls.parse('Buses'),
                  'commodity_sources': xls.parse('Sources'),
                  'sources_series': xls.parse('Sources_series'),
                  'demand': xls.parse('Demand'),
                  'transformers_siso': xls.parse('Transformer_siso'),
                  'transformers_sido': xls.parse('Transformer_sido'),
                  'transformers_diso': xls.parse('Transformer_diso'),
                  'storages': xls.parse('Storages'),
                  'timeseries': xls.parse('Timeseries'),
                  'general': xls.parse('General')
                  }

    # set datetime index
    nodes_data['timeseries'].set_index('timestamp', inplace=True)
    nodes_data['timeseries'].index = pd.to_datetime(
        nodes_data['timeseries'].index)

    print('Data from Excel file {} imported.'
          .format(filename))

    return nodes_data


def create_nodes(nd=None):
    """Create nodes (oemof objects) from node dict

    Parameters
    ----------
    nd : :obj:`dict`
        Nodes data

    Returns
    -------
    nodes : `obj`:dict of :class:`nodes <oemof.network.Node>`
    """

    if not nd:
        raise ValueError('No nodes data provided.')

    nodes = []

    # Create Bus objects from buses table
    busd = {}

    for i, b in nd['buses'].iterrows():
        if b['active']:
            bus = solph.Bus(label=b['label'])
            nodes.append(bus)

            busd[b['label']] = bus
            if b['excess']:
                nodes.append(
                    solph.Sink(label=b['label'] + '_excess',
                               inputs={busd[b['label']]: solph.Flow(
                                   variable_costs=b['excess costs'])})
                )
            if b['shortage']:
                nodes.append(
                    solph.Source(label=b['label'] + '_shortage',
                                 outputs={busd[b['label']]: solph.Flow(
                                     variable_costs=b['shortage costs'])})
                    )

    # Create Source objects from table 'Sources'
    for i, cs in nd['commodity_sources'].iterrows():
        if cs['active']:

            outflow_args = {'variable_costs': cs['variable costs']}

            if cs['emission_series']:
                for col in nd['timeseries'].columns.values:
                    if col.split('.')[0] == cs['label']:
                        outflow_args['emission_factor'] = nd['timeseries'][col]
            else:
                outflow_args['emission_factor'] = \
                    np.full(nd['general']['timesteps'][0], cs['emissions'])

            nodes.append(
                solph.Source(
                    label=cs['label'],
                    outputs={busd[cs['to']]: solph.Flow(**outflow_args)})
                )

    # Create Source objects with fixed time series from 'renewables' table
    for i, ss in nd['sources_series'].iterrows():
        if ss['active']:
            # set static outflow values
            outflow_args = {'nominal_value': ss['scalingfactor'],
                            'fixed': True}
            # get time series for node and parameter
            for col in nd['timeseries'].columns.values:
                if col.split('.')[0] == ss['label']:
                    outflow_args[col.split('.')[1]] = nd['timeseries'][col]

            # create
            nodes.append(
                solph.Source(label=ss['label'],
                             outputs={
                                 busd[ss['to']]: solph.Flow(**outflow_args)})
            )

    # Create Sink objects with fixed time series from 'demand' table
    for i, de in nd['demand'].iterrows():
        if de['active']:
            # set static inflow values
            inflow_args = {'nominal_value': de['scalingfactor'],
                           'fixed': de['fixed']}
            # get time series for node and parameter
            for col in nd['timeseries'].columns.values:
                if col.split('.')[0] == de['label']:
                    inflow_args[col.split('.')[1]] = nd['timeseries'][col]

            # create
            nodes.append(
                solph.Sink(label=de['label'],
                           inputs={
                               busd[de['from']]: solph.Flow(**inflow_args)})
            )

    # Create Transformer objects from 'transformers' table
    for i, t in nd['transformers_siso'].iterrows():
        if t['active']:

            if t['invest']:

                # calculation epc
                epc_t = economics.annuity(
                    capex=t['capex'], n=t['n'],
                    wacc=nd['general']['interest rate'][0]) * \
                        nd['general']['timesteps'][0] / 8760

                # create
                nodes.append(
                    solph.Transformer(
                        label=t['label'],
                        inputs={busd[t['from']]: solph.Flow()},
                        outputs={busd[t['to']]: solph.Flow(
                            variable_costs=t['variable costs'],
                            emissions=['emissions'],
                            investment=solph.Investment(
                                ep_costs=epc_t))},
                        conversion_factors={busd[t['to']]: t['efficiency']})
                )

            else:
                # create
                nodes.append(
                    solph.Transformer(
                        label=t['label'],
                        inputs={busd[t['from']]: solph.Flow()},
                        outputs={busd[t['to']]: solph.Flow(
                            nominal_value=t['installed'],
                            variable_costs=t['variable costs'],
                            emissions=['emissions'])},
                        conversion_factors={busd[t['to']]: t['efficiency']})
                )

    for i, tdo in nd['transformers_sido'].iterrows():
        if tdo['active']:
            if tdo['invest']:
                # calculation epc
                epc_tdo = economics.annuity(
                    capex=tdo['capex'], n=tdo['n'],
                    wacc=nd['general']['interest rate'][0]) *\
                      nd['general']['timesteps'][0] / 8760

                # create
                nodes.append(
                    solph.Transformer(
                        label=tdo['label'],
                        inputs={busd[tdo['from']]: solph.Flow()},
                        outputs={busd[tdo['to_1']]: solph.Flow(
                            investment=solph.Investment(ep_costs=epc_tdo)),
                            busd[tdo['to_2']]: solph.Flow()
                        },
                        conversion_factors={
                            busd[tdo['to_1']]: tdo['efficiency_1'],
                            busd[tdo['to_2']]: tdo['efficiency_2']
                        })
                )

            else:
                nodes.append(
                    solph.Transformer(
                        label=tdo['label'],
                        inputs={busd[tdo['from']]: solph.Flow()},
                        outputs={
                            busd[tdo['to_1']]: solph.Flow(
                                nominal_value=tdo['installed']),
                            busd[tdo['to_2']]: solph.Flow()
                        },
                        conversion_factors={
                            busd[tdo['to_1']]: tdo['efficiency_1'],
                            busd[tdo['to_2']]: tdo['efficiency_2']
                        })
                )

    for i, tdiso in nd['transformers_diso'].iterrows():
        if tdiso['active']:
            if tdiso['invest']:
                # calculation epc
                epc_tdiso = economics.annuity(
                    capex=tdiso['capex'], n=tdiso['n'],
                    wacc=nd['general']['interest rate'][0]) *\
                      nd['general']['timesteps'][0] / 8760

                # create
                nodes.append(
                    solph.Transformer(
                        label=tdiso['label'],
                        inputs={busd[tdiso['from_1']]: solph.Flow(),
                                busd[tdiso['from_2']]: solph.Flow()},
                        outputs={busd[tdiso['to_1']]: solph.Flow(
                            investment=solph.Investment(ep_costs=epc_tdiso))},
                        conversion_factors={
                            busd[tdiso['from_1']]: tdiso['eff_in_1'],
                            busd[tdiso['from_2']]: tdiso['eff_in_2'],
                            busd[tdiso['to_1']]: tdiso['eff_out_1']
                        })
                )

            else:
                nodes.append(
                    solph.Transformer(
                        label=tdiso['label'],
                        inputs={busd[tdiso['from_1']]: solph.Flow(),
                                busd[tdiso['from_2']]: solph.Flow()},
                        outputs={busd[tdiso['to_1']]: solph.Flow(
                            nominal_value=tdiso['installed'])},
                        conversion_factors={
                            busd[tdiso['from_1']]: tdiso['eff_in_1'],
                            busd[tdiso['from_2']]: tdiso['eff_in_2'],
                            busd[tdiso['to_1']]: tdiso['eff_out_1']
                        })
                )

    for i, s in nd['storages'].iterrows():
        if s['active']:
            if s['invest']:
                # calculate epc
                epc_s = economics.annuity(
                    capex=s['capex'], n=s['n'],
                    wacc=nd['general']['interest rate'][0]) * \
                        nd['general']['timesteps'][0] / 8760

                # create Storages
                nodes.append(
                    solph.components.GenericStorage(
                        label=s['label'],
                        inputs={busd[s['bus']]: solph.Flow()},
                        outputs={busd[s['bus']]: solph.Flow()},
                        capacity_loss=s['capacity_loss'],
                        invest_relation_input_capacity=s[
                            'invest_relation_input_capacity'],
                        invest_relation_output_capacity=s[
                            'invest_relation_output_capacity'],
                        inflow_conversion_factor=s['inflow_conversion_factor'],
                        outflow_conversion_factor=s['outflow_conversion_factor'],
                        investment=solph.Investment(ep_costs=epc_s)))
            else:
                # create Storages
                nodes.append(
                    solph.components.GenericStorage(
                        label=s['label'],
                        inputs={busd[s['bus']]: solph.Flow()},
                        outputs={busd[s['bus']]: solph.Flow()},
                        capacity_loss=s['capacity_loss'],
                        nominal_capacity=s['capacity'],
                        inflow_conversion_factor=s['inflow_conversion_factor'],
                        outflow_conversion_factor=s['outflow_conversion_factor'],
                        ))

    return nodes


def setup_es(excel_nodes=None):
    # Initialise the Energy System
    logger.define_logging()
    logging.info('Initialize the energy system')

    number_timesteps = excel_nodes['general']['timesteps'][0]

    date_time_index = pd.date_range('1/1/2016',
                                    periods=number_timesteps,
                                    freq='H')
    energysystem = solph.EnergySystem(timeindex=date_time_index)

    logging.info('Create oemof objects')

    # create nodes from Excel sheet data with create_nodes function
    my_nodes = create_nodes(nd=excel_nodes)

    # add nodes and flows to energy system
    energysystem.add(*my_nodes)

    print('Energysystem has been created')

    print("*********************************************************")
    print("The following objects have been created from excel sheet:")
    for n in energysystem.nodes:
        oobj =\
            str(type(n)).replace("<class 'oemof.solph.", "").replace("'>", "")
        print(oobj + ':', n.label)
    print("*********************************************************")

    return energysystem


def solve_es(energysystem=None, excel_nodes=None):
    # Optimise the energy system
    logging.info('Optimise the energy system')

    # initialise the operational model
    om = solph.Model(energysystem)

    # Global CONSTRAINTS: CO2 Limit
    add_contraints.emission_limit_dyn(
        om, limit=excel_nodes['general']['emission limit'][0])

    logging.info('Solve the optimization problem')
    # if tee_switch is true solver messages will be displayed
    om.solve(solver='cbc', solve_kwargs={'tee': True})

    logging.info('Store the energy system with the results.')

    # processing results
    result = outputlib.processing.results(om)

    return result


def create_comp_lists(es=None):

    l_buses = []
    l_storages = []
    l_transformer = []

    for n in es.nodes:

        type_name =\
            str(type(n)).replace("<class 'oemof.solph.", "").replace("'>", "")

        if type_name == "network.Bus":
            l_buses.append(n.label)

        if type_name == "network.Transformer":
            l_transformer.append(n.label)

        if type_name == "components.GenericStorage":
            l_storages.append(n.label)

    comp_dict = {'buses': l_buses,
                 'transformer': l_transformer,
                 'storages': l_storages
                 }

    return comp_dict
