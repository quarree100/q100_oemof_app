"""
oemof application for research project quarree100.

Based on the excel_reader example of oemof_examples repository:
https://github.com/oemof/oemof-examples

SPDX-License-Identifier: GPL-3.0-or-later
"""

from oemof.graph import create_nx_graph
import networkx as nx
from matplotlib import pyplot as plt



def draw_graph(grph, edge_labels=True, node_color='#AFAFAF',
               edge_color='#CFCFCF', plot=True, node_size=2000,
               with_labels=True, arrows=True, layout='neato'):
    """
    Parameters
    ----------
    grph : networkxGraph
        A graph to draw.
    edge_labels : boolean
        Use nominal values of flow as edge label
    node_color : dict or string
        Hex color code oder matplotlib color for each node. If string, all
        colors are the same.

    edge_color : string
        Hex color code oder matplotlib color for edge color.

    plot : boolean
        Show matplotlib plot.

    node_size : integer
        Size of nodes.

    with_labels : boolean
        Draw node labels.

    arrows : boolean
        Draw arrows on directed edges. Works only if an optimization_model has
        been passed.
    layout : string
        networkx graph layout, one of: neato, dot, twopi, circo, fdp, sfdp.
    """
    if type(node_color) is dict:
        node_color = [node_color.get(g, '#AFAFAF') for g in grph.nodes()]

    # set drawing options
    options = {
        'prog': 'dot',
        'with_labels': with_labels,
        'node_color': node_color,
        'edge_color': edge_color,
        'node_size': node_size,
        'arrows': arrows
    }

    # try to use pygraphviz for graph layout
    try:
        import pygraphviz
        pos = nx.drawing.nx_agraph.graphviz_layout(grph, prog=layout)
    except ImportError:
        logging.error('Module pygraphviz not found, I won\'t plot the graph.')
        return

    # draw graph
    nx.draw(grph, pos=pos, **options)

    # add edge labels for all edges
    if edge_labels is True and plt:
        labels = nx.get_edge_attributes(grph, 'weight')
        nx.draw_networkx_edge_labels(grph, pos=pos, edge_labels=labels)

    # show output
    if plot is True:
        plt.show()