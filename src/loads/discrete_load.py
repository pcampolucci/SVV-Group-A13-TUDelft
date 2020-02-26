"""
Title: The script is based on the input dictionary values and the distributed loads from aero force
"""

# import packages
import numpy as np
from src.input.input import input_dict
from src.input.cross_section.cross_section import CrossSection
from src.loads.distributed_load import *
from src.input.input import Input
import tqdm as tqdm


class PointLoads:

    def __init__(self, aircraft):

        self.aircraft = aircraft
        self.input = input_dict
        self.stepsize = 0.1
        self.aero_load = Input(self.aircraft).aero_input()

    def get_discrete_input(self):

        x1 = self.input['x1'][self.aircraft]
        x2 = self.input['x2'][self.aircraft]
        x3 = self.input['x3'][self.aircraft]
        xa = self.input['xa'][self.aircraft]
        xa1 = self.input['xa1'][self.aircraft]
        xa2 = self.input['xa2'][self.aircraft]

        d1 = self.input['d1'][self.aircraft]
        d3 = self.input['d3'][self.aircraft]
        theta = self.input['theta'][self.aircraft]
        la = self.input['la'][self.aircraft]

        P = self.input['P'][self.aircraft]
        E = self.input['E'][self.aircraft]
        G = self.input['G'][self.aircraft]

        return x1, x2, x3, xa, xa1, xa2, theta, d1, d3, E, G, P, la, self.stepsize

    def get_distributed_loads_aero(self):

        # loads due to aerodynamic forces
        x1, x2, x3, xa, xa1, xa2, theta, d1, d3, E, G, P, la, step = self.get_discrete_input()
        load = self.aero_load
        stepsize = self.stepsize

        discrete_loads = get_discrete_load(la, load, stepsize)
        discrete_resultants = get_discrete_resultant(la, discrete_loads, stepsize)
        discrete_locations = get_discrete_location_resultant(la, discrete_resultants, discrete_loads, stepsize)
        discrete_moments = get_discrete_moment(discrete_resultants, discrete_locations)
        discrete_angles = get_discrete_angle(la, discrete_moments, stepsize)
        discrete_deflections = get_discrete_deflection(la, discrete_angles, stepsize)

        # forces
        Q_l = magnitude_resultant(la, discrete_resultants, self.stepsize)  # aero force at la
        # moments
        Mqz_l = moment_resultant(la, discrete_moments, self.stepsize)  # aero moment at la

        # deflections
        ddq_x2 = deflection_resultant(x2, discrete_deflections, self.stepsize)
        ddq_xa2 = deflection_resultant(xa2, discrete_deflections, self.stepsize)
        ddq_x1 = deflection_resultant(x1, discrete_deflections, self.stepsize)
        ddq_x3 = deflection_resultant(x3, discrete_deflections, self.stepsize)

        return Q_l, Mqz_l, ddq_x2, ddq_xa2, ddq_x1, ddq_x3

    def get_geometry(self):

        section = CrossSection(self.input, self.aircraft)

        # geometry
        dsch = section.get_shear_center()[0]  # distance hingeline shear center
        dsca_y = self.input['h'][self.aircraft]/2  # actuator to S.C. in y dir
        dsca_z = dsch  # actuator to S.C. in z dir
        Izz = section.get_moments_inertia()[0]
        Iyy = section.get_moments_inertia()[2]
        J = section.get_j()
        z = self.input['la'][self.aircraft]/2  # datum twist

        return dsch, dsca_y, dsca_z, Izz, Iyy, J, z

    def get_discrete_loads(self):

        """ INPUT: la, x1, x2, x3, xa, xa1, xa2, d1, d3, E, G, q, Mqz, Tq, qq, qqt, dsch, dsca_y, dsca_z, Izz, Iyy, J, z
            OUTPUT: F_z1 , F_z2, F_z3, F_a, F_y1, F_y2, F_y3, c1, c2, c3, c4, c5 """

        # input values
        x1, x2, x3, xa, xa1, xa2, theta, d1, d3, E, G, P, la, step = self.get_discrete_input()
        Q_l, Mqz_l, ddq_x2, ddq_xa2, ddq_x1, ddq_x3 = self.get_distributed_loads_aero()
        dsch, dsca_y, dsca_z, Izz, Iyy, J, z = self.get_geometry()

        # function
        cte_v = -1 / (E * Izz)  # cte in v deflection formula
        cte_w = -1 / (E * Iyy)  # cte in w deflection formula
        cte_T = 1 / (G * J)  # cte in torsion equation
        # order variables matrix
        # F_z1 , F_z2, F_z3, F_a, F_y1, F_y2, F_y3, c1, c2, c3, c4, c5

        left_column = np.array([
            [la - x1, la - x2, la - x3, np.cos(theta) * (la - xa1), 0, 0, 0, 0, 0, 0, 0, 0],
            # Moment around y equation at la
            [0, 0, 0, np.sin(theta) * (la - xa1), la - x1, la - x2, la - x3, 0, 0, 0, 0, 0],
            # Moment around z equation at la
            [-dsch, dsch, -dsch, dsca_y * np.cos(theta) + dsca_z * np.sin(theta), 0, 0, 0, 0, 0, 0, 0, 0],
            # Torque aka Moment around x at la
            [1, 1, 1, np.cos(theta), 0, 0, 0, 0, 0, 0, 0, 0],  # force/shear z
            [0, 0, 0, np.sin(theta), 1, 1, 1, 0, 0, 0, 0, 0],  # force/shear y
            [0, 0, 0, cte_v / 6 * np.sin(theta) * (x2 - xa1) ** 3, cte_v / 6 * (x2 - x1) ** 3, 0, 0, x2, 1, 0, 0, 0],
            # v deflection at x2
            [0, 0, 0, cte_v / 6 * np.sin(theta) * (xa2 - xa1) ** 3, cte_v / 6 * (xa2 - x1) ** 3,
             cte_v / 6 * (xa2 - x2) ** 3, 0, xa2, 1, 0, 0, 0],  # v deflection at xa2
            [cte_w / 6 * (x2 - x1) ** 3, 0, 0, cte_w / 6 * np.cos(theta) * (x2 - xa1) ** 3, 0, 0, 0, 0, 0, x2, 1, 0],
            # w deflection at x2
            [0, 0, 0, 0, 0, 0, 0, x1, 1, 0, 0, (z - x1)],  # v + theta(z-x) deflection at x1
            [-cte_T * dsch * (x3 - x1) * (z - x3), cte_T * dsch * (x3 - x2) * (z - x3), 0,
             cte_v / 6 * np.sin(theta) * (x3 - xa1) ** 3 + cte_T * (dsca_y * np.cos(theta) + dsca_z * np.sin(theta)) * (
                         z - x3),
             cte_v / 6 * (x3 - x1) ** 3, cte_v / 6 * (x3 - x2) ** 3, 0, x3, 1, 0, 0, (z - x3)],
            # v + theta(z-x) deflection at x3
            [0, 0, 0, 0, 0, 0, 0, 0, 0, x1, 1, (z - x1)],  # w + theta(z-x) deflection at x1
            [cte_w / 6 * (x3 - x1) ** 3 - cte_T * dsch * (x3 - x1) * (z - x3),
             cte_w / 6 * (x3 - x2) ** 3 + cte_T * dsch * (x3 - x2) * (z - x3), 0,
             cte_v / 6 * np.cos(theta) * (x3 - xa1) ** 3 + cte_T * (dsca_y * np.cos(theta) + dsca_z * np.sin(theta)) * (
                         z - x3),
             0, 0, 0, 0, 0, x3, 1, (z - x3)]  # w + theta(z-x) deflection at x3
        ])

        right_column = np.array([
            [P * np.cos(theta) * (la - xa2)],  # Moment around y equation at la
            [P * np.sin(theta) * (la - xa2) + Mqz_l],  # Moment around z equation at la
            [P * (dsca_y * np.cos(theta) + dsca_z * np.sin(theta))],  # Torque aka Moment around x at la
            [P * np.cos(theta)],  # force/shear z
            [P * np.sin(theta) + Q_l],  # force/shear y
            [cte_v * ddq_x2],  # v deflection at x2 qq at x2
            [cte_v * ddq_xa2],  # v deflection at xa2  qq at x2
            [0],  # w deflection at x2
            [d1 * np.sin(theta) + cte_v * ddq_x1],  # v deflection at x1  qq at x1
            [d3 * np.sin(theta) + cte_v * (1 / 6 * P * np.sin(theta) * (x3 - xa2) ** 3 + ddq_x3)
             + (cte_T * (P * (dsca_y * np.cos(theta) + dsca_z * np.sin(theta)) * (x3 - x1))) * (z - x3)],
            # v deflection at x3 qqt qq at x3
            [d1 * np.cos(theta)],  # w deflection at x1
            [d3 * np.cos(theta) + cte_w / 6 * P * np.cos(theta) * (x3 - xa2) ** 3
             + (cte_T * (P * (dsca_y * np.cos(theta) + dsca_z * np.sin(theta)) * (x3 - x1))) * (z - x3)]
            # w deflection at x3
        ])

        F_z1, F_z2, F_z3, F_a, F_y1, F_y2, F_y3, c1, c2, c3, c4, c5 = np.linalg.solve(left_column, right_column)

        return F_z1, F_z2, F_z3, F_a, F_y1, F_y2, F_y3, c1, c2, c3, c4, c5




