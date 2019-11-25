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
Species CCCCO[O] (run time: 20:45:17)

Overall time since project initiation: 1.0 days, 00:05:18
"""
entry(
    index = 0,
    label = "CCCCO[O]",
    molecule = 
"""
multiplicity 2
1  O u0 p2 c0 {2,S} {5,S}
2  O u1 p2 c0 {1,S}
3  C u0 p0 c0 {4,S} {5,S} {9,S} {10,S}
4  C u0 p0 c0 {3,S} {6,S} {7,S} {8,S}
5  C u0 p0 c0 {1,S} {3,S} {11,S} {12,S}
6  C u0 p0 c0 {4,S} {13,S} {14,S} {15,S}
7  H u0 p0 c0 {4,S}
8  H u0 p0 c0 {4,S}
9  H u0 p0 c0 {3,S}
10 H u0 p0 c0 {3,S}
11 H u0 p0 c0 {5,S}
12 H u0 p0 c0 {5,S}
13 H u0 p0 c0 {6,S}
14 H u0 p0 c0 {6,S}
15 H u0 p0 c0 {6,S}
""",
    thermo = NASA(
        polynomials = [
            NASAPolynomial(coeffs=[3.32408,0.0676577,-0.00019658,4.18099e-07,-3.18915e-10,-11033.8,12.7824], Tmin=(10,'K'), Tmax=(447.968,'K')),
            NASAPolynomial(coeffs=[1.78201,0.049391,-2.81443e-05,7.79059e-09,-8.40554e-13,-10574.2,22.5715], Tmin=(447.968,'K'), Tmax=(3000,'K')),
        ],
        Tmin = (10,'K'),
        Tmax = (3000,'K'),
        E0 = (-91.7551,'kJ/mol'),
        Cp0 = (33.2579,'J/(mol*K)'),
        CpInf = (340.893,'J/(mol*K)'),
    ),
    shortDesc = """""",
    longDesc = 
"""
Bond corrections: {'C-C': 3, 'C-H': 9, 'C-O': 1, 'O-O': 1}
1D rotors:
pivots: [1, 2], dihedral: [7, 1, 2, 3], rotor symmetry: 3, max scan energy: 11.99 kJ/mol
pivots: [2, 3], dihedral: [1, 2, 3, 4], rotor symmetry: 1, max scan energy: 22.82 kJ/mol
pivots: [3, 4], dihedral: [2, 3, 4, 5], rotor symmetry: 1, max scan energy: 19.32 kJ/mol
pivots: [4, 5], dihedral: [3, 4, 5, 6], rotor symmetry: 1, max scan energy: 10.48 kJ/mol


External symmetry: 1, optical isomers: 1

Geometry:
{'symbols': ('C', 'C', 'C', 'C', 'O', 'O', 'H', 'H', 'H', 'H', 'H', 'H', 'H', 'H', 'H'), 'isotopes': (12, 12, 12, 12, 16, 16, 1, 1, 1, 1, 1, 1, 1, 1, 1), 'coords': ((-2.179054, -0.143085, -0.307992), (-0.809688, -0.495143, 0.279242), (-0.70011, -0.158733, 1.772209), (0.662068, -0.513396, 2.338625), (0.66129, -0.155938, 3.755382), (1.814022, -0.432229, 4.328939), (-2.389708, 0.925649, -0.20639), (-2.229325, -0.392695, -1.370767), (-2.979319, -0.688736, 0.200664), (-0.027418, 0.039206, -0.272398), (-0.612731, -1.56342, 0.131683), (-0.88361, 0.909689, 1.927895), (-1.470745, -0.697988, 2.333245), (0.878492, -1.582632, 2.275993), (1.4731, 0.045549, 1.865517))}
""",
)

