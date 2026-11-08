# R21 re-derivation summary

Descriptive review; the frozen verdict stands whatever this shows (plan section 9). Rules: R21_DESIGN_v01.md.

- B = 2000 (analysis 40000); power check 500 datasets; bound tolerance 0.0078
- exact weight reproduction: {"n_bounds": 496, "max_abs_diff": 0.01309896909249536, "exact": false}
- comparisons: {"agree": 94455, "MC-borderline": 58, "info": 20}
- runtime 68 s; memory {"working_set_mb": 161, "peak_working_set_mb": 239, "peak_private_mb": 258}

## H1

- R21: holds = False (T1 False, T3 False)
- without zero-SE removals: {"holds": false, "V_t1": ["B0", "B1", "B3", "B9"], "V_t3": ["B0", "B3", "B6", "B9"], "zero_se_removed_t1": [], "zero_se_removed_t3": []}

- within_lt3d/t1: Valid(M*) False; V_t ['B0', 'B1', 'B3', 'B9']; Form B met False; UB {'B0': -0.1767, 'B1': -0.1765, 'B3': -0.7287, 'B9': -0.2878}; RETUNED {'0': 'B0a0.5', '1': 'B0a0.5', '2': 'B0a0.5', '3': 'B0a0.5', '4': 'B0a0.5'}
- within_lt3d/t3: Valid(M*) False; V_t ['B0', 'B3', 'B6', 'B9']; Form B met False; UB {'B0': -0.5066, 'B3': -0.5487, 'B6': 0.0203, 'B9': -0.1928}; RETUNED {'0': 'B0d0.3', '1': 'B0d0.3', '2': 'B0d0.3', '3': 'B0d0.3', '4': 'B0d0.3'}
- transfer_lt3d/t1: Valid(M*) False; V_t ['B0', 'B1', 'B3', 'B9', 'RETUNED']; Form B met False; UB {'B0': -0.1724, 'B1': -0.2016, 'B3': -0.6893, 'B9': -0.2637, 'RETUNED': -0.1724}; RETUNED {'all': 'B0a1'}
- transfer_lt3d/t3: Valid(M*) False; V_t ['B0', 'B3', 'B6', 'B9', 'RETUNED']; Form B met False; UB {'B0': -0.5536, 'B3': -0.5837, 'B6': 0.009, 'B9': -0.2127, 'RETUNED': -0.2483}; RETUNED {'all': 'B0d0.3'}
- H2: {"bound_form_holds": true, "p": 0.0004997501249375312, "multiplier": 1}
- H3: {"bound_form_holds": false, "validJ_both": true, "p_form": 0.041979010494752625, "multiplier": 4, "p": 0.041979010494752625, "p_rule": "p = max_t min(1, 2|V^J| max p_c) (plan 6.1); 1 when ValidJ(M*Jx) fails on a tracker"}
- H4: {"bound_form_holds": false, "valid_Mstar_both": false, "p_form_b": 0.494752623688156, "multiplier": 10, "p": 1.0, "p_rule": "p = max_t min(1, 2|V_t| max p_c) (plan 6.1); 1 when Valid(M*) fails on a tracker (H1's formula includes Valid)"}

## Disagreements (0)


## MC-borderline (58)

- within_lt3d/t1/Mstar/SD1_7_gap_le_5m R21-own family (check): R21 ["car|long|static"], analysis ["car|lat|static"]
- within_lt3d/t1/B4/PD7_primary flagged cells: R21 [], analysis ["car|long|new", "pedestrian|long|static"]
- within_lt3d/t1/B4/PD7_primary NoFlag: R21 true, analysis false
- within_lt3d/t1/B6/PD7_primary family flagged: R21 ["car|long|new"], analysis []
- within_lt3d/t1/B6/PD7_primary FamFlag: R21 true, analysis false
- within_lt3d/t1/B6/PD7_primary valid: R21 false, analysis true
- within_lt3d/t1/B6/PD7_primary shown_above: R21 true, analysis false
- within_lt3d/t1/RETUNED/PD7_primary flagged cells: R21 [], analysis ["car|long|new"]
- within_lt3d/t1/RETUNED/PD7_primary NoFlag: R21 true, analysis false
- within_lt3d/t1 H1 V_t: R21 ["B0", "B1", "B3", "B9"], analysis ["B0", "B1", "B3", "B6", "B9"]
- within_lt3d/t1 H1 removed (shown above): R21 ["B4", "B6", "RETUNED"], analysis ["B4", "RETUNED"]
- within_lt3d/t1 H1 |V_t|: R21 4, analysis 5
- within_lt3d/t1 H1 Form B level: R21 0.996875, analysis 0.9975
- within_lt3d/t1 K8 validity(C1 level 0.99861) B4/PD7_primary flagged: R21 [], analysis ["car|long|new", "pedestrian|long|static"]
- within_lt3d/t1 K8 validity(C1 level 0.95000) B0d0.2/SD1_7_gap_le_5m flagged: R21 ["pedestrian|long|static", "pedestrian|long|turning"], analysis ["pedestrian|long|turning"]
- within_lt3d/t1 K8 validity(C1 level 0.99861) RETUNED/PD7_primary flagged: R21 [], analysis ["car|long|new"]
- within_lt3d/t1 K8 cell(0.95) B0d0.2/SD1_7_gap_le_5m/pedestrian|long|static flag: R21 true, analysis false
- within_lt3d/t1 K8 cell(0.95) B9/NIP_not_in_path/car|long|new flag: R21 false, analysis true
- within_lt3d/t1 K8 cell(0.95) B0a0.25/NIP_not_in_path/large|long|straight flag: R21 true, analysis false
- within_lt3d/t1 K8 cell(0.95) B0d0.2/NIP_not_in_path/large|long|straight flag: R21 true, analysis false
- within_lt3d/t3/Mstar/SD1_7_gap_le_5m R21-own family (check): R21 ["car|lat|static"], analysis []
- within_lt3d/t3/B1/PD7_primary family flagged: R21 ["car|long|straight", "car|long|turning", "car|long|new"], analysis ["car|long|straight", "car|long|turning"]
- within_lt3d/t3/B1/PD_inpath shown_above: R21 false, analysis true
- within_lt3d/t3/B4/PD_inpath family flagged: R21 ["car|long|straight"], analysis []
- within_lt3d/t3/B4/PD_inpath FamFlag: R21 true, analysis false
- within_lt3d/t3/RETUNED/PD7_primary family flagged: R21 ["car|long|straight"], analysis []
- within_lt3d/t3/RETUNED/PD7_primary FamFlag: R21 true, analysis false
- within_lt3d/t3/RETUNED/PD7_primary valid: R21 false, analysis true
- within_lt3d/t3/RETUNED/PD7_primary shown_above: R21 true, analysis false
- within_lt3d/t3 H1 V_t: R21 ["B0", "B3", "B6", "B9"], analysis ["B0", "B3", "B6", "B9", "RETUNED"]
- within_lt3d/t3 H1 removed (shown above): R21 ["B1", "B4", "RETUNED"], analysis ["B1", "B4"]
- within_lt3d/t3 H1 |V_t|: R21 4, analysis 5
- within_lt3d/t3 H1 Form B level: R21 0.996875, analysis 0.9975
- within_lt3d/t3 K8 validity(C1 level 0.95000) B0a0.03125/PD7_primary flagged: R21 ["car|long|straight", "car|long|turning", "car|long|new", "pedestrian|long|static", "large|long|straight", "large|long|new"], analysis ["car|long|straight", "car|long|turning", "car|long|new", "pedestrian|long|static", "large|long|straight", "large|long|turning", "large|long|new"]
- within_lt3d/t3 K8 cell(0.95) B0a0.03125/PD7_primary/large|long|turning flag: R21 false, analysis true
- within_lt3d/t3 K8 cell(0.95) B4/SD1_7_gap_le_5m/car|long|straight flag: R21 false, analysis true
- within_lt3d/t3 K8 cell(0.95) B0a0.125/NIP_not_in_path/car|long|straight flag: R21 true, analysis false
- within_lt3d/tab K8 validity(C1 level 0.99861) B4/PD7_primary flagged: R21 ["car|long|new", "pedestrian|long|static", "pedestrian|long|turning"], analysis ["car|long|new", "pedestrian|long|static"]
- within_lt3d/tab K8 validity(C1 level 0.95000) B0a0.5/PD7_primary flagged: R21 ["car|long|new", "pedestrian|long|static", "pedestrian|long|straight", "pedestrian|long|turning"], analysis ["car|long|new", "pedestrian|long|static", "pedestrian|long|turning"]
- within_lt3d/tab K8 validity(C1 level 0.95000) B0d0.2/SD1_7_gap_le_5m flagged: R21 ["pedestrian|long|static", "pedestrian|long|turning"], analysis ["pedestrian|long|turning"]
- within_lt3d/tab K8 validity(C1 level 0.99861) RETUNED/PD7_primary flagged: R21 ["car|long|new", "pedestrian|long|static", "pedestrian|long|turning"], analysis ["car|long|new", "pedestrian|long|static"]
- within_lt3d/tab K8 cell(0.95) B0a0.5/PD7_primary/pedestrian|long|straight flag: R21 true, analysis false
- within_lt3d/tab K8 cell(0.95) RETUNED/PD7_primary/pedestrian|long|straight flag: R21 true, analysis false
- within_lt3d/tab K8 cell(0.95) B0d0.2/SD1_7_gap_le_5m/pedestrian|long|static flag: R21 true, analysis false
- within_lt3d/tab K8 cell(0.95) B0a0.25/NIP_not_in_path/large|long|new flag: R21 true, analysis false
- within_lt3d/tab K8 cell(0.95) B0a0.333/NIP_not_in_path/car|lat|turning flag: R21 true, analysis false
- transfer_lt3d/t1/Mstar/PD7_primary R21-own family (check): R21 ["car|long|static", "car|long|straight", "car|long|new", "car|lat|static", "car|lat|straight", "pedestrian|long|static", "pedestrian|long|turning", "pedestri..., analysis ["car|long|static", "car|long|straight", "car|long|new", "car|lat|static", "car|lat|straight", "pedestrian|long|turning", "pedestrian|lat|turning"]
- transfer_lt3d/t1/Mstar/SD1_7_gap_le_5m R21-own family (check): R21 ["car|long|static"], analysis []
- transfer_lt3d/t1/B4/PD7_primary flagged cells: R21 ["car|long|new", "pedestrian|long|turning"], analysis ["pedestrian|long|turning"]
- transfer_lt3d/t1 K8 validity(C1 level 0.99972) B4/PD7_primary flagged: R21 ["car|long|new", "pedestrian|long|turning"], analysis ["pedestrian|long|turning"]
- transfer_lt3d/t1 K8 validity(C1 level 0.95000) B0a0.25/SD1_7_gap_le_5m flagged: R21 ["pedestrian|long|turning"], analysis ["pedestrian|long|static", "pedestrian|long|turning"]
- transfer_lt3d/t1 K8 cell(0.95) B0a0.25/SD1_7_gap_le_5m/pedestrian|long|static flag: R21 false, analysis true
- transfer_lt3d/t1 K8 cell(0.95) B0a0.25/NIP_not_in_path/large|long|straight flag: R21 true, analysis false
- transfer_lt3d/t3/Mstar/PD7_primary R21-own family (check): R21 ["car|long|static", "car|long|straight", "car|long|turning", "car|long|new", "car|lat|static", "pedestrian|long|static", "pedestrian|long|straight", "pedestr..., analysis ["car|long|static", "car|long|straight", "car|long|new", "car|lat|static", "pedestrian|long|static", "pedestrian|long|turning", "pedestrian|lat|static"]
- transfer_lt3d/t3/Mstar/SD1_7_gap_le_5m R21-own family (check): R21 ["car|lat|static"], analysis []
- transfer_lt3d/t3 K8 validity(C1 level 0.95000) B0d0.3/PD7_primary flagged: R21 ["car|long|straight", "car|long|turning"], analysis ["car|long|straight", "car|long|turning", "large|long|straight"]
- transfer_lt3d/t3 K8 cell(0.95) B0d0.3/PD7_primary/large|long|straight flag: R21 false, analysis true
- transfer_lt3d/t3 K8 cell(0.95) RETUNED/PD7_primary/large|long|straight flag: R21 false, analysis true
