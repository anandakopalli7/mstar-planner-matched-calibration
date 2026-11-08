# X3 A4 (5): AB3DMOT without unmatched tracks

**X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test)** -- added after review (amendment A4)

Every track row with tr_inst = -1 (no annotation match) removed from the planner's input after loading (203733 track rows over 375 logs); matched tracks unchanged; decision mode; registered screen with the record's roles; seeds [20261201, 2, 15] / [20261202, 2, 15].

| arm | infeasible (all tracks, record) | progress (record) | registered (record Valid) |
|---|---|---|---|
| Mstar_matched_only | 0.7570 (0.8907) | 0.9765 (0.9812) | flagged (False) |
| Z0_matched_only | 0.0044 (0.0063) | 0.9949 (0.9929) | flagged (False) |

Reading (fixed by A4): the infeasible rate does not fall by more than half (0.8907 -> 0.7570): the text drops the false-positive explanation.
