"""
oemof application for research project quarree100.

Based on the excel_reader example of oemof_examples repository:
https://github.com/oemof/oemof-examples

SPDX-License-Identifier: GPL-3.0-or-later
"""
import networkx as nx


def plot_graph(pos, grph):
    pos_keys = list()
    for i in pos.keys():
        pos_keys.append(i)

    bus_gas_keys = list()
    bus_el_keys = list()
    bus_heat_keys = list()
    trans_keys = list()
    nets_keys = list()
    store_keys = list()
    others_keys = list()

    for i in pos_keys:
        x = i[0:3]
        y = i[0:2]
        if x == 'bg_':
            bus_gas_keys.append(i)
        elif x == 'be_':
            bus_el_keys.append(i)
        elif x == 'bh_':
            bus_heat_keys.append(i)
        elif y == 'st':
            store_keys.append(i)
        elif y == 't_':
            trans_keys.append(i)
        elif y == 'n_':
            nets_keys.append(i)
        else:
            others_keys.append(i)
                                
    bus_gas_nodes = bus_gas_keys
    bus_el_nodes = bus_el_keys
    bus_heat_nodes = bus_heat_keys
    trans_nodes = trans_keys
    nets_nodes = nets_keys
    store_nodes = store_keys
    others_nodes = others_keys

    buses_el = grph.subgraph(bus_el_nodes)
    pos_buses_el = {x: pos[x] for x in bus_el_keys}
    
    buses_gas = grph.subgraph(bus_gas_nodes)
    pos_buses_gas = {x: pos[x] for x in bus_gas_keys}
    
    buses_heat = grph.subgraph(bus_heat_nodes)
    pos_buses_heat = {x: pos[x] for x in bus_heat_keys}
    
    trans = grph.subgraph(trans_nodes)
    pos_trans = {x: pos[x] for x in trans_keys}
    
    sources = grph.subgraph(nets_nodes)
    pos_sources = {x: pos[x] for x in nets_keys}
    
    store = grph.subgraph(store_nodes)
    pos_store = {x: pos[x] for x in store_keys}

    others = grph.subgraph(others_nodes)
    pos_others = {x: pos[x] for x in others_keys}
    
    sizenodes = 500

    nx.draw(grph, pos=pos, node_shape='1', prog='neato', with_labels=True,
            node_color='#ffffff', edge_color='#CFCFCF', node_size=sizenodes,
            arrows=True)
    nx.draw(buses_el, pos=pos_buses_el, node_shape='p', node_color='#0049db',
            node_size=sizenodes)
    nx.draw(buses_gas, pos=pos_buses_gas, node_shape='p', node_color='#f2e60e',
            node_size=sizenodes)
    nx.draw(buses_heat, pos=pos_buses_heat, node_shape='p',
            node_color='#f95c8b', node_size=sizenodes)
    nx.draw(trans, pos=pos_trans, node_shape='s', node_color='#85a8c2',
            node_size=sizenodes)
    nx.draw(sources, pos=pos_sources, node_shape='P', node_color='#70210c',
            node_size=sizenodes)
    nx.draw(store, pos=pos_store, node_shape='o', node_color='#ac88ff',
            node_size=sizenodes)
    nx.draw(others, pos=pos_others, node_shape='v', node_color='#71f442',
            node_size=sizenodes)
    return
