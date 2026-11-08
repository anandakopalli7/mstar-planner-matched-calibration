# R21 re-derivation summary

Descriptive review; the frozen verdict stands whatever this shows (plan section 9). Rules: R21_DESIGN_v01.md.

- B = 40000 (analysis 40000); power check 500 datasets; bound tolerance 0.0024
- exact weight reproduction: {"n_bounds": 480, "max_abs_diff": 4.440892098500626e-16, "exact": true}
- comparisons: {"agree": 108059, "MC-borderline": 2, "info": 48}
- runtime 245 s; memory {"working_set_mb": 187, "peak_working_set_mb": 416, "peak_private_mb": 434}

## H1

- R21: holds = True (T1 True, T3 True)
- without zero-SE removals: {"holds": true, "V_t1": ["B3"], "V_t3": ["B0", "B3"], "zero_se_removed_t1": [], "zero_se_removed_t3": []}

- within_lt3d/t1: Valid(M*) True; V_t ['B3']; Form B met True; UB {'B3': -0.7602}; RETUNED {'0': 'B0a1', '1': 'B0d0.02', '2': 'B0a1', '3': 'B0d0.02', '4': 'B0a1'}
- within_lt3d/t3: Valid(M*) True; V_t ['B0', 'B3']; Form B met True; UB {'B0': -0.5819, 'B3': -0.6664}; RETUNED {'0': 'B0a0.25', '1': 'B0a0.125', '2': 'B0d0.3', '3': 'B0a0.125', '4': 'B0a0.25'}
- transfer_lt3d/t1: Valid(M*) False; V_t ['B3']; Form B met False; UB {'B3': -0.7223}; RETUNED {'all': 'B0a1'}
- transfer_lt3d/t3: Valid(M*) False; V_t ['B0', 'B3']; Form B met False; UB {'B0': -0.5829, 'B3': -0.609}; RETUNED {'all': 'B0d0.3'}
- H2: {"bound_form_holds": true, "p": 2.499937501562461e-05, "multiplier": 1}
- H3: {"bound_form_holds": false, "validJ_both": true, "p_form": 1.0, "multiplier": 4, "p": 1.0, "p_rule": "p = max_t min(1, 2|V^J| max p_c) (plan 6.1); 1 when ValidJ(M*Jx) fails on a tracker"}
- H4: {"bound_form_holds": false, "valid_Mstar_both": false, "p_form_b": 9.999750006249843e-05, "multiplier": 4, "p": 1.0, "p_rule": "p = max_t min(1, 2|V_t| max p_c) (plan 6.1); 1 when Valid(M*) fails on a tracker (H1's formula includes Valid)"}

## Disagreements (0)


## MC-borderline (2)

- within_lt3d/t3/Mstar/SD1_7_gap_le_5m R21-own family (check): R21 ["car|long|static", "car|long|straight", "car|lat|static", "car|lat|straight", "car|lat|new", "pedestrian|long|static", "pedestrian|lat|static", "pedestrian|..., analysis ["car|long|static", "car|long|straight", "car|lat|static", "car|lat|straight", "car|lat|new", "pedestrian|long|static", "pedestrian|lat|static", "pedestrian|...
- transfer_lt3d/t1/B6/PD_inpath shown_above: R21 false, analysis true
