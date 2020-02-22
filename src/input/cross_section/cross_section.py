"""
Title: Cross Section Information

Author: Group A13
"""

# import packages
import numpy as np
import matplotlib.pyplot as plt
from src.input.general.discrete_input import input_dict


class CrossSection:
    """ get all the geometrical information for the aircraft chosen and output properties """

    def __init__(self, discrete_dict, aircraft):
        self.input = discrete_dict
        self.aircraft = aircraft

    def stiffener_spacing(self):

        # input required
        h = self.input['h'][self.aircraft]
        c_a = self.input['Ca'][self.aircraft]
        spacing_circle = self.input['nst_circle'][self.aircraft] + 1
        spacing_triangle = self.input['nst_triangle'][self.aircraft] + 2

        # function
        perimeter_semicircle = np.pi * h
        perimeter_triangle = 2 * np.sqrt((c_a - h) * 2 + h * 2)
        stiffener_spacing_semicircle = perimeter_semicircle / spacing_circle
        stiffener_spacing_triangle = perimeter_triangle / spacing_triangle

        return stiffener_spacing_triangle, stiffener_spacing_semicircle, perimeter_semicircle, perimeter_triangle

    def boom_locations(self):

        # input required
        h = self.input['h'][self.aircraft]
        c_a = self.input['Ca'][self.aircraft]
        stiffener_spacing_semicircle = self.stiffener_spacing()[1]
        spacing_circle = self.input['nst_circle'][self.aircraft] + 1
        spacing_triangle = self.input['nst_triangle'][self.aircraft] + 2

        # function
        y_lst = []
        z_lst = []

        for i in range(spacing_circle//2):
            theta = np.radians(i * stiffener_spacing_semicircle / (np.pi * h) * 180)
            delta_y = h * np.sin(theta)
            delta_z = h - h * np.cos(theta)
            y_lst.append(delta_y)
            z_lst.append(-delta_z)

        for i in range(1, spacing_triangle//2):
            y = h - i * h / (spacing_triangle//2)
            z = -h - i * (c_a - h) / (spacing_triangle//2)
            y_lst.append(y)
            z_lst.append(z)

        reverse_z = z_lst[::-1]
        reverse_y = y_lst[::-1]

        for i in range(len(reverse_z) - 1):
            z_lst.append(reverse_z[i])
            y_lst.append(-reverse_y[i])

        return z_lst, y_lst

    def stiffener_area(self):

        # input required
        w = self.input['wst'][self.aircraft]
        h = self.input['hst'][self.aircraft]
        t = self.input['tst'][self.aircraft]

        # function
        area = w * t + (h-t) * t

        return area

    def get_centroid(self):

        # input required
        c_a = self.input['Ca'][self.aircraft]
        t_sk = self.input['tsk'][self.aircraft]
        h = self.input['h'][self.aircraft]
        z_lst = self.boom_locations()[0]
        a_st = self.stiffener_area()
        n_st = self.input['nst_circle'][self.aircraft] + self.input['nst_triangle'][self.aircraft]

        # function
        yc = 0
        stiffener = sum([i * a_st for i in z_lst])
        triangle = -2 * (h + (c_a - h) / 2) * np.sqrt((c_a - h) * 2 + h * 2) * t_sk
        semicircle = -h * (1 - 2 / np.pi) * np.pi*(h * 2 - (h - t_sk) * 2) / 2
        spar = -t_sk * h * 2 * h

        zc = (stiffener + semicircle + triangle + spar) / (n_st * a_st + np.sqrt((c_a - h) * 2 + h * 2) * t_sk * 2 + np.pi*(
            h * 2 - (h - t_sk) * 2) / 2 + t_sk * 2 * h)

        return yc, zc

    def get_incl(self):

        # get input
        c_a = self.input['Ca'][self.aircraft]
        h = self.input['h'][self.aircraft]

        return np.sqrt((c_a - h) ** 2 + h ** 2)

    def get_moments_inertia(self):

        # input information
        c_a = self.input['Ca'][self.aircraft]
        t_sk = self.input['tsk'][self.aircraft]
        h = self.input['h'][self.aircraft]
        l_a = self.input['la'][self.aircraft]
        t_sp = self.input['tsp'][self.aircraft]
        z_lst = self.boom_locations()[0]
        y_lst = self.boom_locations()[1]
        a_st = self.stiffener_area()
        yc = self.get_centroid()[0]
        zc = self.get_centroid()[1]
        incl = self.get_incl()

        stif_z = sum([(i - yc) ** 2 * a_st for i in y_lst])
        triangle_z = ((2 * incl) ** 3 * t_sk / 12) * ((h) / incl) ** 2
        spar_z = (2 * t_sp / 12) * (2 * h) ** 3
        semic_z = 0.5 * np.pi * h ** 3 * t_sk / 8

        i_zz = stif_z + triangle_z + spar_z + semic_z

        stff_y = sum([(i - zc) ** 2 * a_st for i in z_lst])
        triangle_y = 2 / 12 * t_sk * incl ** 3 * ((c_a - h) / incl) ** 2 + 2 * incl * t_sk * (
                    -h - (c_a - h) / 2 - zc) ** 2
        spar_y = (2 * h / 12) * t_sk ** 3 + 2 * h * t_sp * (-h - zc) ** 2
        semic_y = h ** 3 * t_sk * (np.pi / 2 - 4 / np.pi) + np.pi * h * t_sk * ((-h + 2 * h / np.pi) - zc) ** 2

        i_yy = stff_y + spar_y + semic_y + triangle_y
        i_xx = 1 / 12 * l_a * c_a ** 3

        return i_zz, i_xx, i_yy

    def get_shear_flow(self, segment, b, Sy, n):

        # input data
        t_sk = self.input['tsk'][self.aircraft]
        h = self.input['h'][self.aircraft]
        t_sp = self.input['tsp'][self.aircraft]
        y_lst = self.boom_locations()[1]
        a_st = self.stiffener_area()
        i_zz = self.get_moments_inertia()[0]
        incl = self.get_incl()

        def integrate(a, t, num, fx):
            """ enter function in the form lambda x:f(x) """

            f = fx
            h_i = (t - a) / num
            A = 0.5 * h * (f(a) + f(t))
            for i in range(1, num):
                A += h_i * (f(a + i * h_i))
            return A

        qbl = []
        qb1t = (-Sy / i_zz) * (integrate(0, 0.5 * np.pi, 100, lambda x: h ** 2 * t_sk * np.sin(x)) + sum(
            [a_st * i for i in (y_lst[0:3])]))
        qb2t = (-Sy / i_zz) * (integrate(0, h, 100, lambda x: t_sp * x))
        qb3t = (-Sy / i_zz) * (integrate(0, incl, 100, lambda x: (h - (h / incl) * x) * t_sk) + sum(
            [a_st * i for i in (y_lst[3:9])])) + qb1t + qb2t
        qb4t = (-Sy / i_zz) * (integrate(0, incl, 100, lambda x: (- (h / incl) * x) * t_sk) + sum(
            [a_st * i for i in (y_lst[9:15])])) + qb3t
        qb5t = (-Sy / i_zz) * (integrate(0, -h, 100, lambda x: t_sp * x))
        qb6t = (-Sy / i_zz) * (integrate(-0.5 * np.pi, 0, 100, lambda x: h ** 2 * t_sk * np.sin(x)) + sum(
            [a_st * i for i in (y_lst[15:17])])) + qb4t - qb5t
        h_seg = b / ((len(segment) * n) - 1)

        ds = 0
        for segment in segment:
            for i in range(n):
                b = h_seg * (i + ds)
                # upper part semi circle
                if segment <= 2:
                    qb = (-Sy / i_zz) * (integrate(0, b, 100, lambda x: h ** 2 * t_sk * np.sin(x)) + sum(
                        [a_st * i for i in (y_lst[0:segment + 1])]))
                # upper spar part
                elif segment == 3:
                    qb = (-Sy / i_zz) * (integrate(0, b, 100, lambda x: t_sp * x))
                # upper triangular part
                elif 4 <= segment <= 10:
                    if segment == 4:
                        qb = (-Sy / i_zz) * (integrate(0, b, 100, lambda x: (h - (h / incl) * x) * t_sk)) + qb1t + qb2t
                    else:
                        qb = (-Sy / i_zz) * (integrate(0, b, 100, lambda x: (h - (h / incl) * x) * t_sk) + sum(
                            [a_st * i for i in (y_lst[3:segment - 1])])) + qb1t + qb2t
                # lower triangular part
                elif 11 <= segment <= 17:
                    if segment == 11:
                        qb = (-Sy / i_zz) * (integrate(0, b, 100, lambda x: - (h / incl) * x * t_sk)) + qb3t
                    else:
                        qb = (-Sy / i_zz) * (integrate(0, b, 100, lambda x: - (h / incl) * x * t_sk) + sum(
                            [a_st * i for i in (y_lst[9:segment - 2])])) + qb3t
                # lower spar part
                elif segment == 18:
                    qb = (-Sy / i_zz) * (integrate(0, -b, 100, lambda x: t_sk * x))
                # lower part semi circle
                else:
                    if segment == 19:
                        qb = (-Sy / i_zz) * (
                            integrate(-0.5 * np.pi, b, 100, lambda x: h ** 2 * t_sk * np.sin(x))) + qb4t - qb5t
                    else:
                        qb = (-Sy / i_zz) * (integrate(-0.5 * np.pi, b, 100, lambda x: h ** 2 * t_sk * np.sin(x)) + sum(
                            [a_st * i for i in (y_lst[15:segment - 4])])) + qb4t - qb5t
                qbl.append(qb)
            ds += n

        return qbl

    def get_shear_center(self):

        # get input data
        c_a = self.input['Ca'][self.aircraft]
        t_sk = self.input['tsk'][self.aircraft]
        h = self.input['h'][self.aircraft]
        t_sp = self.input['tsp'][self.aircraft]
        incl = self.get_incl()

        # define functions
        def second_integration(z_lst, q_lst):
            """ integration over number of points with known value,, approximated by trapezoidal rule, do for each wall! """

            step = z_lst[1] - z_lst[0]
            A = 0.5 * step * (q_lst[0] + q_lst[-1])
            for i in range(1, len(z_lst)):
                A += step * (q_lst[i])
            return A

        def second_int(zlist, qblist):
            for i, j in zip(zlist, qblist):
                A = 0
                A += second_integration(i, j)
            return A

        def add_constant_shearflow(qb1, qb2, qb3, qb4, qb5, qb6, qs01, qs02):
            qb1 = [i + qs01 for i in qb1]
            qb6 = [i + qs01 for i in qb6]
            qb2 = [i - qs01 + qs02 for i in qb2]
            qb5 = [i - qs01 + qs02 for i in qb5]
            qb4 = [i + qs02 for i in qb4]
            qb3 = [i + qs02 for i in qb3]
            return qb1, qb2, qb3, qb4, qb5, qb6

        # insert segment, b, Sy and n
        qb1 = self.get_shear_flow([0, 1, 2], 0.5 * np.pi, 1, 20)
        qb2 = self.get_shear_flow([3], h, 1, 40)
        qb3 = self.get_shear_flow([4, 5, 6, 7, 8, 9, 10], incl, 1, 20)
        qb4 = qb3[::-1]
        qb5 = qb2
        qb6 = qb1[::-1]

        # points along line of integration (s)
        s_co1 = np.linspace(0, np.pi * h / 2, 60)
        s_co2 = np.linspace(0, h, 40)
        s_co3 = np.linspace(0, incl, 140)
        s_co4 = s_co3
        s_co5 = s_co2
        s_co6 = s_co1

        # testing function
        # A=second_integration([np.radians(i) for i in np.linspace(0,90,1000)],
        # [np.cos(np.radians(i)) for i in np.linspace(0,90,1000)])

        qblist1 = [[i / t_sk for i in qb1], [-i / t_sp for i in qb2], [-i / t_sp for i in qb5], [i / t_sk for i in qb6]]
        zlist1 = [s_co1, s_co2, s_co5, s_co6]

        qblist2 = [[i / t_sp for i in qb2], [i / t_sp for i in qb5], [i / t_sk for i in qb3], [i / t_sk for i in qb4]]
        zlist2 = [s_co2, s_co5, s_co3, s_co4]

        a3 = second_int(zlist1, qblist1)
        b3 = second_int(zlist2, qblist2)
        a1 = np.pi * h / t_sk + 2 * h / t_sp
        a2 = -2 * h / t_sp
        b1 = -2 * h / t_sp
        b2 = 2 * (incl / t_sk) + 2 * h / t_sp

        A = np.array([[a1, b1], [a2, b2]])
        g = np.array([-a3, -b3])
        solution = np.linalg.solve(A, g)
        qs01 = solution[0]
        qs02 = solution[1]

        qb1, qb2, qb3, qb4, qb5, qb6 = add_constant_shearflow(qb1, qb2, qb3, qb4, qb5, qb6, qs01, qs02)

        m_2 = ((c_a - h) / incl) * h * -second_integration(s_co3, qb3) + ((c_a - h) / incl) * h * second_integration(s_co4, qb4) + 2 * h * second_integration(s_co1, qb1)

        shear_center = - h - m_2

        return shear_center

    """ ============================ Plotting and reporting results ============================ """

    def plot_cross_section(self):
        x_axis = self.boom_locations()[0]
        y_axis = self.boom_locations()[1]
        centroid = self.get_centroid()
        shear_center = self.get_shear_center()

        # plot boom points
        plt.figure(1)
        plt.title("Aileron Cross Section Plot")
        plt.scatter(x_axis, y_axis, color='g', label='stiffeners')
        plt.scatter(centroid[1], centroid[0], color='r', label='centroid')
        plt.scatter(shear_center, 0, color='b', label='shear center')
        plt.grid()
        plt.legend()
        plt.show()

        return 0

    def get_all(self):
        # return a cross section report as dict
        all_dict = {
            'area_st': CrossSection.stiffener_area(self),
            'shear_center': CrossSection.get_shear_center(self),
            'centroid': CrossSection.get_centroid(self),
            'i_zz': CrossSection.get_moments_inertia(self)[0],
            'i_yy': CrossSection.get_moments_inertia(self)[1],
            'i_xx': CrossSection.get_moments_inertia(self)[2]
        }

        return all_dict

    def get_report(self):
        print("\nCross section input information for aircraft aileron\n")
        print(self.get_all())
        print("\nPlotting ...\n")
        self.plot_cross_section()
        return 0


# ==================================================================================================
# debugging setting
DEBUG = False

if DEBUG:
    cross_section = CrossSection(input_dict, 'A')
    cross_section.get_report()
