# R21 Monte Carlo error and seed stability

Descriptive (plan section 6.1); the verdict is always the primary seed's. B = 500; power mode recompute.

- H1 (bound form) at the reference set: False; share of alternative sets with the same: 1.0

## within_lt3d/t1 (2 sets)

- removal_stat B0: reference -0.0133693; empirical MC SE 0.00851037; A-B MC SE 0.00564607; range [-0.01661, -0.00457452]
- removal_stat B1: reference -0.019708; empirical MC SE 0.00678951; A-B MC SE 0.00196217; range [-0.0329643, -0.0233625]
- removal_stat B3: reference -0.0495081; empirical MC SE 4.71838e-05; A-B MC SE 2.67351e-05; range [-0.0494864, -0.0494196]
- removal_stat B4: reference 0.0428001; empirical MC SE 0.0151142; A-B MC SE 0.00229991; range [0.0179434, 0.0393181]
- removal_stat B6: reference 0.00642818; empirical MC SE 0.00702593; A-B MC SE 0.00201332; range [0.00230041, 0.0122366]
- removal_stat B9: reference -0.00474719; empirical MC SE 0.00475357; A-B MC SE 0.00205282; range [-0.00602333, 0.000699236]
- removal_stat RETUNED: reference 0.0366702; empirical MC SE 0.000349252; A-B MC SE 0.00140334; range [0.0232444, 0.0237383]
- Form B UB M* - B0 (level 0.996875): reference -0.175508; empirical MC SE 0.0028438; A-B MC SE 0.00173796; range [-0.175512, -0.171491]
- p_c M* - B0: reference 0.00199601; empirical MC SE 0; A-B MC SE 0.00199601; range [0.00199601, 0.00199601]
- Form B UB M* - B1 (level 0.996875): reference -0.180951; empirical MC SE 0.0025857; A-B MC SE 0.00337784; range [-0.174899, -0.171242]
- p_c M* - B1: reference 0.00199601; empirical MC SE 0; A-B MC SE 0.00199601; range [0.00199601, 0.00199601]
- Form B UB M* - B3 (level 0.996875): reference -0.72628; empirical MC SE 0.00123168; A-B MC SE 0.00540057; range [-0.733549, -0.731807]
- p_c M* - B3: reference 0.00199601; empirical MC SE 0; A-B MC SE 0.00199601; range [0.00199601, 0.00199601]
- Form B UB M* - B9 (level 0.996875): reference -0.290262; empirical MC SE 3.90919e-06; A-B MC SE 0.00208468; range [-0.28676, -0.286755]
- p_c M* - B9: reference 0.00199601; empirical MC SE 0; A-B MC SE 0.00199601; range [0.00199601, 0.00199601]
- HK1c UB M* PD7_primary: reference 0.0433096; empirical MC SE 0.000774659; A-B MC SE 0.000716686; range [0.0424049, 0.0435004]
- pooled LB M* PD7_primary: reference 0.0320269; empirical MC SE 3.3877e-05; A-B MC SE 0.000475395; range [0.0322037, 0.0322516]
- HK1c UB M* SD1_7_gap_le_5m: reference 0.0427231; empirical MC SE 0.00116712; A-B MC SE 0.000316624; range [0.0412019, 0.0428525]
- pooled LB M* SD1_7_gap_le_5m: reference 0.0192243; empirical MC SE 8.8853e-05; A-B MC SE 0.000816891; range [0.0195831, 0.0197087]
- HK1c UB M* PD_inpath: reference 0.0496371; empirical MC SE 0.000481518; A-B MC SE 0.0012941; range [0.0493061, 0.0499871]
- pooled LB M* PD_inpath: reference 0.013479; empirical MC SE 0.000984877; A-B MC SE 0.00168608; range [0.011893, 0.0132858]
- H3 p (this tracker; doubled): reference 0.00399202; empirical MC SE 0; A-B MC SE None; range [0.00399202, 0.00399202]
- H3 UB M*Jx - B3 (own level): reference -0.189994; empirical MC SE 0.000503543; A-B MC SE 0.00290283; range [-0.193644, -0.192932]
- statuses not identical in every set: 3; {"B9/PD7_primary FamFlag": {"reference": false, "share_same": 0.5, "analysis": false}, "B9/PD7_primary shown_above": {"reference": false, "share_same": 0.5, "analysis": false}, "V_t membership identical": {"reference": ["B0", "B1", "B3", "B9"], "share_same": 0.5, "analysis": ["B0", "B1", "B3", "B6", "B9"], "differing_sets": {"2": ["B0", "B1", "B3"]}}}
- power-family size changes: {"Mstar/PD7_primary family size": {"reference": 7, "values": [7, 8], "by_set": [8, 7]}, "B0/PD7_primary family size": {"reference": 7, "values": [7, 8], "by_set": [7, 8]}, "B1/PD7_primary family size": {"reference": 7, "values": [5, 7], "by_set": [5, 7]}, "B1/SD1_7_gap_le_5m family size": {"reference": 0, "values": [0, 1], "by_set": [1, 0]}, "B3/PD7_primary family size": {"reference": 6, "values": [6, 7], "by_set": [6, 7]}, "B4/PD7_primary family size": {"reference": 7, "values": [6, 10], "by_set": [6, 10]}, "B4/SD1_7_gap_le_5m family size": {"reference": 1, "values": [0, 1], "by_set": [0, 1]}, "B6/PD7_primary family size": {"reference": 7, "values": [8], "by_set": [8, 8]}, "B6/SD1_7_gap_le_5m family size": {"reference": 1, "values": [0, 1], "by_set": [0, 1]}, "B9/PD7_primary family size": {"reference": 6, "values": [6, 7], "by_set": [7, 6]}, "B9/SD1_7_gap_le_5m family size": {"reference": 0, "values": [0, 1], "by_set": [1, 0]}, "RETUNED/PD7_primary family size": {"reference": 7, "values": [9, 10], "by_set": [9, 10]}, "RETUNED/SD1_7_gap_le_5m family size": {"reference": 1, "values": [0, 1], "by_set": [1, 0]}}
- cells with |t - q| < 0.2: B0/PD7_primary/pedestrian|long|static family (1 sets), B4/PD7_primary/pedestrian|long|turning cells (2 sets), RETUNED/PD7_primary/pedestrian|long|turning cells (2 sets), B4/PD7_primary/car|long|new cells (1 sets), B6/PD7_primary/car|long|new family (1 sets), B9/PD7_primary/car|long|new family (1 sets), RETUNED/PD7_primary/car|long|new cells (1 sets)

## within_lt3d/t3 (2 sets)

- removal_stat B0: reference -0.0496041; empirical MC SE 0.000144825; A-B MC SE 5.24265e-05; range [-0.05, -0.0497952]
- removal_stat B1: reference 0.0448449; empirical MC SE 0.00272867; A-B MC SE 0.00337732; range [0.0374981, 0.041357]
- removal_stat B3: reference -0.0497513; empirical MC SE 0.000109405; A-B MC SE 5.51108e-05; range [-0.05, -0.0498453]
- removal_stat B4: reference 0.0732596; empirical MC SE 0.00473488; A-B MC SE 0.00546649; range [0.0817196, 0.0884158]
- removal_stat B6: reference -0.0169398; empirical MC SE 0.000735827; A-B MC SE 0.00099944; range [-0.0124633, -0.0114227]
- removal_stat B9: reference -0.015388; empirical MC SE 0.00798622; A-B MC SE 0.00555395; range [-0.0212024, -0.00990816]
- removal_stat RETUNED: reference -0.00701231; empirical MC SE 0.000772844; A-B MC SE 0.00239193; range [0.00126377, 0.00235674]
- Form B UB M* - B0 (level 0.997500): reference -0.512304; empirical MC SE 0.00317819; A-B MC SE 0.0126816; range [-0.511708, -0.507213]
- p_c M* - B0: reference 0.00199601; empirical MC SE 0; A-B MC SE 0.00199601; range [0.00199601, 0.00199601]
- Form B UB M* - B3 (level 0.997500): reference -0.551398; empirical MC SE 0.00304927; A-B MC SE 0.00674784; range [-0.553727, -0.549414]
- p_c M* - B3: reference 0.00199601; empirical MC SE 0; A-B MC SE 0.00199601; range [0.00199601, 0.00199601]
- Form B UB M* - B6 (level 0.997500): reference 0.0206121; empirical MC SE 0.000635331; A-B MC SE 0.00203438; range [0.0218967, 0.0227952]
- p_c M* - B6: reference 0.359281; empirical MC SE 0.0225823; A-B MC SE 0.0214569; range [0.333333, 0.365269]
- Form B UB M* - B9 (level 0.997500): reference -0.201426; empirical MC SE 0.00316442; A-B MC SE 0.0103999; range [-0.198478, -0.194003]
- p_c M* - B9: reference 0.00199601; empirical MC SE 0; A-B MC SE 0.00199601; range [0.00199601, 0.00199601]
- Form B UB M* - RETUNED (level 0.997500): reference -0.211722; empirical MC SE 0.00339614; A-B MC SE 0.00922803; range [-0.211176, -0.206374]
- p_c M* - RETUNED: reference 0.00199601; empirical MC SE 0; A-B MC SE 0.00199601; range [0.00199601, 0.00199601]
- HK1c UB M* PD7_primary: reference 0.0467241; empirical MC SE 0.000351592; A-B MC SE 0.000339191; range [0.0466095, 0.0471067]
- pooled LB M* PD7_primary: reference 0.0341979; empirical MC SE 0.000360161; A-B MC SE 0.000480422; range [0.0343839, 0.0348932]
- HK1c UB M* SD1_7_gap_le_5m: reference 0.0415939; empirical MC SE 0.00141495; A-B MC SE 0.000717071; range [0.0408252, 0.0428262]
- pooled LB M* SD1_7_gap_le_5m: reference 0.0187789; empirical MC SE 9.33704e-05; A-B MC SE 0.000822925; range [0.0186542, 0.0187863]
- HK1c UB M* PD_inpath: reference 0.0411702; empirical MC SE 0.000537482; A-B MC SE 0.00107509; range [0.0414502, 0.0422103]
- pooled LB M* PD_inpath: reference 0.0180821; empirical MC SE 0.000377917; A-B MC SE 0.000832397; range [0.0156784, 0.0162129]
- H3 p (this tracker; doubled): reference 0.0638723; empirical MC SE 0.00564556; A-B MC SE None; range [0.0558882, 0.0638723]
- H3 UB M*Jx - B0 (own level): reference 0.00383769; empirical MC SE 0.00347897; A-B MC SE 0.00374519; range [0.00231549, 0.0072355]
- H3 UB M*Jx - B3 (own level): reference -0.0369758; empirical MC SE 0.00374227; A-B MC SE 0.00254046; range [-0.0386636, -0.0333712]
- statuses not identical in every set: 8; {"Mstar/PD7_primary Floor": {"reference": true, "share_same": 0.5, "analysis": true}, "Mstar/PD7_primary valid": {"reference": true, "share_same": 0.5, "analysis": true}, "B4/PD_inpath NoFlag": {"reference": true, "share_same": 0.5, "analysis": true}, "B4/PD_inpath FamFlag": {"reference": true, "share_same": 0.5, "analysis": false}, "B4/PD_inpath shown_above": {"reference": true, "share_same": 0.5, "analysis": true}, "RETUNED/PD7_primary FamFlag": {"reference": false, "share_same": 0.0, "analysis": false}, "RETUNED/PD7_primary shown_above": {"reference": false, "share_same": 0.0, "analysis": false}, "V_t membership identical": {"reference": ["B0", "B3", "B6", "B9", "RETUNED"], "share_same": 0.0, "analysis": ["B0", "B3", "B6", "B9", "RETUNED"], "differing_sets": {"1": ["B0", "B3", "B6", "B9"], "2": ["B0", "B3", "B6", "B9"]}}}
- power-family size changes: {"Mstar/PD7_primary family size": {"reference": 7, "values": [4, 7], "by_set": [4, 7]}, "B0/PD7_primary family size": {"reference": 8, "values": [7, 8], "by_set": [7, 8]}, "B1/PD7_primary family size": {"reference": 8, "values": [7, 8], "by_set": [8, 7]}, "B4/PD7_primary family size": {"reference": 8, "values": [7], "by_set": [7, 7]}, "B6/PD7_primary family size": {"reference": 8, "values": [8, 11], "by_set": [11, 8]}, "B6/SD1_7_gap_le_5m family size": {"reference": 1, "values": [0, 1], "by_set": [1, 0]}, "B9/PD7_primary family size": {"reference": 8, "values": [5, 7], "by_set": [5, 7]}, "B9/SD1_7_gap_le_5m family size": {"reference": 0, "values": [0, 1], "by_set": [1, 0]}, "RETUNED/PD7_primary family size": {"reference": 9, "values": [6, 10], "by_set": [10, 6]}}
- cells with |t - q| < 0.2: B4/PD_inpath/car|long|straight family (2 sets), B1/PD7_primary/car|long|new cells (1 sets), B4/PD_inpath/car|long|straight cells (1 sets), RETUNED/PD7_primary/car|long|straight family (1 sets)
