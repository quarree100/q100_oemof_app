# -*- coding: utf-8 -*-
"""Additional constraints to be used in an oemof energy model.
This file is part of project oemof (github.com/oemof/oemof). It's copyrighted
by the contributors recorded in the version control history of the file,
available from its original location oemof/oemof/solph/constraints.py
SPDX-License-Identifier: GPL-3.0-or-later
"""

import pyomo.environ as po


def emission_limit_dyn(om, flows=None, limit=None):
    """Set a global limit for emissions. The emission attribute has to be added
    to every flow you want to take into account.
    .. math:: \sum_{F_E} \sum_{T} flow(i,o,t) \cdot emission_factor(i,o,t)
               \cdot \tau \leq limit
    With `F_E` being the set of flows considered for the emission limit and
    `T` being the set of timestepsself.
    Total total emissions after optimization can be retrieved calling the
    :attr:`om.oemof.solph.Model.total_emissions()`.
    Parameters
    ----------
    om : oemof.solph.Model
        Model to which constraints are added.
    flows : dict
        Dictionary holding the flows that should be considered in constraint.
        Keys are (source, target) objects of the Flow. If no dictionary is
        given all flows containing the 'emission_factor' attribute will be
        used.
    limit : numeric
        Absolute emission limit for the energy system.
    Note
    ----
    Flow objects required an emission attribute!
    """
    if flows is None:
        flows = {}
        for (i, o) in om.flows:
            if hasattr(om.flows[i, o], 'emission_factor'):
                flows[(i, o)] = om.flows[i, o]
    else:
        for (i, o) in flows:
            if not hasattr(flows[i, o], 'emission_factor'):
                raise AttributeError(
                    ('Flow with source: {0} and target: {1} '
                     'has no attribute emission_factor.').format(i.label,
                                                                 o.label))

    om.total_emissions =  po.Expression(
        expr=sum(om.flow[inflow, outflow, t] * om.timeincrement[t] *
                 om.flows[inflow, outflow].emission_factor[t]
                 for (inflow, outflow) in flows
                 for t in om.TIMESTEPS))

    om.emission_limit = po.Constraint(expr=om.total_emissions <= limit)
