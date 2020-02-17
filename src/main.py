"""
Aerodynamic Load Analizer and Plotter

@author: Willem Dekeyser
"""

# importing packages
import numpy as np
import plotly.graph_objects as go
import pandas as pd

# ------------------- Input parameters ----------------------------------
# Geometric inputs
Ca  = 0.547   # [m]  Chord length aileron   A: 0.547   B: 0.605
la  = 2.771   # [m]  Span aileron           A: 2.771   B: 2.661
x1  = 0.153   # [m]  Location hinge 1       A: 0.153   B: 0.172
x2  = 1.281   # [m]  Location hinge 2       A: 1.281   B: 1.211
x3  = 2.681   # [m]  Location hinge 3       A: 2.681   B: 2.591
xa  = 0.28    # [m]  Dist between A1 & A2   A: 0.28    B: 0.35
h   = 0.225   # [m]  Height aileron         A: 0.225   B: 0.205
tsk = 0.0011  # [m]  Skin thickness         A: 0.0011  B: 0.0011
tsp = 0.0029  # [m]  Spar thickness         A: 0.0029  B: 0.0029
tst = 0.0012  # [m]  Thickness stiffener    A: 0.0012  B: 0.0012
hst = 0.015   # [m]  Height stiffener       A: 0.015   B: 0.016
wst = 0.02    # [m]  Width stiffener        A: 0.02    B: 0.019
nst = 17      # [-]  Number of stiffeners   A: 17      B: 15

# Displacements
d1    = 0.01103  # [m]    Displacement hinge 1   A: 0.01103 B: 0.01154
d3    = 0.01642  # [m]    Displacement hinge 3   A: 0.01642 B: 0.01840
theta = 28       # [deg]  Max upward deflection  A: 26      B: 28

# Loads
P = 91.7  # [kN]  Load actuator 2     A: 91.7     # B: 97.4

