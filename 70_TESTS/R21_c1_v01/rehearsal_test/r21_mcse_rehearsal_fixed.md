# R21 Monte Carlo error and seed stability

Descriptive (plan section 6.1); the verdict is always the primary seed's. B = 500; power mode fixed.

- H1 (bound form) at the reference set: False; share of alternative sets with the same: 1.0

## within_lt3d/t1 (2 sets)

- removal_stat B0: reference -0.0133693; empirical MC SE 0.00325226; A-B MC SE 0.00564607; range [-0.0212094, -0.01661]
- removal_stat B1: reference -0.019708; empirical MC SE 0.00218942; A-B MC SE 0.00196217; range [-0.0248166, -0.0217203]
- removal_stat B3: reference -0.0495081; empirical MC SE 4.71838e-05; A-B MC SE 2.67351e-05; range [-0.0494864, -0.0494196]
- removal_stat B4: reference 0.0428001; empirical MC SE 0.0103316; A-B MC SE 0.00229991; range [0.0242608, 0.0388719]
- removal_stat B6: reference 0.00642818; empirical MC SE 0.00280593; A-B MC SE 0.00201332; range [0.00230041, 0.00626859]
- removal_stat B9: reference -0.00474719; empirical MC SE 0.00463798; A-B MC SE 0.00205282; range [-0.00585986, 0.000699236]
- removal_stat RETUNED: reference 0.0366702; empirical MC SE 0.00684451; A-B MC SE 0.00140334; range [0.0252856, 0.0349652]
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
- power-family size changes: none
- cells with |t - q| < 0.2: B4/PD7_primary/pedestrian|long|turning cells (2 sets), RETUNED/PD7_primary/pedestrian|long|turning cells (2 sets), B4/PD7_primary/car|long|new cells (1 sets), B6/PD7_primary/car|long|new family (1 sets), B9/PD7_primary/car|long|new family (1 sets), RETUNED/PD7_primary/car|long|new cells (1 sets)

## within_lt3d/t3 (2 sets)

- removal_stat B0: reference -0.0496041; empirical MC SE 0.000144825; A-B MC SE 5.24265e-05; range [-0.05, -0.0497952]
- removal_stat B1: reference 0.0448449; empirical MC SE 0.00711483; A-B MC SE 0.00337732; range [0.034542, 0.0446039]
- removal_stat B3: reference -0.0497513; empirical MC SE 0.000109405; A-B MC SE 5.51108e-05; range [-0.05, -0.0498453]
- removal_stat B4: reference 0.0732596; empirical MC SE 0.00239165; A-B MC SE 0.00546649; range [0.083942, 0.0873243]
- removal_stat B6: reference -0.0169398; empirical MC SE 0.00278628; A-B MC SE 0.00099944; range [-0.010205, -0.00626462]
- removal_stat B9: reference -0.015388; empirical MC SE 0.000158563; A-B MC SE 0.00555395; range [-0.0132305, -0.0130062]
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
- statuses not identical in every set: 6; {"B4/PD_inpath NoFlag": {"reference": true, "share_same": 0.5, "analysis": true}, "B4/PD_inpath FamFlag": {"reference": true, "share_same": 0.5, "analysis": false}, "B4/PD_inpath shown_above": {"reference": true, "share_same": 0.5, "analysis": true}, "RETUNED/PD7_primary FamFlag": {"reference": false, "share_same": 0.0, "analysis": false}, "RETUNED/PD7_primary shown_above": {"reference": false, "share_same": 0.0, "analysis": false}, "V_t membership identical": {"reference": ["B0", "B3", "B6", "B9", "RETUNED"], "share_same": 0.0, "analysis": ["B0", "B3", "B6", "B9", "RETUNED"], "differing_sets": {"1": ["B0", "B3", "B6", "B9"], "2": ["B0", "B3", "B6", "B9"]}}}
- power-family size changes: none
- cells with |t - q| < 0.2: B4/PD_inpath/car|long|straight family (2 sets), B1/PD7_primary/car|long|new cells (1 sets), B4/PD_inpath/car|long|straight cells (1 sets), RETUNED/PD7_primary/car|long|straight family (1 sets), B1/PD7_primary/car|long|new family (1 sets), RETUNED/PD7_primary/car|long|turning family (1 sets)

## transfer_lt3d/t1 (2 sets)

- removal_stat B0: reference -0.0231603; empirical MC SE 0.00751795; A-B MC SE 0.00570603; range [-0.00417442, 0.00645756]
- removal_stat B1: reference -0.0404927; empirical MC SE 0.000669771; A-B MC SE 6.58606e-05; range [-0.0405595, -0.0396123]
- removal_stat B3: reference -0.04925; empirical MC SE 3.95776e-05; A-B MC SE 2.16274e-05; range [-0.049386, -0.04933]
- removal_stat B4: reference 0.0423244; empirical MC SE 0.00243396; A-B MC SE 0.00166219; range [0.042315, 0.0457571]
- removal_stat B6: reference 0.013302; empirical MC SE 0.00817203; A-B MC SE 0.00580989; range [0.0311134, 0.0426704]
- removal_stat B9: reference -0.0212133; empirical MC SE 0.00193694; A-B MC SE 0.00724644; range [0.00458776, 0.00732701]
- removal_stat RETUNED: reference -0.0317329; empirical MC SE 0.00386351; A-B MC SE 0.000234469; range [-0.0178257, -0.0123618]
- Form B UB M* - B0 (level 0.997500): reference -0.176246; empirical MC SE 0.000202439; A-B MC SE 0.00299247; range [-0.180027, -0.17974]
- p_c M* - B0: reference 0.00199601; empirical MC SE 0; A-B MC SE 0.00199601; range [0.00199601, 0.00199601]
- Form B UB M* - B1 (level 0.997500): reference -0.20695; empirical MC SE 0.000467933; A-B MC SE 0.00673315; range [-0.205112, -0.204451]
- p_c M* - B1: reference 0.00199601; empirical MC SE 0; A-B MC SE 0.00199601; range [0.00199601, 0.00199601]
- Form B UB M* - B3 (level 0.997500): reference -0.690612; empirical MC SE 0.00445748; A-B MC SE 0.00286876; range [-0.689004, -0.6827]
- p_c M* - B3: reference 0.00199601; empirical MC SE 0; A-B MC SE 0.00199601; range [0.00199601, 0.00199601]
- Form B UB M* - B9 (level 0.997500): reference -0.264436; empirical MC SE 0.00511566; A-B MC SE 0.000906037; range [-0.262019, -0.254784]
- p_c M* - B9: reference 0.00199601; empirical MC SE 0; A-B MC SE 0.00199601; range [0.00199601, 0.00199601]
- Form B UB M* - RETUNED (level 0.997500): reference -0.176246; empirical MC SE 0.000202439; A-B MC SE 0.00299247; range [-0.180027, -0.17974]
- p_c M* - RETUNED: reference 0.00199601; empirical MC SE 0; A-B MC SE 0.00199601; range [0.00199601, 0.00199601]
- HK1c UB M* PD7_primary: reference 0.0536573; empirical MC SE 7.30778e-05; A-B MC SE 0.00062668; range [0.053381, 0.0534844]
- pooled LB M* PD7_primary: reference 0.0405733; empirical MC SE 0.000264261; A-B MC SE 0.000279561; range [0.0408499, 0.0412236]
- HK1c UB M* SD1_7_gap_le_5m: reference 0.0451334; empirical MC SE 0.0020816; A-B MC SE 0.000432555; range [0.0453655, 0.0483094]
- pooled LB M* SD1_7_gap_le_5m: reference 0.0257923; empirical MC SE 0.00065396; A-B MC SE 0.000789237; range [0.0249485, 0.0258733]
- HK1c UB M* PD_inpath: reference 0.0291158; empirical MC SE 0.000541619; A-B MC SE 0.0006585; range [0.0289558, 0.0297217]
- pooled LB M* PD_inpath: reference 0.0115142; empirical MC SE 0.000501245; A-B MC SE 0.000618731; range [0.011076, 0.0117848]
- H4 p (this tracker; doubled): reference 0.0199601; empirical MC SE 0.00282278; A-B MC SE None; range [0.011976, 0.0159681]
- statuses not identical in every set: 5; {"B0/PD7_primary FamFlag": {"reference": false, "share_same": 0.5, "analysis": false}, "B0/PD7_primary shown_above": {"reference": false, "share_same": 0.5, "analysis": false}, "B9/PD7_primary FamFlag": {"reference": false, "share_same": 0.0, "analysis": false}, "B9/PD7_primary shown_above": {"reference": false, "share_same": 0.0, "analysis": false}, "V_t membership identical": {"reference": ["B0", "B1", "B3", "B9", "RETUNED"], "share_same": 0.0, "analysis": ["B0", "B1", "B3", "B9", "RETUNED"], "differing_sets": {"1": ["B1", "B3", "RETUNED"], "2": ["B0", "B1", "B3", "RETUNED"]}}}
- power-family size changes: none
- cells with |t - q| < 0.2: B0/PD7_primary/pedestrian|long|static family (1 sets)

## transfer_lt3d/t3 (2 sets)

- removal_stat B0: reference -0.0498205; empirical MC SE 6.69641e-05; A-B MC SE 4.12718e-05; range [-0.05, -0.0499053]
- removal_stat B1: reference 0.0363078; empirical MC SE 0.0113171; A-B MC SE 0.00358289; range [0.0354302, 0.051435]
- removal_stat B3: reference -0.05; empirical MC SE 0; A-B MC SE 0; range [-0.05, -0.05]
- removal_stat B4: reference 0.134686; empirical MC SE 7.00205e-05; A-B MC SE 0.000777852; range [0.132151, 0.13225]
- removal_stat B6: reference 0.0132706; empirical MC SE 0.00691927; A-B MC SE 0.000273604; range [-0.00377579, 0.00600953]
- removal_stat B9: reference 0.00149181; empirical MC SE 0.0183202; A-B MC SE 0.000335091; range [-0.0303165, -0.00440781]
- removal_stat RETUNED: reference 0.00736006; empirical MC SE 0.00397636; A-B MC SE 0.000106595; range [-0.000968367, 0.00465506]
- Form B UB M* - B0 (level 0.993750): reference -0.556976; empirical MC SE 0.000546804; A-B MC SE 0.00279832; range [-0.562561, -0.561788]
- p_c M* - B0: reference 0.00199601; empirical MC SE 0; A-B MC SE 0.00199601; range [0.00199601, 0.00199601]
- Form B UB M* - B3 (level 0.993750): reference -0.587461; empirical MC SE 0.00188694; A-B MC SE 0.00299349; range [-0.590245, -0.587576]
- p_c M* - B3: reference 0.00199601; empirical MC SE 0; A-B MC SE 0.00199601; range [0.00199601, 0.00199601]
- HK1c UB M* PD7_primary: reference 0.0539574; empirical MC SE 0.000368903; A-B MC SE 0.000611747; range [0.0537753, 0.054297]
- pooled LB M* PD7_primary: reference 0.0406269; empirical MC SE 0.000251964; A-B MC SE 0.000431381; range [0.0410548, 0.0414112]
- HK1c UB M* SD1_7_gap_le_5m: reference 0.0493787; empirical MC SE 0.00094422; A-B MC SE 0.000662155; range [0.0483607, 0.0496961]
- pooled LB M* SD1_7_gap_le_5m: reference 0.0251275; empirical MC SE 0.000848982; A-B MC SE 0.00109755; range [0.0252214, 0.026422]
- HK1c UB M* PD_inpath: reference 0.030187; empirical MC SE 0.000454332; A-B MC SE 0.000842227; range [0.0292056, 0.0298481]
- pooled LB M* PD_inpath: reference 0.0121395; empirical MC SE 0.00121264; A-B MC SE 0.00053358; range [0.0113047, 0.0130196]
- H4 p (this tracker; doubled): reference 0.00798403; empirical MC SE 0.414949; A-B MC SE None; range [0.011976, 0.598802]
- statuses not identical in every set: 7; {"B6/PD7_primary FamFlag": {"reference": true, "share_same": 0.5, "analysis": false}, "B6/PD7_primary shown_above": {"reference": true, "share_same": 0.5, "analysis": false}, "B9/PD7_primary FamFlag": {"reference": true, "share_same": 0.0, "analysis": false}, "B9/PD7_primary shown_above": {"reference": true, "share_same": 0.0, "analysis": false}, "RETUNED/PD7_primary FamFlag": {"reference": true, "share_same": 0.5, "analysis": false}, "RETUNED/PD7_primary shown_above": {"reference": true, "share_same": 0.5, "analysis": false}, "V_t membership identical": {"reference": ["B0", "B3"], "share_same": 0.0, "analysis": ["B0", "B3", "B6", "B9", "RETUNED"], "differing_sets": {"1": ["B0", "B3", "B9"], "2": ["B0", "B3", "B6", "B9", "RETUNED"]}}}
- power-family size changes: none
- cells with |t - q| < 0.2: B4/PD7_primary/pedestrian|long|static family (1 sets), B6/PD7_primary/car|long|new family (1 sets), B9/PD7_primary/car|long|new family (1 sets), B6/PD7_primary/pedestrian|long|static family (1 sets), B4/SD1_7_gap_le_5m/car|long|straight cells (1 sets), RETUNED/PD7_primary/car|long|straight family (1 sets)
