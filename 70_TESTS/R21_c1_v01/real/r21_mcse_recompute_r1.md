# R21 Monte Carlo error and seed stability

Descriptive (plan section 6.1); the verdict is always the primary seed's. B = 40000; power mode recompute.

- H1 (bound form) at the reference set: True; share of alternative sets with the same: 1.0

## within_lt3d/t1 (20 sets)

- removal_stat B0: reference 0.0856834; empirical MC SE 0.000764947; A-B MC SE 0.00119548; range [0.0836754, 0.0865976]
- removal_stat B1: reference 0.0844658; empirical MC SE 0.00216522; A-B MC SE 0.00325493; range [0.0765223, 0.0858807]
- removal_stat B3: reference -0.0493033; empirical MC SE 1.24666e-05; A-B MC SE 2.42032e-05; range [-0.0493241, -0.0492733]
- removal_stat B4: reference 0.174395; empirical MC SE 0.000838302; A-B MC SE 0.00113189; range [0.172059, 0.175658]
- removal_stat B6: reference 0.16523; empirical MC SE 0.000865871; A-B MC SE 0.00172984; range [0.163074, 0.165956]
- removal_stat B9: reference 0.0371697; empirical MC SE 0.000804393; A-B MC SE 0.00102116; range [0.035008, 0.0382897]
- removal_stat RETUNED: reference 0.0679073; empirical MC SE 0.000667902; A-B MC SE 0.00113399; range [0.0661322, 0.0689579]
- Form B UB M* - B3 (level 0.987500): reference -0.7602; empirical MC SE 0.00012084; A-B MC SE 0.000269964; range [-0.760612, -0.760106]
- p_c M* - B3: reference 2.49994e-05; empirical MC SE 0; A-B MC SE 2.49994e-05; range [2.49994e-05, 2.49994e-05]
- HK1c UB M* PD7_primary: reference 0.0482489; empirical MC SE 3.73567e-05; A-B MC SE 5.9595e-05; range [0.0481587, 0.0483106]
- pooled LB M* PD7_primary: reference 0.0410687; empirical MC SE 1.90068e-05; A-B MC SE 1.93395e-05; range [0.0410379, 0.0410962]
- HK1c UB M* SD1_7_gap_le_5m: reference 0.0472535; empirical MC SE 8.94197e-05; A-B MC SE 0.000109591; range [0.0471317, 0.0474901]
- pooled LB M* SD1_7_gap_le_5m: reference 0.0301518; empirical MC SE 5.1415e-05; A-B MC SE 5.6294e-05; range [0.0301539, 0.0303832]
- HK1c UB M* PD_inpath: reference 0.0545964; empirical MC SE 0.00012957; A-B MC SE 0.000173886; range [0.0544218, 0.0549053]
- pooled LB M* PD_inpath: reference 0.0296279; empirical MC SE 7.71611e-05; A-B MC SE 7.59544e-05; range [0.0296245, 0.0298692]
- H3 p (this tracker; doubled): reference 4.99988e-05; empirical MC SE 0; A-B MC SE None; range [4.99988e-05, 4.99988e-05]
- H3 UB M*Jx - B3 (own level): reference -0.091699; empirical MC SE 0.000120032; A-B MC SE 0.00019829; range [-0.0919656, -0.0914807]
- statuses not identical in every set: 1; {"B4/SD1_7_gap_le_5m NoFlag": {"reference": true, "share_same": 0.8, "analysis": true}}
- power-family size changes: {"B0/SD1_7_gap_le_5m family size": {"reference": 10, "values": [9, 10], "by_set": [10, 10, 10, 10, 10, 10, 10, 9, 10, 9, 10, 9, 10, 9, 9, 10, 10, 10, 10, 10]}, "B0/PD_inpath family size": {"reference": 6, "values": [5, 6], "by_set": [6, 6, 6, 6, 5, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6]}, "B1/PD7_primary family size": {"reference": 18, "values": [18, 19], "by_set": [18, 18, 18, 18, 18, 18, 18, 19, 18, 18, 18, 18, 18, 18, 18, 18, 18, 18, 18, 18]}, "B1/SD1_7_gap_le_5m family size": {"reference": 8, "values": [7, 8], "by_set": [7, 7, 7, 7, 7, 7, 8, 7, 8, 8, 8, 7, 7, 7, 7, 8, 7, 8, 8, 8]}, "B3/SD1_7_gap_le_5m family size": {"reference": 3, "values": [3, 4], "by_set": [3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 4, 3]}, "B4/SD1_7_gap_le_5m family size": {"reference": 8, "values": [8, 9], "by_set": [8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 9, 8, 8, 8, 8]}, "B6/SD1_7_gap_le_5m family size": {"reference": 10, "values": [9, 10], "by_set": [10, 9, 10, 10, 9, 10, 10, 10, 10, 9, 9, 10, 10, 10, 9, 10, 10, 10, 10, 10]}, "RETUNED/SD1_7_gap_le_5m family size": {"reference": 10, "values": [9, 10], "by_set": [10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 9, 10, 10, 10, 9, 10, 9]}}
- cells with |t - q| < 0.2: B0/PD7_primary/pedestrian|long|static cells (21 sets), B4/PD7_primary/car|long|straight family (21 sets), B4/SD1_7_gap_le_5m/car|lat|turning cells (21 sets), B6/SD1_7_gap_le_5m/car|lat|turning cells (13 sets), B4/SD1_7_gap_le_5m/pedestrian|long|turning cells (8 sets), B0/PD7_primary/pedestrian|long|static family (2 sets), B6/SD1_7_gap_le_5m/car|lat|turning family (1 sets), B4/PD7_primary/car|long|straight cells (2 sets)

## within_lt3d/t3 (20 sets)

- removal_stat B0: reference -0.0424288; empirical MC SE 0.000190136; A-B MC SE 0.000406338; range [-0.0428198, -0.0420723]
- removal_stat B1: reference 0.00113277; empirical MC SE 0.000394977; A-B MC SE 0.000702292; range [0.000312562, 0.00146788]
- removal_stat B3: reference -0.0494671; empirical MC SE 1.18259e-05; A-B MC SE 1.97289e-05; range [-0.049445, -0.0494047]
- removal_stat B4: reference 0.146664; empirical MC SE 0.000627563; A-B MC SE 0.000775367; range [0.144711, 0.147695]
- removal_stat B6: reference 0.0871876; empirical MC SE 0.00052641; A-B MC SE 0.000718154; range [0.0856761, 0.08786]
- removal_stat B9: reference 0.035014; empirical MC SE 0.000606426; A-B MC SE 0.00108019; range [0.0337001, 0.0359359]
- removal_stat RETUNED: reference 0.0630788; empirical MC SE 0.000613955; A-B MC SE 0.000926411; range [0.0616232, 0.0639184]
- Form B UB M* - B0 (level 0.993750): reference -0.581885; empirical MC SE 0.000315634; A-B MC SE 0.000395238; range [-0.582647, -0.581442]
- p_c M* - B0: reference 2.49994e-05; empirical MC SE 0; A-B MC SE 2.49994e-05; range [2.49994e-05, 2.49994e-05]
- Form B UB M* - B3 (level 0.993750): reference -0.66643; empirical MC SE 0.00027049; A-B MC SE 0.000390201; range [-0.666667, -0.665554]
- p_c M* - B3: reference 2.49994e-05; empirical MC SE 0; A-B MC SE 2.49994e-05; range [2.49994e-05, 2.49994e-05]
- HK1c UB M* PD7_primary: reference 0.0471001; empirical MC SE 2.88191e-05; A-B MC SE 4.87674e-05; range [0.0470277, 0.0471341]
- pooled LB M* PD7_primary: reference 0.040197; empirical MC SE 1.54919e-05; A-B MC SE 1.85652e-05; range [0.0401517, 0.0402187]
- HK1c UB M* SD1_7_gap_le_5m: reference 0.0411573; empirical MC SE 7.3518e-05; A-B MC SE 9.43752e-05; range [0.0410789, 0.0413269]
- pooled LB M* SD1_7_gap_le_5m: reference 0.0255261; empirical MC SE 6.49256e-05; A-B MC SE 5.14489e-05; range [0.0253546, 0.0256474]
- HK1c UB M* PD_inpath: reference 0.0520995; empirical MC SE 9.86017e-05; A-B MC SE 0.000142898; range [0.0518288, 0.0521816]
- pooled LB M* PD_inpath: reference 0.0321929; empirical MC SE 6.04947e-05; A-B MC SE 5.97902e-05; range [0.0320525, 0.0322632]
- H3 p (this tracker; doubled): reference 1; empirical MC SE 0; A-B MC SE None; range [1, 1]
- H3 UB M*Jx - B0 (own level): reference 0.0553965; empirical MC SE 0.000149067; A-B MC SE 0.000212649; range [0.0552061, 0.055844]
- H3 UB M*Jx - B3 (own level): reference -0.0284709; empirical MC SE 0.000150026; A-B MC SE 0.000181294; range [-0.0285113, -0.0280061]
- statuses not identical in every set: 1; {"B1/PD7_primary NoFlag": {"reference": true, "share_same": 0.95, "analysis": true}}
- power-family size changes: {"B1/SD1_7_gap_le_5m family size": {"reference": 6, "values": [5, 6], "by_set": [5, 6, 6, 5, 5, 5, 6, 6, 6, 5, 5, 5, 5, 6, 5, 5, 5, 5, 5, 6]}, "B4/SD1_7_gap_le_5m family size": {"reference": 8, "values": [7, 8], "by_set": [7, 7, 7, 8, 8, 8, 7, 8, 7, 8, 7, 7, 8, 8, 7, 7, 7, 8, 8, 7]}, "RETUNED/SD1_7_gap_le_5m family size": {"reference": 7, "values": [6, 7], "by_set": [7, 7, 7, 7, 6, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7]}}
- cells with |t - q| < 0.2: B1/PD7_primary/car|long|new cells (20 sets), B1/PD7_primary/car|long|new family (21 sets), B4/PD7_primary/large|long|static family (18 sets), B4/SD1_7_gap_le_5m/large|long|straight cells (21 sets), B4/SD1_7_gap_le_5m/car|long|turning family (10 sets), B6/PD7_primary/car|lat|new cells (21 sets), RETUNED/PD7_primary/car|long|turning cells (21 sets), RETUNED/PD7_primary/car|long|straight family (21 sets), RETUNED/PD7_primary/car|long|straight cells (4 sets), B9/PD7_primary/large|long|new cells (4 sets)

## transfer_lt3d/t1 (20 sets)

- removal_stat B0: reference 0.0782696; empirical MC SE 0.00194642; A-B MC SE 0.000911605; range [0.0723493, 0.0791022]
- removal_stat B1: reference 0.111948; empirical MC SE 0.00642686; A-B MC SE 0.00912676; range [0.087352, 0.112546]
- removal_stat B3: reference -0.0484578; empirical MC SE 4.60075e-05; A-B MC SE 4.82617e-05; range [-0.0485535, -0.048398]
- removal_stat B4: reference 0.214088; empirical MC SE 0.00197771; A-B MC SE 0.00318631; range [0.207419, 0.214222]
- removal_stat B6: reference 0.198775; empirical MC SE 0.00139698; A-B MC SE 0.00208822; range [0.193686, 0.200111]
- removal_stat B9: reference 0.133899; empirical MC SE 0.00181462; A-B MC SE 0.00289732; range [0.126584, 0.133693]
- removal_stat RETUNED: reference 0.0782696; empirical MC SE 0.00194642; A-B MC SE 0.000911605; range [0.0723493, 0.0791022]
- Form B UB M* - B3 (level 0.987500): reference -0.722283; empirical MC SE 0.000179484; A-B MC SE 0.000278477; range [-0.722608, -0.721892]
- p_c M* - B3: reference 2.49994e-05; empirical MC SE 0; A-B MC SE 2.49994e-05; range [2.49994e-05, 2.49994e-05]
- HK1c UB M* PD7_primary: reference 0.0560292; empirical MC SE 4.51909e-05; A-B MC SE 6.81198e-05; range [0.0560154, 0.056194]
- pooled LB M* PD7_primary: reference 0.0479832; empirical MC SE 1.76505e-05; A-B MC SE 2.30833e-05; range [0.0479568, 0.0480236]
- HK1c UB M* SD1_7_gap_le_5m: reference 0.0566051; empirical MC SE 5.7674e-05; A-B MC SE 0.000117238; range [0.0565088, 0.0567235]
- pooled LB M* SD1_7_gap_le_5m: reference 0.0404018; empirical MC SE 5.46036e-05; A-B MC SE 4.62907e-05; range [0.0403293, 0.0405063]
- HK1c UB M* PD_inpath: reference 0.0889218; empirical MC SE 0.000148803; A-B MC SE 0.000227703; range [0.0886273, 0.0891624]
- pooled LB M* PD_inpath: reference 0.0570754; empirical MC SE 9.70812e-05; A-B MC SE 9.20427e-05; range [0.0568775, 0.0571866]
- H4 p (this tracker; doubled): reference 4.99988e-05; empirical MC SE 0; A-B MC SE None; range [4.99988e-05, 4.99988e-05]
- statuses not identical in every set: 5; {"B4/SD1_7_gap_le_5m NoFlag": {"reference": false, "share_same": 0.7, "analysis": false}, "B4/SD1_7_gap_le_5m FamFlag": {"reference": true, "share_same": 0.65, "analysis": true}, "B4/SD1_7_gap_le_5m shown_above": {"reference": true, "share_same": 0.9, "analysis": true}, "B6/PD_inpath FamFlag": {"reference": false, "share_same": 0.15, "analysis": false}, "B6/PD_inpath shown_above": {"reference": false, "share_same": 0.15, "analysis": true}}
- power-family size changes: {"B0/SD1_7_gap_le_5m family size": {"reference": 10, "values": [9, 10], "by_set": [10, 10, 9, 10, 10, 10, 10, 10, 10, 10, 9, 10, 10, 10, 10, 10, 10, 10, 10, 9]}, "B0/PD_inpath family size": {"reference": 6, "values": [5, 6], "by_set": [6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 5, 6, 6, 6, 6, 6, 6, 6, 6]}, "B1/PD7_primary family size": {"reference": 18, "values": [18, 19], "by_set": [19, 18, 18, 19, 19, 18, 18, 18, 19, 18, 19, 18, 18, 18, 18, 18, 18, 18, 19, 18]}, "B1/SD1_7_gap_le_5m family size": {"reference": 8, "values": [8, 9], "by_set": [8, 8, 8, 8, 8, 8, 9, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8]}, "B3/PD_inpath family size": {"reference": 5, "values": [3, 4, 5], "by_set": [3, 5, 5, 5, 5, 5, 5, 4, 5, 5, 4, 4, 5, 4, 5, 4, 4, 5, 5, 5]}, "B6/SD1_7_gap_le_5m family size": {"reference": 10, "values": [8, 9, 10], "by_set": [10, 10, 9, 10, 9, 10, 10, 10, 9, 10, 8, 9, 9, 10, 10, 10, 9, 9, 10, 10]}, "B9/SD1_7_gap_le_5m family size": {"reference": 6, "values": [6, 7], "by_set": [7, 6, 6, 6, 7, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6]}, "RETUNED/SD1_7_gap_le_5m family size": {"reference": 10, "values": [9, 10], "by_set": [10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 9, 10, 9, 10, 10, 10, 10, 9, 10]}}
- cells with |t - q| < 0.2: Mstar/PD7_primary/car|long|turning family (21 sets), Mstar/PD_inpath/car|long|static family (21 sets), B1/PD7_primary/car|lat|turning family (5 sets), B4/PD7_primary/car|lat|straight cells (17 sets), B4/SD1_7_gap_le_5m/pedestrian|long|turning cells (14 sets), B6/PD7_primary/large|long|straight family (10 sets), B6/SD1_7_gap_le_5m/car|long|new cells (8 sets), B6/PD_inpath/car|long|new family (17 sets), B1/PD7_primary/large|long|straight cells (17 sets), B1/PD7_primary/large|long|straight family (6 sets), B4/SD1_7_gap_le_5m/car|lat|turning family (17 sets), B4/PD7_primary/car|lat|straight family (10 sets), B6/PD_inpath/car|long|new cells (8 sets), B0/PD7_primary/pedestrian|long|static family (3 sets), RETUNED/PD7_primary/pedestrian|long|static family (3 sets), B0/PD7_primary/car|lat|turning cells (5 sets), RETUNED/PD7_primary/car|lat|turning cells (5 sets), B6/PD7_primary/large|long|straight cells (2 sets)

## transfer_lt3d/t3 (20 sets)

- removal_stat B0: reference -0.0450308; empirical MC SE 0.000739548; A-B MC SE 0.000863628; range [-0.047402, -0.0442303]
- removal_stat B1: reference 0.0800048; empirical MC SE 0.00233011; A-B MC SE 0.0055735; range [0.070211, 0.0796889]
- removal_stat B3: reference -0.0480692; empirical MC SE 3.06899e-05; A-B MC SE 5.39711e-05; range [-0.0481079, -0.0480035]
- removal_stat B4: reference 0.159541; empirical MC SE 0.00112785; A-B MC SE 0.00079521; range [0.157466, 0.161175]
- removal_stat B6: reference 0.0904789; empirical MC SE 0.000927698; A-B MC SE 0.000889837; range [0.0888449, 0.0921498]
- removal_stat B9: reference 0.123568; empirical MC SE 0.00174835; A-B MC SE 0.00483684; range [0.123197, 0.130405]
- removal_stat RETUNED: reference 0.0853981; empirical MC SE 0.00142578; A-B MC SE 0.00220553; range [0.0832881, 0.0890232]
- Form B UB M* - B0 (level 0.993750): reference -0.582913; empirical MC SE 0.000286093; A-B MC SE 0.000387975; range [-0.583333, -0.58236]
- p_c M* - B0: reference 2.49994e-05; empirical MC SE 0; A-B MC SE 2.49994e-05; range [2.49994e-05, 2.49994e-05]
- Form B UB M* - B3 (level 0.993750): reference -0.608992; empirical MC SE 0.000340847; A-B MC SE 0.000399568; range [-0.609474, -0.608412]
- p_c M* - B3: reference 2.49994e-05; empirical MC SE 0; A-B MC SE 2.49994e-05; range [2.49994e-05, 2.49994e-05]
- HK1c UB M* PD7_primary: reference 0.0515211; empirical MC SE 3.2811e-05; A-B MC SE 5.26719e-05; range [0.0514867, 0.0516082]
- pooled LB M* PD7_primary: reference 0.044308; empirical MC SE 1.99386e-05; A-B MC SE 2.05244e-05; range [0.0442668, 0.0443463]
- HK1c UB M* SD1_7_gap_le_5m: reference 0.0532621; empirical MC SE 8.47093e-05; A-B MC SE 0.000131714; range [0.0529853, 0.0532222]
- pooled LB M* SD1_7_gap_le_5m: reference 0.0365261; empirical MC SE 5.4423e-05; A-B MC SE 5.1331e-05; range [0.0364149, 0.0366556]
- HK1c UB M* PD_inpath: reference 0.0890639; empirical MC SE 0.000151735; A-B MC SE 0.000209335; range [0.089009, 0.0896571]
- pooled LB M* PD_inpath: reference 0.0568557; empirical MC SE 5.23473e-05; A-B MC SE 9.72096e-05; range [0.0568382, 0.0570248]
- H4 p (this tracker; doubled): reference 9.99975e-05; empirical MC SE 0; A-B MC SE None; range [9.99975e-05, 9.99975e-05]
- statuses not identical in every set: 5; {"B1/SD1_7_gap_le_5m NoFlag": {"reference": false, "share_same": 0.6, "analysis": false}, "B1/SD1_7_gap_le_5m shown_above": {"reference": true, "share_same": 0.6, "analysis": true}, "B9/PD_inpath NoFlag": {"reference": false, "share_same": 0.05, "analysis": false}, "B9/PD_inpath FamFlag": {"reference": true, "share_same": 0.85, "analysis": true}, "B9/PD_inpath shown_above": {"reference": true, "share_same": 0.85, "analysis": true}}
- power-family size changes: {"B1/SD1_7_gap_le_5m family size": {"reference": 6, "values": [6, 7], "by_set": [6, 7, 7, 7, 6, 7, 7, 7, 7, 6, 7, 7, 6, 6, 7, 6, 7, 6, 6, 7]}, "B4/SD1_7_gap_le_5m family size": {"reference": 8, "values": [7, 8], "by_set": [8, 7, 8, 8, 8, 8, 7, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8]}, "B6/SD1_7_gap_le_5m family size": {"reference": 7, "values": [7, 8], "by_set": [8, 7, 7, 7, 8, 8, 8, 8, 7, 8, 7, 8, 8, 7, 8, 8, 8, 8, 8, 8]}, "B9/SD1_7_gap_le_5m family size": {"reference": 6, "values": [6, 7], "by_set": [7, 6, 7, 6, 6, 6, 6, 7, 7, 6, 6, 7, 6, 6, 7, 6, 6, 6, 7, 7]}, "RETUNED/SD1_7_gap_le_5m family size": {"reference": 7, "values": [6, 7], "by_set": [7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 6, 7, 7, 7, 7, 7, 7]}}
- cells with |t - q| < 0.2: Mstar/PD7_primary/large|long|straight cells (21 sets), Mstar/PD_inpath/car|long|new cells (17 sets), Mstar/PD_inpath/car|long|new family (21 sets), B1/PD7_primary/car|long|turning family (5 sets), B1/SD1_7_gap_le_5m/car|long|new cells (14 sets), B1/SD1_7_gap_le_5m/large|long|straight cells (18 sets), B4/PD7_primary/large|long|static cells (16 sets), B6/PD7_primary/car|lat|turning cells (21 sets), B9/PD_inpath/car|long|new cells (13 sets), RETUNED/PD7_primary/large|long|new cells (12 sets), B1/PD7_primary/car|long|straight cells (1 sets), B1/PD7_primary/large|long|new cells (1 sets), B4/PD7_primary/large|long|static family (15 sets), B4/SD1_7_gap_le_5m/large|long|straight cells (15 sets), B6/PD7_primary/large|long|new cells (3 sets), B9/PD_inpath/car|long|new family (11 sets), B6/PD7_primary/car|lat|turning family (7 sets), B4/SD1_7_gap_le_5m/car|long|turning cells (3 sets), B4/SD1_7_gap_le_5m/car|long|turning family (2 sets)
