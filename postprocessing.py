"""
oemof application for research project quarree100.

Some parts of the code are adapted from
https://github.com/oemof/oemof-examples
-> excel_reader

SPDX-License-Identifier: GPL-3.0-or-later
"""

import oemof.outputlib as outputlib
import oemof.solph as solph
import pandas as pd
import os
import config as cfg
from matplotlib import pyplot as plt


def plot_buses(res=None, es=None):

    l_buses = []

    for n in es.nodes:
        type_name =\
            str(type(n)).replace("<class 'oemof.solph.", "").replace("'>", "")
        if type_name == "network.Bus":
            l_buses.append(n.label)

    for n in l_buses:
        bus_sequences = outputlib.views.node(res, n)["sequences"]
        bus_sequences.plot(kind='line', drawstyle="steps-mid", subplots=False,
                           sharey=True)
        plt.show()


def plot_trans_invest(res=None, es=None):

    l_transformer = []

    for n in es.nodes:
        type_name =\
            str(type(n)).replace("<class 'oemof.solph.", "").replace("'>", "")
        if type_name == "network.Transformer":
            l_transformer.append(n.label)

    p_trans_install = []

    for q in l_transformer:
        if outputlib.views.node(res, q)["scalars"][0] is not None:
            p_install = outputlib.views.node(res, q)["scalars"][0]
            p_trans_install.append(p_install)

    # plot the installed Transformer Capacities
    y = p_trans_install
    x = l_transformer
    width = 1/2
    plt.bar(x, y, width, color="blue")
    plt.ylabel('Installierte Leistung [kW]')
    plt.show()


def plot_storages_soc(res=None, es=None):

    l_storages = []

    for n in es.nodes:
        type_name =\
            str(type(n)).replace("<class 'oemof.solph.", "").replace("'>", "")
        if type_name == "components.GenericStorage":
            l_storages.append(n.label)

    for n in l_storages:
        soc_sequences = outputlib.views.node(res, n)["sequences"]
        soc_sequences = soc_sequences.drop(soc_sequences.columns[[0, 2]], 1)
        soc_sequences.plot(kind='line', drawstyle="steps-mid", subplots=False,
                           sharey=True)
        plt.show()


def plot_storages_invest(res=None, es=None):

    l_storages = []

    for n in es.nodes:
        type_name =\
            str(type(n)).replace("<class 'oemof.solph.", "").replace("'>", "")
        if type_name == "components.GenericStorage":
            l_storages.append(n.label)

    c_storage_install = []

    for n in l_storages:
        c_storage = outputlib.views.node(res, n)["scalars"][0]
        c_storage_install.append(c_storage)

    # plot the installed Storage Capacities
    plt.bar(l_storages, c_storage_install, width=0.5, color="blue")
    plt.ylabel('Kapazität [kWh]')
    plt.show()


def plot_invest(res=None, om=None):


    # Zeige alle Investment Flows
    l_invest = []
    p_invest = []
    inv_flows = om.InvestmentFlow.invest._data
    list_flows = [k for k in inv_flows]
    filter = []
    t1 = []
    t2 = []

    # Check for Type
    for n in range(len(list_flows)):
        t1.append(str(type(list_flows[n][0])))
        t2.append(str(type(list_flows[n][1])))

    # Filter storage flows counted twice
    for n in range(len(t2)):
        filter.append("Bus" not in t2[n])

    list_flows = [i for indx, i in enumerate(list_flows) if filter[indx]==False]

    # Check for Storage -> Capacity instead of rated Power
    for n in range(len(list_flows)):

        fnode = str(list_flows[n][0])
        if "GenericStorage" in str(type(list_flows[n][0])):
            tnode = 'None'
        else:
            tnode = str(list_flows[n][1])

        p_invest.append(outputlib.views.node(res, fnode)["scalars"][((fnode, tnode), 'invest')])
        l_invest.append(fnode)

    # plot the installed Capacities
    y = p_invest
    x = l_invest
    width = 2/3
    plt.bar(x, y, width, color="blue")
    plt.ylabel('Inst. Leistung [kW] / Inst. Kapazität [kWh]')
    plt.xlabel('Investierte Technologie')
    plt.title('Alle getaetigten Investitionen')
    plt.xticks(rotation=45)
    plt.show()


def export_excel(res=None, es=None):

    l_buses = []

    for n in es.nodes:
        type_name =\
            str(type(n)).replace("<class 'oemof.solph.", "").replace("'>", "")
        if type_name == "network.Bus":
            l_buses.append(n.label)

    l_transformer = []

    for n in es.nodes:
        type_name =\
            str(type(n)).replace("<class 'oemof.solph.", "").replace("'>", "")
        if type_name == "network.Transformer":
            l_transformer.append(n.label)

    l_storages = []

    for s in es.nodes:
        type_name =\
            str(type(s)).replace("<class 'oemof.solph.", "").replace("'>", "")
        if type_name == "components.GenericStorage":
            l_storages.append(s.label)

    df_series = pd.DataFrame()

    for n in l_buses:
        bus_sequences = outputlib.views.node(res, n)["sequences"]
        df_series = pd.concat([df_series, bus_sequences], axis=1)

    for n in l_storages:
        soc_sequences = outputlib.views.node(res, n)["sequences"]
        df_series = pd.concat([df_series, soc_sequences], axis=1)

    c_storage_install = []

    for n in l_storages:
        c_storage = outputlib.views.node(res, n)["scalars"][0]
        c_storage_install.append(c_storage)

    p_trans_install = []

    for q in l_transformer:
        p_install = outputlib.views.node(res, q)["scalars"][0]
        p_trans_install.append(p_install)

    df_invest_ges = pd.DataFrame(
        [p_trans_install+c_storage_install],
        columns=l_transformer+l_storages)

    # the result_gesamt df is exported in excel
    path_to_results = os.path.join(os.path.expanduser("~"),
                                   cfg.get('paths', 'results'))
    filename = 'results.xlsx'
    with pd.ExcelWriter(os.path.join(path_to_results, filename)) as xls:
        df_series.to_excel(xls, sheet_name='Timeseries')
        df_invest_ges.to_excel(xls, sheet_name='Invest')


def analyse_costs(es):
    """
    It is necessary to store the parameter and results
    like this:

    e_sys.results['main'] = outputlib.processing.results(om)
    e_sys.results['parameter'] = outputlib.processing.parameter_as_dict(om.es)

    :param es:
    :return: dict with cost structure
    """

    d_costs = {}

    p = es.results['parameter']
    r = es.results['main']

    # variable costs
    flows = [x for x in p if x[1] is not None]

    var_const = [x for x in flows if hasattr(p[x]['scalars'],
                                             'variable_costs')]
    var_seq = [x for x in flows if hasattr(p[x]['sequences'],
                                           'variable_costs')]

    var_const = [x for x in var_const if
                 p[x]['scalars']['variable_costs'] != 0]

    var_seq = [x for x in var_seq if
               r[x]['sequences'].sum() != 0]

    df_const = pd.DataFrame(index=es.timeindex)
    for flow in var_const:
        label = (flow[0].label, flow[1].label)
        values = r[flow]["sequences"].values * p[flow]["scalars"][
            'variable_costs']
        df_const[label] = values

    df_seq = pd.DataFrame(index=es.timeindex)
    for flow in var_seq:
        label = (flow[0].label, flow[1].label)
        values = r[flow]["sequences"].values * p[flow]["sequence"][
            'variable_costs']
        df_seq[label] = values

    df = pd.concat([df_const, df_seq], axis=1)
    var_costs = df.sum().sum()

    d_costs.update({'variable': {'total': var_costs,
                                 'detail': df}})

    # investment costs
    # flows
    flows = [x for x in r.keys() if x[1] is not None]

    # get keys of investmentflows out of list of flows
    invest_flows_all = [x for x in flows if hasattr(
        r[x]['scalars'], 'invest')]

    df_invest_flows = pd.DataFrame(index=['invest'])
    for flow in invest_flows_all:
        label = (flow[0].label, flow[1].label)
        value = r[flow]["scalars"]['invest']
        df_invest_flows[label] = value * p[flow]['scalars'][
            'investment_ep_costs']

    # storages
    flows = [x for x in r.keys() if x[1] is None]

    # get keys of investmentflows out of list of flows
    invest_flows_all = [x for x in flows if hasattr(
        r[x]['scalars'], 'invest')]

    # get list of keys of investment trafos
    invest_storages = [x for x in invest_flows_all if isinstance(
        x[0], solph.components.GenericStorage)]

    df_invest_store = pd.DataFrame(index=['invest'])
    for flow in invest_storages:
        label = (flow[0].label, None)
        value = r[flow]["scalars"]['invest']
        df_invest_store[label] = value * p[flow]['scalars'][
            'investment_ep_costs']

    df_2 = pd.concat([df_invest_flows, df_invest_store], axis=1)
    invest_costs = df_2.sum().sum()

    d_costs.update({'invest': {'total': invest_costs,
                               'detail': df_2},
                    'total': invest_costs + var_costs})

    return d_costs
