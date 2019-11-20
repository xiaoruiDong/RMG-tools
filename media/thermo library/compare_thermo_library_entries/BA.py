#!/usr/bin/env python
# encoding: utf-8

name = "BA"
shortDesc = ""
longDesc = """
ARC v1.1.0
ARC project BA

Levels of theory used:

Conformers:       b3lyp/6-31g(d,p) empiricaldispersion=gd3bj
TS guesses:       b3lyp/6-31g(d,p) empiricaldispersion=gd3bj
Composite method: cbs-qb3 (using a fine grid)
Frequencies:      b3lyp/cbsb7
Rotor scans:      b3lyp/cbsb7
Using bond additivity corrections for thermo

Using the following ESS settings: {'gaussian': ['c3ddb']}

Considered the following species and TSs:
Species tBA (run time: 9:03:29)

Overall time since project initiation: 00:37:35
"""
entry(
    index = 0,
    label = "tBA",
    molecule = 
"""
1  O u0 p2 c0 {3,S} {8,S}
2  O u0 p2 c0 {8,D}
3  C u0 p0 c0 {1,S} {4,S} {5,S} {6,S}
4  C u0 p0 c0 {3,S} {9,S} {10,S} {11,S}
5  C u0 p0 c0 {3,S} {12,S} {13,S} {14,S}
6  C u0 p0 c0 {3,S} {15,S} {16,S} {17,S}
7  C u0 p0 c0 {8,S} {18,S} {19,S} {20,S}
8  C u0 p0 c0 {1,S} {2,D} {7,S}
9  H u0 p0 c0 {4,S}
10 H u0 p0 c0 {4,S}
11 H u0 p0 c0 {4,S}
12 H u0 p0 c0 {5,S}
13 H u0 p0 c0 {5,S}
14 H u0 p0 c0 {5,S}
15 H u0 p0 c0 {6,S}
16 H u0 p0 c0 {6,S}
17 H u0 p0 c0 {6,S}
18 H u0 p0 c0 {7,S}
19 H u0 p0 c0 {7,S}
20 H u0 p0 c0 {7,S}
""",
    thermo = NASA(
        polynomials = [
            NASAPolynomial(coeffs=[3.31774,0.0574826,-5.00231e-06,-2.9095e-08,1.45227e-11,-65852.9,13.1464], Tmin=(10,'K'), Tmax=(870.031,'K')),
            NASAPolynomial(coeffs=[4.58602,0.0633305,-3.52197e-05,9.48807e-09,-9.97354e-13,-66515.6,4.66404], Tmin=(870.031,'K'), Tmax=(3000,'K')),
        ],
        Tmin = (10,'K'),
        Tmax = (3000,'K'),
        E0 = (-547.599,'kJ/mol'),
        Cp0 = (33.2579,'J/(mol*K)'),
        CpInf = (457.296,'J/(mol*K)'),
    ),
    shortDesc = """""",
    longDesc = 
"""
Bond corrections: {'C-O': 2, 'C-C': 4, 'C=O': 1, 'C-H': 12}
1D rotors:
pivots: [1, 2], dihedral: [9, 1, 2, 3], rotor symmetry: 3, max scan energy: 0.82 kJ/mol (set as a FreeRotor)
pivots: [2, 4], dihedral: [1, 2, 4, 5], rotor symmetry: 1, max scan energy: 54.41 kJ/mol
pivots: [4, 5], dihedral: [2, 4, 5, 6], rotor symmetry: 3, max scan energy: 17.79 kJ/mol
pivots: [5, 6], dihedral: [4, 5, 6, 12], rotor symmetry: 3, max scan energy: 13.78 kJ/mol
pivots: [5, 7], dihedral: [4, 5, 7, 15], rotor symmetry: 3, max scan energy: 13.83 kJ/mol
pivots: [5, 8], dihedral: [4, 5, 8, 18], rotor symmetry: 3, max scan energy: 13.66 kJ/mol


External symmetry: 1, optical isomers: 1

Geometry:
{'symbols': ('C', 'C', 'O', 'O', 'C', 'C', 'C', 'C', 'H', 'H', 'H', 'H', 'H', 'H', 'H', 'H', 'H', 'H', 'H', 'H'), 'isotopes': (12, 12, 16, 16, 12, 12, 12, 12, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1), 'coords': ((2.964862, 0.138792, 0.426981), (1.518598, 0.540619, 0.609631), (1.140958, 1.420212, 1.344369), (0.724001, -0.225105, -0.164928), (-0.74492, -0.053458, -0.189144), (-1.326696, -0.333432, 1.198961), (-1.099089, 1.347071, -0.695869), (-1.186067, -1.121769, -1.189607), (3.095549, -0.912942, 0.691004), (3.253099, 0.250303, -0.620596), (3.595201, 0.763298, 1.056565), (-1.008244, 0.418667, 1.918683), (-2.418723, -0.327953, 1.144275), (-1.010035, -1.318744, 1.550749), (-0.624008, 1.531419, -1.662918), (-2.18156, 1.423096, -0.830098), (-0.778709, 2.113393, 0.007816), (-0.888111, -2.114802, -0.846202), (-0.729597, -0.94444, -2.165829), (-2.27254, -1.104485, -1.304786))}
""",
)

