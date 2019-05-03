# -*- coding: utf-8 -*-

"""This module is designed to hold custom components with their classes and
associated individual constraints (blocks) and groupings. Therefore this
module holds the class definition and the block directly located by each other.

This file is part of project oemof (github.com/oemof/oemof). It's copyrighted
by the contributors recorded in the version control history of the file,
available from its original location oemof/oemof/solph/custom.py

SPDX-License-Identifier: GPL-3.0-or-later
"""

from pyomo.core.base.block import SimpleBlock
from pyomo.environ import (Binary, Set, NonNegativeReals, Var, Constraint,
                           Expression, BuildAction)
import logging

from oemof.solph.network import Bus, Transformer
from oemof.solph.plumbing import sequence
from oemof.solph import Investment


class Heatpipe(Transformer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # general data
        self.length = kwargs.get('length')
        self.effiency = kwargs.get('effiency')

        # parameters for fix (no invest) option
        self.heat_loss = kwargs.get('heat_loss')

        # parameters for investment mode
        self.heat_loss_factor = kwargs.get('heat_loss_factor')

        # a = self.outputs.kwargs.get('investment')

        # self.investment = kwargs.get('investment')
        # self._invest_group = isinstance(self.investment, Investment)

        if len(self.inputs) > 1 or len(self.outputs) > 1:
            raise ValueError("Heatpipe must not have more than \
                             one input and one output!")

        for f in self.inputs.values():
            if f.nonconvex is not None:
                raise ValueError(
                    "Attribute `nonconvex` must be None for" +
                    " inflows of component `ElectricalLine`!")

        for f in self.outputs.values():
            if f.nonconvex is not None:
                raise ValueError(
                    "Attribute `nonconvex` must be None for" +
                    " outflows of component `ElectricalLine`!")

    def constraint_group(self):
        return HeatpipeInvestBlock
        # if self._invest_group is True:
        #     return HeatpipeInvestBlock
        # else:
        #     return HeatpipeBlock


class HeatpipeBlock(SimpleBlock):
    r"""Block representing a pipe of a district heating grid.
    :class:`~Heatpipe.Heatpipe`

    **The following constraints are created:**

        .. math::
            flow(n, o, t) =  flow(n, i, t) - loss(n, t) \cdot l(n) \newline
            \newline
            \forall t \\in  \textrm{TIMESTEPS}, \newline
            \forall n \\in  \textrm{ELECTRICAL\_LINES}.

    """

    CONSTRAINT_GROUP = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _create(self, group=None):
        """ Creates the linear constraint for the class:`Heatpipe`
        block.

        Parameters
        ----------
        group : list

        """
        if group is None:
            return None

        m = self.parent_block()

        self.HEATPIPES = Set(initialize=[n for n in group])

        # Defining Variables
        self.heat_loss_total = Var(self.HEATPIPES, m.TIMESTEPS,
                                    within=NonNegativeReals)

        def _heat_loss_rule(block, n, t):
            """Rule definition for constraint to connect the installed power
            and the heat loss:
            heat_loss = heat_loss_factor * installed_power
            """
            expr = 0
            expr += - block.heat_loss_total[n, t]
            expr += n.heat_loss * n.length
            return expr == 0
        self.heat_loss_equation = Constraint(self.HEATPIPES, m.TIMESTEPS,
                                             rule=_heat_loss_rule)

        def _relation_rule(block, n, t):
            """Link binary input and output flow to component outflow."""
            expr = 0
            expr += - m.flow[n, list(n.outputs.keys())[0], t]
            expr += m.flow[list(n.inputs.keys())[0], n, t]*n.effiency[t]
            expr += - block.heat_loss_total[n, t]
            return expr == 0

        self.relation = Constraint(self.HEATPIPES, m.TIMESTEPS,
                                   rule=_relation_rule)


class HeatpipeInvestBlock(SimpleBlock):
    r"""Block representing a pipe of a district heating grid.
    :class:`~Heatpipe.Heatpipe`

    **The following constraints are created:**

        .. math::
            flow(n, o, t) =  flow(n, i, t) - loss(n, t) \cdot l(n) \newline
            \newline
            \forall t \\in  \textrm{TIMESTEPS}, \newline
            \forall n \\in  \textrm{ELECTRICAL\_LINES}.

    """

    CONSTRAINT_GROUP = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _create(self, group=None):
        """ Creates the linear constraint for the class:`Heatpipe`
        block.

        Parameters
        ----------
        group : list

        """
        if group is None:
            return None

        m = self.parent_block()

        # Defining Sets
        self.INVESTHEATPIPES = Set(initialize=[n for n in group])

        # Defining Variables
        self.heat_loss_invest = Var(self.INVESTHEATPIPES, m.TIMESTEPS,
                                    within=NonNegativeReals)

        def _heat_loss_rule(block, n, t):
            """Rule definition for constraint to connect the installed power
            and the heat loss:
            heat_loss = heat_loss_factor * installed_power
            """
            expr = 0
            expr += - block.heat_loss_invest[n, t]
            expr += n.heat_loss_factor * n.length * m.InvestmentFlow.invest[
                n, list(n.outputs.keys())[0]]
            return expr == 0
        self.heat_loss_equation = Constraint(self.INVESTHEATPIPES, m.TIMESTEPS,
                                             rule=_heat_loss_rule)

        def _relation_rule(block, n, t):
            """Link binary input and output flow to component outflow."""
            expr = 0
            expr += - m.flow[n, list(n.outputs.keys())[0], t]
            expr += m.flow[list(n.inputs.keys())[0], n, t]*n.effiency[t]
            expr += - block.heat_loss_invest[n, t]
            return expr == 0

        self.relation = Constraint(self.INVESTHEATPIPES, m.TIMESTEPS,
                                   rule=_relation_rule)
