# X3 (c1): interval sensitivity of the quantities that decided H1 (v01)

**X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test)**

Plan `20_DESIGN/X3_POSTREG_EXPLORATORY_PLAN_v01.md` section 2(c1) (sha256 38e2526d...); referee concern M4. Route within_lt3d, decision mode, T1 and T3. JSON: `x3_c1_intervals_v01.json`.

## Methods

- **i_rec**: (i) record's bootstrap bound, record weights B=40000 (reproduction)
- **i_x3**: (i) record's bootstrap bound, X3 weights B=4000
- **ii_x3**: (ii) studentised log bootstrap with SE floor, X3 weights B=4000 (primary (ii))
- **ii_rec**: (ii) studentised log bootstrap with SE floor, record weights B=40000 (MC sensitivity)
- **iii**: (iii) design-effect Wilson, Bonferroni, centre = record's estimate (primary (iii))
- **iii_pooledcentre**: (iii') design-effect Wilson, Bonferroni, centre = record-pooled x/n (variant)

Families and evaluable sets are the record's. Thresholds: a flag is LB > 0.05; HK1c passes at UB <= 0.08. M* is judged at one-sided 0.95; a comparator's removal conditions at 1 - 0.0125/9 = 0.998611. The record's (i) is the sup-t bound on the bootstrap SE (for one cell, the basic bootstrap bound); the pure percentile UB of HK1c is in the JSON (`hk1c_ub_pure_percentile`).

## Reproduction of the record by (i) on the record's weights

- t1: largest absolute difference over 194 numeric checks = 3.11e-15; list / status mismatches = 0; RETUNED composite mismatches against the record = 0.
- t3: largest absolute difference over 195 numeric checks = 5.33e-15; list / status mismatches = 0; RETUNED composite mismatches against the record = 0.

## M*'s pooled HK1c upper bound at 0.995 (passes at <= 0.08)

| Tracker | Population | i_rec | i_x3 | ii_x3 | ii_rec | iii | iii_pooledcentre |
|---|---|---|---|---|---|---|---|
| t1 | PD7_primary | 0.0482 | 0.0481 | 0.0485 | 0.0487 | 0.0482 | 0.0496 |
| t1 | SD1_7_gap_le_5m | 0.0473 | 0.0468 | 0.0521 | 0.0526 | 0.0449 | 0.0385 |
| t1 | PD_inpath | 0.0546 | 0.0550 | 0.0606 | 0.0598 | 0.0551 | 0.0493 |
| t3 | PD7_primary | 0.0471 | 0.0473 | 0.0475 | 0.0474 | 0.0471 | 0.0487 |
| t3 | SD1_7_gap_le_5m | 0.0412 | 0.0409 | 0.0447 | 0.0450 | 0.0396 | 0.0369 |
| t3 | PD_inpath | 0.0521 | 0.0514 | 0.0527 | 0.0536 | 0.0535 | 0.0480 |

## M*'s largest simultaneous 0.95 upper bound per population (descriptive, never gated)

| Tracker | Population | i_rec | i_x3 | ii_x3 | ii_rec | iii | iii_pooledcentre |
|---|---|---|---|---|---|---|---|
| t1 | PD7_primary | 0.1268 (large|long|turning) | 0.1269 (large|long|turning) | 0.1621 (large|lat|new) | 0.1633 (large|lat|new) | 0.1970 (large|lat|new) | 0.2177 (large|lat|new) |
| t1 | SD1_7_gap_le_5m | 0.1184 (pedestrian|lat|straight) | 0.1183 (pedestrian|lat|straight) | 0.1578 (pedestrian|lat|straight) | 0.1570 (pedestrian|lat|straight) | 0.1434 (car|long|turning) | 0.1595 (pedestrian|long|turning) |
| t1 | PD_inpath | 0.1285 (car|lat|straight) | 0.1277 (car|lat|straight) | 0.1556 (car|lat|straight) | 0.1553 (car|lat|straight) | 0.1626 (car|lat|straight) | 0.1561 (large|long|straight) |
| t3 | PD7_primary | 0.1219 (large|long|turning) | 0.1224 (large|long|turning) | 0.1622 (large|long|turning) | 0.1606 (large|long|turning) | 0.1458 (large|long|turning) | 0.1333 (large|lat|turning) |
| t3 | SD1_7_gap_le_5m | 0.1096 (large|lat|straight) | 0.1097 (large|lat|straight) | 0.1653 (large|lat|straight) | 0.1660 (large|lat|straight) | 0.1289 (large|lat|static) | 0.1628 (large|long|static) |
| t3 | PD_inpath | 0.1569 (car|lat|straight) | 0.1555 (car|lat|straight) | 0.1894 (car|lat|straight) | 0.1884 (car|lat|straight) | 0.1817 (car|lat|straight) | 0.1801 (car|lat|straight) |

## M*'s flags under each method (any entry here is a status change for M*)

| Tracker | Population | Method | Flag |
|---|---|---|---|
| t1 | PD7_primary | iii | car|lat|static |
| t1 | PD7_primary | iii | family:car|lat|static |
| t1 | PD7_primary | iii_pooledcentre | car|lat|new |
| t1 | PD7_primary | iii_pooledcentre | pedestrian|long|static |
| t1 | PD7_primary | iii_pooledcentre | pedestrian|lat|static |
| t1 | PD7_primary | iii_pooledcentre | pedestrian|lat|turning |
| t1 | PD7_primary | iii_pooledcentre | family:car|lat|new |
| t1 | PD7_primary | iii_pooledcentre | family:pedestrian|long|static |
| t1 | PD7_primary | iii_pooledcentre | family:pedestrian|lat|static |
| t1 | PD7_primary | iii_pooledcentre | family:pedestrian|lat|turning |
| t3 | PD7_primary | iii_pooledcentre | car|long|new |
| t3 | PD7_primary | iii_pooledcentre | pedestrian|lat|turning |
| t3 | PD7_primary | iii_pooledcentre | family:car|long|new |
| t3 | PD7_primary | iii_pooledcentre | family:pedestrian|lat|turning |
| t3 | PD_inpath | iii | car|lat|straight |
| t3 | PD_inpath | iii_pooledcentre | car|lat|straight |

## Every r1 removal condition of a comparator: its bound under each method

Lower bounds at 0.998611 (flag when > 0.05; '*' marks a flag); for an HK1c row the pooled upper bound (fails when > 0.08).

| Tracker | Arm | Population | Set | Cell | i_rec | i_x3 | ii_x3 | ii_rec | iii | iii_pooledcentre |
|---|---|---|---|---|---|---|---|---|---|---|
| t1 | B0 | PD7_primary | cell | car|long|new | 0.1310* | 0.1355* | 0.1563* | 0.1575* | 0.1589* | 0.1790* |
| t1 | B0 | PD7_primary | cell | car|lat|turning | 0.0670* | 0.0750* | 0.1018* | 0.1035* | 0.1074* | 0.1245* |
| t1 | B0 | PD7_primary | cell | pedestrian|long|static | 0.0502* | 0.0523* | 0.0651* | 0.0658* | 0.0754* | 0.0871* |
| t1 | B0 | PD7_primary | family | car|long|new | 0.1357* | 0.1362* | 0.1565* | 0.1585* | 0.1597* | 0.1797* |
| t1 | B0 | PD7_primary | family | car|lat|turning | 0.0734* | 0.0760* | 0.1021* | 0.1049* | 0.1082* | 0.1254* |
| t1 | B0 | PD7_primary | family | pedestrian|long|static | 0.0530* | 0.0528* | 0.0652* | 0.0665* | 0.0757* | 0.0874* |
| t1 | B1 | PD7_primary | cell | large|long|new | 0.1345* | 0.1295* | 0.2212* | 0.2233* | 0.2245* | 0.2044* |
| t1 | B4 | PD7_primary | cell | car|long|turning | 0.0562* | 0.0574* | 0.0797* | 0.0807* | 0.0898* | 0.0629* |
| t1 | B4 | PD7_primary | cell | car|long|new | 0.2200* | 0.2205* | 0.2441* | 0.2452* | 0.2481* | 0.2749* |
| t1 | B4 | PD7_primary | cell | car|lat|turning | 0.0873* | 0.0909* | 0.1190* | 0.1205* | 0.1271* | 0.1406* |
| t1 | B4 | PD7_primary | cell | car|lat|new | 0.0636* | 0.0660* | 0.0876* | 0.0887* | 0.0969* | 0.1044* |
| t1 | B4 | PD7_primary | cell | pedestrian|long|static | 0.0907* | 0.0909* | 0.1061* | 0.1069* | 0.1192* | 0.1282* |
| t1 | B4 | PD7_primary | cell | pedestrian|long|straight | 0.0608* | 0.0617* | 0.0835* | 0.0846* | 0.1002* | 0.0732* |
| t1 | B4 | PD7_primary | cell | pedestrian|long|turning | 0.0898* | 0.0907* | 0.1093* | 0.1102* | 0.1215* | 0.1283* |
| t1 | B4 | PD7_primary | cell | pedestrian|long|new | 0.0640* | 0.0651* | 0.0878* | 0.0888* | 0.1014* | 0.0905* |
| t1 | B4 | PD7_primary | cell | large|long|new | 0.1233* | 0.1267* | 0.1960* | 0.1993* | 0.2089* | 0.1818* |
| t1 | B4 | PD7_primary | family | car|long|straight | 0.0503* | 0.0501* | 0.0597* | 0.0601* | 0.0639* | 0.0528* |
| t1 | B4 | PD7_primary | family | car|long|turning | 0.0604* | 0.0593* | 0.0803* | 0.0812* | 0.0905* | 0.0635* |
| t1 | B4 | PD7_primary | family | car|long|new | 0.2244* | 0.2226* | 0.2448* | 0.2457* | 0.2490* | 0.2759* |
| t1 | B4 | PD7_primary | family | car|lat|turning | 0.0930* | 0.0935* | 0.1199* | 0.1211* | 0.1281* | 0.1417* |
| t1 | B4 | PD7_primary | family | car|lat|new | 0.0680* | 0.0680* | 0.0882* | 0.0891* | 0.0976* | 0.1051* |
| t1 | B4 | PD7_primary | family | pedestrian|long|static | 0.0935* | 0.0922* | 0.1066* | 0.1072* | 0.1196* | 0.1287* |
| t1 | B4 | PD7_primary | family | pedestrian|long|straight | 0.0649* | 0.0637* | 0.0842* | 0.0850* | 0.1008* | 0.0737* |
| t1 | B4 | PD7_primary | family | pedestrian|long|turning | 0.0933* | 0.0924* | 0.1099* | 0.1106* | 0.1221* | 0.1289* |
| t1 | B4 | PD7_primary | family | pedestrian|long|new | 0.0683* | 0.0672* | 0.0884* | 0.0893* | 0.1021* | 0.0912* |
| t1 | B4 | SD1_7_gap_le_5m | family | car|lat|turning | 0.0618* | 0.0637* | 0.0997* | 0.1020* | 0.1116* | 0.1147* |
| t1 | B4 | PD_inpath | cell | car|long|new | 0.0623* | 0.0599* | 0.1040* | 0.1001* | 0.1140* | 0.1339* |
| t1 | B4 | PD_inpath | family | car|long|new | 0.0659* | 0.0649* | 0.1060* | 0.1023* | 0.1158* | 0.1358* |
| t1 | B4 | PD_inpath | hk1c | pooled UB | 0.0984* | 0.0981* | 0.1052* | 0.1055* | 0.0969* | 0.0794 |
| t1 | B6 | PD7_primary | cell | car|long|turning | 0.0551* | 0.0540* | 0.0766* | 0.0766* | 0.0859* | 0.0643* |
| t1 | B6 | PD7_primary | cell | car|long|new | 0.2114* | 0.2102* | 0.2343* | 0.2342* | 0.2367* | 0.2571* |
| t1 | B6 | PD7_primary | cell | car|lat|straight | 0.0614* | 0.0616* | 0.0763* | 0.0763* | 0.0816* | 0.0711* |
| t1 | B6 | PD7_primary | cell | car|lat|turning | 0.0914* | 0.0921* | 0.1220* | 0.1220* | 0.1277* | 0.1392* |
| t1 | B6 | PD7_primary | cell | car|lat|new | 0.0843* | 0.0852* | 0.1076* | 0.1075* | 0.1138* | 0.1275* |
| t1 | B6 | PD7_primary | family | car|long|turning | 0.0587* | 0.0565* | 0.0774* | 0.0771* | 0.0865* | 0.0648* |
| t1 | B6 | PD7_primary | family | car|long|new | 0.2152* | 0.2129* | 0.2351* | 0.2348* | 0.2376* | 0.2580* |
| t1 | B6 | PD7_primary | family | car|lat|straight | 0.0639* | 0.0633* | 0.0769* | 0.0767* | 0.0821* | 0.0716* |
| t1 | B6 | PD7_primary | family | car|lat|turning | 0.0965* | 0.0956* | 0.1231* | 0.1228* | 0.1287* | 0.1403* |
| t1 | B6 | PD7_primary | family | car|lat|new | 0.0882* | 0.0879* | 0.1084* | 0.1082* | 0.1146* | 0.1283* |
| t1 | B6 | SD1_7_gap_le_5m | family | car|lat|turning | 0.0612* | 0.0602* | 0.1037* | 0.1042* | 0.1137* | 0.1113* |
| t1 | B9 | PD7_primary | cell | car|long|new | 0.0849* | 0.0863* | 0.1111* | 0.1112* | 0.1108* | 0.1273* |
| t1 | B9 | PD7_primary | family | car|long|new | 0.0872* | 0.0868* | 0.1120* | 0.1123* | 0.1113* | 0.1278* |
| t1 | RETUNED | PD7_primary | cell | car|long|new | 0.1130* | 0.1151* | 0.1381* | 0.1401* | 0.1416* | 0.1590* |
| t1 | RETUNED | PD7_primary | cell | car|lat|turning | 0.0633* | 0.0683* | 0.0984* | 0.1011* | 0.1044* | 0.1217* |
| t1 | RETUNED | PD7_primary | family | car|long|new | 0.1179* | 0.1186* | 0.1383* | 0.1407* | 0.1422* | 0.1597* |
| t1 | RETUNED | PD7_primary | family | car|lat|turning | 0.0701* | 0.0730* | 0.0986* | 0.1019* | 0.1052* | 0.1226* |
| t3 | B1 | PD7_primary | family | car|long|new | 0.0511* | 0.0509* | 0.0653* | 0.0659* | 0.0679* | 0.0812* |
| t3 | B4 | PD7_primary | cell | car|long|straight | 0.1549* | 0.1543* | 0.1673* | 0.1685* | 0.1724* | 0.1531* |
| t3 | B4 | PD7_primary | cell | car|long|turning | 0.1538* | 0.1512* | 0.1747* | 0.1768* | 0.1837* | 0.1388* |
| t3 | B4 | PD7_primary | cell | car|long|new | 0.1924* | 0.1914* | 0.2091* | 0.2108* | 0.2185* | 0.2373* |
| t3 | B4 | PD7_primary | cell | large|long|straight | 0.1537* | 0.1531* | 0.1920* | 0.1957* | 0.2004* | 0.2031* |
| t3 | B4 | PD7_primary | cell | large|long|turning | 0.0847* | 0.0791* | 0.1424* | 0.1480* | 0.1601* | 0.1420* |
| t3 | B4 | PD7_primary | cell | large|long|new | 0.1275* | 0.1256* | 0.1855* | 0.1911* | 0.2023* | 0.1936* |
| t3 | B4 | PD7_primary | family | car|long|straight | 0.1580* | 0.1603* | 0.1698* | 0.1692* | 0.1729* | 0.1536* |
| t3 | B4 | PD7_primary | family | car|long|turning | 0.1591* | 0.1616* | 0.1789* | 0.1779* | 0.1844* | 0.1395* |
| t3 | B4 | PD7_primary | family | car|long|new | 0.1967* | 0.1995* | 0.2124* | 0.2116* | 0.2190* | 0.2379* |
| t3 | B4 | PD7_primary | family | large|long|straight | 0.1633* | 0.1713* | 0.1994* | 0.1977* | 0.2018* | 0.2045* |
| t3 | B4 | PD7_primary | pooled | pooled | 0.0523* | 0.0530* | 0.0543* | 0.0540* | 0.0548* | 0.0509* |
| t3 | B4 | SD1_7_gap_le_5m | cell | car|long|straight | 0.1176* | 0.1184* | 0.1421* | 0.1415* | 0.1473* | 0.1336* |
| t3 | B4 | SD1_7_gap_le_5m | cell | car|long|new | 0.1494* | 0.1554* | 0.2105* | 0.2091* | 0.2134* | 0.2301* |
| t3 | B4 | SD1_7_gap_le_5m | cell | large|long|straight | 0.0504* | 0.0569* | 0.1363* | 0.1344* | 0.1601* | 0.1596* |
| t3 | B4 | SD1_7_gap_le_5m | family | car|long|straight | 0.1241* | 0.1240* | 0.1458* | 0.1448* | 0.1491* | 0.1353* |
| t3 | B4 | SD1_7_gap_le_5m | family | car|long|turning | 0.0555* | 0.0582* | 0.1044* | 0.1019* | 0.1144* | 0.0530* |
| t3 | B4 | PD_inpath | cell | car|long|straight | 0.0981* | 0.1042* | 0.1209* | 0.1198* | 0.1303* | 0.0973* |
| t3 | B4 | PD_inpath | cell | car|long|turning | 0.0671* | 0.0749* | 0.1077* | 0.1059* | 0.1202* | 0.0853* |
| t3 | B4 | PD_inpath | cell | car|long|new | 0.0735* | 0.0841* | 0.1103* | 0.1087* | 0.1237* | 0.1444* |
| t3 | B4 | PD_inpath | family | car|long|straight | 0.1036* | 0.1066* | 0.1230* | 0.1221* | 0.1315* | 0.0983* |
| t3 | B4 | PD_inpath | family | car|long|turning | 0.0769* | 0.0793* | 0.1116* | 0.1099* | 0.1223* | 0.0870* |
| t3 | B4 | PD_inpath | family | car|long|new | 0.0823* | 0.0879* | 0.1138* | 0.1123* | 0.1255* | 0.1464* |
| t3 | B4 | PD_inpath | pooled | pooled | 0.0828* | 0.0837* | 0.0890* | 0.0879* | 0.0927* | 0.0867* |
| t3 | B4 | PD_inpath | hk1c | pooled UB | 0.1346* | 0.1338* | 0.1393* | 0.1404* | 0.1318* | 0.1249* |
| t3 | B6 | PD7_primary | cell | car|long|straight | 0.0678* | 0.0678* | 0.0794* | 0.0798* | 0.0842* | 0.0676* |
| t3 | B6 | PD7_primary | cell | car|long|turning | 0.0696* | 0.0692* | 0.0887* | 0.0893* | 0.0972* | 0.0692* |
| t3 | B6 | PD7_primary | cell | car|long|new | 0.1337* | 0.1338* | 0.1509* | 0.1515* | 0.1562* | 0.1723* |
| t3 | B6 | PD7_primary | cell | car|lat|turning | 0.0719* | 0.0719* | 0.0962* | 0.0970* | 0.1068* | 0.1155* |
| t3 | B6 | PD7_primary | cell | car|lat|new | 0.0509* | 0.0502* | 0.0716* | 0.0723* | 0.0802* | 0.0693* |
| t3 | B6 | PD7_primary | family | car|long|straight | 0.0701* | 0.0715* | 0.0796* | 0.0800* | 0.0846* | 0.0679* |
| t3 | B6 | PD7_primary | family | car|long|turning | 0.0735* | 0.0753* | 0.0891* | 0.0897* | 0.0978* | 0.0697* |
| t3 | B6 | PD7_primary | family | car|long|new | 0.1372* | 0.1392* | 0.1512* | 0.1518* | 0.1568* | 0.1730* |
| t3 | B6 | PD7_primary | family | car|lat|turning | 0.0768* | 0.0796* | 0.0967* | 0.0976* | 0.1075* | 0.1162* |
| t3 | B6 | PD7_primary | family | car|lat|new | 0.0551* | 0.0568* | 0.0720* | 0.0727* | 0.0808* | 0.0698* |
| t3 | B9 | PD7_primary | cell | car|long|new | 0.0843* | 0.0846* | 0.1071* | 0.1073* | 0.1077* | 0.1307* |
| t3 | B9 | PD7_primary | family | car|long|new | 0.0850* | 0.0860* | 0.1080* | 0.1083* | 0.1082* | 0.1313* |
| t3 | RETUNED | PD7_primary | cell | car|long|turning | 0.0514* | 0.0521* | 0.0728* | 0.0724* | 0.0807* | 0.0551* |
| t3 | RETUNED | PD7_primary | cell | car|long|new | 0.1104* | 0.1116* | 0.1297* | 0.1294* | 0.1327* | 0.1570* |
| t3 | RETUNED | PD7_primary | family | car|long|straight | 0.0503* | 0.0505* | 0.0618* | 0.0622* | 0.0664* | 0.0542* |
| t3 | RETUNED | PD7_primary | family | car|long|turning | 0.0544* | 0.0549* | 0.0733* | 0.0739* | 0.0811* | 0.0554* |
| t3 | RETUNED | PD7_primary | family | car|long|new | 0.1131* | 0.1141* | 0.1301* | 0.1307* | 0.1331* | 0.1575* |

## Status, V_t and H1 per method

| Tracker | Method | Valid(M*) | V_t | removed | H1 |
|---|---|---|---|---|---|
| t1 | i_rec | True | B3 | B0, B1, B4, B6, B9, RETUNED | True |
| t1 | i_x3 | True | B3 | B0, B1, B4, B6, B9, RETUNED | True |
| t1 | ii_x3 | True | B3 | B0, B1, B4, B6, B9, RETUNED | True |
| t1 | ii_rec | True | B3 | B0, B1, B4, B6, B9, RETUNED | True |
| t1 | iii | False | B3 | B0, B1, B4, B6, B9, RETUNED | False |
| t1 | iii_pooledcentre | False | B3 | B0, B1, B4, B6, B9, RETUNED | False |
| t3 | i_rec | True | B0, B3 | B1, B4, B6, B9, RETUNED | True |
| t3 | i_x3 | True | B0, B3 | B1, B4, B6, B9, RETUNED | True |
| t3 | ii_x3 | True | B0, B3 | B1, B4, B6, B9, RETUNED | True |
| t3 | ii_rec | True | B0, B3 | B1, B4, B6, B9, RETUNED | True |
| t3 | iii | False | B0, B3 | B1, B4, B6, B9, RETUNED | False |
| t3 | iii_pooledcentre | False | B0, B3 | B1, B4, B6, B9, RETUNED | False |

## Status changes against the record ((i), record weights)

| Tracker | Method | Arm | Population | What | Record | Method | Detail |
|---|---|---|---|---|---|---|---|
| t1 | ii_x3 | B0 | PD7_primary | flagged cell set | - | - | lost []; new ['car|lat|new', 'large|long|new', 'pedestrian|long|turning']; lost family []; new family ['car|lat|new', 'pedestrian|long|turning'] |
| t1 | ii_x3 | B0 | SD1_7_gap_le_5m | NoFlag | True | False |  |
| t1 | ii_x3 | B0 | SD1_7_gap_le_5m | FamFlag | False | True |  |
| t1 | ii_x3 | B0 | SD1_7_gap_le_5m | flagged cell set | - | - | lost []; new ['car|lat|turning']; lost family []; new family ['car|lat|turning'] |
| t1 | ii_x3 | B0 | PD_inpath | NoFlag | True | False |  |
| t1 | ii_x3 | B0 | PD_inpath | FamFlag | False | True |  |
| t1 | ii_x3 | B0 | PD_inpath | flagged cell set | - | - | lost []; new ['car|lat|turning', 'car|long|new']; lost family []; new family ['car|long|new'] |
| t1 | ii_x3 | B1 | PD7_primary | FamFlag | False | True |  |
| t1 | ii_x3 | B1 | PD7_primary | flagged cell set | - | - | lost []; new ['car|lat|turning', 'large|long|straight', 'large|long|turning']; lost family []; new family ['car|lat|turning', 'large|long|straight'] |
| t1 | ii_x3 | B1 | SD1_7_gap_le_5m | NoFlag | True | False |  |
| t1 | ii_x3 | B1 | SD1_7_gap_le_5m | FamFlag | False | True |  |
| t1 | ii_x3 | B1 | SD1_7_gap_le_5m | flagged cell set | - | - | lost []; new ['car|lat|turning']; lost family []; new family ['car|lat|turning'] |
| t1 | ii_x3 | B1 | PD_inpath | NoFlag | True | False |  |
| t1 | ii_x3 | B1 | PD_inpath | flagged cell set | - | - | lost []; new ['car|lat|turning']; lost family []; new family [] |
| t1 | ii_x3 | B4 | PD7_primary | flagged cell set | - | - | lost []; new ['car|lat|straight', 'car|long|straight']; lost family []; new family ['car|lat|straight'] |
| t1 | ii_x3 | B4 | SD1_7_gap_le_5m | NoFlag | True | False |  |
| t1 | ii_x3 | B4 | SD1_7_gap_le_5m | flagged cell set | - | - | lost []; new ['car|lat|turning', 'car|long|new', 'pedestrian|long|static', 'pedestrian|long|turning']; lost family []; new family ['pedestrian|long|static'] |
| t1 | ii_x3 | B4 | PD_inpath | NoFlag_pool | True | False |  |
| t1 | ii_x3 | B4 | PD_inpath | flagged cell set | - | - | lost []; new ['car|lat|straight', 'car|lat|turning']; lost family []; new family ['car|lat|straight'] |
| t1 | ii_x3 | B6 | PD7_primary | flagged cell set | - | - | lost []; new ['car|long|straight', 'large|long|new']; lost family []; new family ['car|long|straight'] |
| t1 | ii_x3 | B6 | SD1_7_gap_le_5m | NoFlag | True | False |  |
| t1 | ii_x3 | B6 | SD1_7_gap_le_5m | flagged cell set | - | - | lost []; new ['car|lat|straight', 'car|lat|turning']; lost family []; new family ['car|lat|straight'] |
| t1 | ii_x3 | B6 | PD_inpath | NoFlag | True | False |  |
| t1 | ii_x3 | B6 | PD_inpath | FamFlag | False | True |  |
| t1 | ii_x3 | B6 | PD_inpath | flagged cell set | - | - | lost []; new ['car|long|new']; lost family []; new family ['car|long|new'] |
| t1 | ii_x3 | B9 | PD7_primary | flagged cell set | - | - | lost []; new ['large|long|new']; lost family []; new family [] |
| t1 | ii_x3 | RETUNED | PD7_primary | flagged cell set | - | - | lost []; new ['car|lat|new', 'large|long|new', 'pedestrian|long|static']; lost family []; new family ['car|lat|new', 'pedestrian|long|static'] |
| t1 | ii_x3 | RETUNED | SD1_7_gap_le_5m | NoFlag | True | False |  |
| t1 | ii_x3 | RETUNED | SD1_7_gap_le_5m | FamFlag | False | True |  |
| t1 | ii_x3 | RETUNED | SD1_7_gap_le_5m | flagged cell set | - | - | lost []; new ['car|lat|turning']; lost family []; new family ['car|lat|turning'] |
| t1 | ii_x3 | RETUNED | PD_inpath | NoFlag | True | False |  |
| t1 | ii_x3 | RETUNED | PD_inpath | FamFlag | False | True |  |
| t1 | ii_x3 | RETUNED | PD_inpath | flagged cell set | - | - | lost []; new ['car|lat|turning', 'car|long|new']; lost family []; new family ['car|long|new'] |
| t1 | ii_rec | B0 | PD7_primary | flagged cell set | - | - | lost []; new ['car|lat|new', 'large|long|new', 'pedestrian|long|turning']; lost family []; new family ['car|lat|new', 'pedestrian|long|turning'] |
| t1 | ii_rec | B0 | SD1_7_gap_le_5m | NoFlag | True | False |  |
| t1 | ii_rec | B0 | SD1_7_gap_le_5m | FamFlag | False | True |  |
| t1 | ii_rec | B0 | SD1_7_gap_le_5m | flagged cell set | - | - | lost []; new ['car|lat|turning']; lost family []; new family ['car|lat|turning'] |
| t1 | ii_rec | B0 | PD_inpath | NoFlag | True | False |  |
| t1 | ii_rec | B0 | PD_inpath | FamFlag | False | True |  |
| t1 | ii_rec | B0 | PD_inpath | flagged cell set | - | - | lost []; new ['car|lat|turning', 'car|long|new']; lost family []; new family ['car|long|new'] |
| t1 | ii_rec | B1 | PD7_primary | FamFlag | False | True |  |
| t1 | ii_rec | B1 | PD7_primary | flagged cell set | - | - | lost []; new ['car|lat|turning', 'large|long|straight', 'large|long|turning']; lost family []; new family ['car|lat|turning', 'large|long|straight'] |
| t1 | ii_rec | B1 | SD1_7_gap_le_5m | NoFlag | True | False |  |
| t1 | ii_rec | B1 | SD1_7_gap_le_5m | FamFlag | False | True |  |
| t1 | ii_rec | B1 | SD1_7_gap_le_5m | flagged cell set | - | - | lost []; new ['car|lat|turning']; lost family []; new family ['car|lat|turning'] |
| t1 | ii_rec | B1 | PD_inpath | NoFlag | True | False |  |
| t1 | ii_rec | B1 | PD_inpath | flagged cell set | - | - | lost []; new ['car|lat|turning']; lost family []; new family [] |
| t1 | ii_rec | B4 | PD7_primary | flagged cell set | - | - | lost []; new ['car|lat|straight', 'car|long|straight']; lost family []; new family ['car|lat|straight'] |
| t1 | ii_rec | B4 | SD1_7_gap_le_5m | NoFlag | True | False |  |
| t1 | ii_rec | B4 | SD1_7_gap_le_5m | flagged cell set | - | - | lost []; new ['car|lat|turning', 'car|long|new', 'pedestrian|long|static', 'pedestrian|long|turning']; lost family []; new family ['pedestrian|long|static'] |
| t1 | ii_rec | B4 | PD_inpath | NoFlag_pool | True | False |  |
| t1 | ii_rec | B4 | PD_inpath | flagged cell set | - | - | lost []; new ['car|lat|straight', 'car|lat|turning']; lost family []; new family ['car|lat|straight'] |
| t1 | ii_rec | B6 | PD7_primary | flagged cell set | - | - | lost []; new ['car|long|straight', 'large|long|new']; lost family []; new family ['car|long|straight'] |
| t1 | ii_rec | B6 | SD1_7_gap_le_5m | NoFlag | True | False |  |
| t1 | ii_rec | B6 | SD1_7_gap_le_5m | flagged cell set | - | - | lost []; new ['car|lat|straight', 'car|lat|turning']; lost family []; new family ['car|lat|straight'] |
| t1 | ii_rec | B6 | PD_inpath | NoFlag | True | False |  |
| t1 | ii_rec | B6 | PD_inpath | FamFlag | False | True |  |
| t1 | ii_rec | B6 | PD_inpath | flagged cell set | - | - | lost []; new ['car|long|new']; lost family []; new family ['car|long|new'] |
| t1 | ii_rec | B9 | PD7_primary | flagged cell set | - | - | lost []; new ['large|long|new']; lost family []; new family [] |
| t1 | ii_rec | RETUNED | PD7_primary | flagged cell set | - | - | lost []; new ['car|lat|new', 'large|long|new', 'pedestrian|long|static']; lost family []; new family ['car|lat|new', 'pedestrian|long|static'] |
| t1 | ii_rec | RETUNED | SD1_7_gap_le_5m | NoFlag | True | False |  |
| t1 | ii_rec | RETUNED | SD1_7_gap_le_5m | FamFlag | False | True |  |
| t1 | ii_rec | RETUNED | SD1_7_gap_le_5m | flagged cell set | - | - | lost []; new ['car|lat|turning']; lost family []; new family ['car|lat|turning'] |
| t1 | ii_rec | RETUNED | PD_inpath | NoFlag | True | False |  |
| t1 | ii_rec | RETUNED | PD_inpath | FamFlag | False | True |  |
| t1 | ii_rec | RETUNED | PD_inpath | flagged cell set | - | - | lost []; new ['car|lat|turning']; lost family []; new family ['car|long|new'] |
| t1 | iii | Mstar | - | valid | True | False |  |
| t1 | iii | Mstar | - | shown_above | False | True |  |
| t1 | iii | Mstar | - | shown_above_9_conditions | False | True |  |
| t1 | iii | Mstar | PD7_primary | NoFlag | True | False |  |
| t1 | iii | Mstar | PD7_primary | FamFlag | False | True |  |
| t1 | iii | Mstar | PD7_primary | flagged cell set | - | - | lost []; new ['car|lat|static']; lost family []; new family ['car|lat|static'] |
| t1 | iii | B0 | PD7_primary | flagged cell set | - | - | lost []; new ['car|lat|new', 'car|long|turning', 'large|long|new', 'pedestrian|long|straight', 'pedestrian|long|turning']; lost family []; new family ['car|lat|new', 'car|long|turning', 'pedestrian|long|straight', 'pedestrian|long|turning'] |
| t1 | iii | B0 | SD1_7_gap_le_5m | NoFlag | True | False |  |
| t1 | iii | B0 | SD1_7_gap_le_5m | FamFlag | False | True |  |
| t1 | iii | B0 | SD1_7_gap_le_5m | flagged cell set | - | - | lost []; new ['car|lat|turning']; lost family []; new family ['car|lat|turning'] |
| t1 | iii | B0 | PD_inpath | NoFlag | True | False |  |
| t1 | iii | B0 | PD_inpath | FamFlag | False | True |  |
| t1 | iii | B0 | PD_inpath | flagged cell set | - | - | lost []; new ['car|lat|turning', 'car|long|new']; lost family []; new family ['car|long|new'] |
| t1 | iii | B1 | PD7_primary | FamFlag | False | True |  |
| t1 | iii | B1 | PD7_primary | flagged cell set | - | - | lost []; new ['car|lat|turning', 'large|long|straight', 'large|long|turning']; lost family []; new family ['car|lat|turning', 'large|long|straight'] |
| t1 | iii | B1 | SD1_7_gap_le_5m | NoFlag | True | False |  |
| t1 | iii | B1 | SD1_7_gap_le_5m | FamFlag | False | True |  |
| t1 | iii | B1 | SD1_7_gap_le_5m | flagged cell set | - | - | lost []; new ['car|lat|turning']; lost family []; new family ['car|lat|turning'] |
| t1 | iii | B1 | PD_inpath | NoFlag | True | False |  |
| t1 | iii | B1 | PD_inpath | flagged cell set | - | - | lost []; new ['car|lat|turning']; lost family []; new family [] |
| t1 | iii | B4 | PD7_primary | flagged cell set | - | - | lost []; new ['car|lat|straight', 'car|long|straight', 'large|long|straight', 'large|long|turning']; lost family []; new family ['car|lat|straight', 'large|long|straight'] |
| t1 | iii | B4 | SD1_7_gap_le_5m | NoFlag | True | False |  |
| t1 | iii | B4 | SD1_7_gap_le_5m | flagged cell set | - | - | lost []; new ['car|lat|straight', 'car|lat|turning', 'car|long|new', 'pedestrian|long|static', 'pedestrian|long|straight', 'pedestrian|long|turning']; lost family []; new family ['car|lat|straight', 'pedestrian|long|static'] |
| t1 | iii | B4 | PD_inpath | NoFlag_pool | True | False |  |
| t1 | iii | B4 | PD_inpath | flagged cell set | - | - | lost []; new ['car|lat|straight', 'car|lat|turning']; lost family []; new family ['car|lat|straight'] |
| t1 | iii | B6 | PD7_primary | flagged cell set | - | - | lost []; new ['car|long|straight', 'large|long|new']; lost family []; new family ['car|long|straight'] |
| t1 | iii | B6 | SD1_7_gap_le_5m | NoFlag | True | False |  |
| t1 | iii | B6 | SD1_7_gap_le_5m | flagged cell set | - | - | lost []; new ['car|lat|straight', 'car|lat|turning', 'car|long|new']; lost family []; new family ['car|lat|straight'] |
| t1 | iii | B6 | PD_inpath | NoFlag | True | False |  |
| t1 | iii | B6 | PD_inpath | FamFlag | False | True |  |
| t1 | iii | B6 | PD_inpath | flagged cell set | - | - | lost []; new ['car|long|new']; lost family []; new family ['car|long|new'] |
| t1 | iii | B9 | PD7_primary | flagged cell set | - | - | lost []; new ['large|long|new']; lost family []; new family [] |
| t1 | iii | RETUNED | PD7_primary | flagged cell set | - | - | lost []; new ['car|lat|new', 'large|long|new', 'pedestrian|long|static', 'pedestrian|long|turning']; lost family []; new family ['car|lat|new', 'pedestrian|long|static', 'pedestrian|long|turning'] |
| t1 | iii | RETUNED | SD1_7_gap_le_5m | NoFlag | True | False |  |
| t1 | iii | RETUNED | SD1_7_gap_le_5m | FamFlag | False | True |  |
| t1 | iii | RETUNED | SD1_7_gap_le_5m | flagged cell set | - | - | lost []; new ['car|lat|turning']; lost family []; new family ['car|lat|turning'] |
| t1 | iii | RETUNED | PD_inpath | NoFlag | True | False |  |
| t1 | iii | RETUNED | PD_inpath | FamFlag | False | True |  |
| t1 | iii | RETUNED | PD_inpath | flagged cell set | - | - | lost []; new ['car|lat|turning', 'car|long|new']; lost family []; new family ['car|long|new'] |
| t1 | iii | - | - | V_t / H1 | [['B3'], True] | [['B3'], False] | Form B UB {'B3': -0.7602} |
| t1 | iii_pooledcentre | Mstar | - | valid | True | False |  |
| t1 | iii_pooledcentre | Mstar | - | shown_above | False | True |  |
| t1 | iii_pooledcentre | Mstar | - | shown_above_9_conditions | False | True |  |
| t1 | iii_pooledcentre | Mstar | PD7_primary | NoFlag | True | False |  |
| t1 | iii_pooledcentre | Mstar | PD7_primary | FamFlag | False | True |  |
| t1 | iii_pooledcentre | Mstar | PD7_primary | flagged cell set | - | - | lost []; new ['car|lat|new', 'pedestrian|lat|static', 'pedestrian|lat|turning', 'pedestrian|long|static']; lost family []; new family ['car|lat|new', 'pedestrian|lat|static', 'pedestrian|lat|turning', 'pedestrian|long|static'] |
| t1 | iii_pooledcentre | B0 | PD7_primary | flagged cell set | - | - | lost []; new ['car|lat|new', 'large|long|new', 'pedestrian|long|turning']; lost family []; new family ['car|lat|new', 'pedestrian|long|turning'] |
| t1 | iii_pooledcentre | B0 | SD1_7_gap_le_5m | NoFlag | True | False |  |
| t1 | iii_pooledcentre | B0 | SD1_7_gap_le_5m | FamFlag | False | True |  |
| t1 | iii_pooledcentre | B0 | SD1_7_gap_le_5m | flagged cell set | - | - | lost []; new ['car|lat|turning', 'pedestrian|long|static', 'pedestrian|long|turning']; lost family []; new family ['car|lat|turning', 'pedestrian|long|static', 'pedestrian|long|turning'] |
| t1 | iii_pooledcentre | B0 | PD_inpath | NoFlag | True | False |  |
| t1 | iii_pooledcentre | B0 | PD_inpath | FamFlag | False | True |  |
| t1 | iii_pooledcentre | B0 | PD_inpath | flagged cell set | - | - | lost []; new ['car|lat|turning', 'car|long|new']; lost family []; new family ['car|long|new'] |
| t1 | iii_pooledcentre | B1 | PD7_primary | FamFlag | False | True |  |
| t1 | iii_pooledcentre | B1 | PD7_primary | flagged cell set | - | - | lost []; new ['car|lat|turning', 'large|long|straight', 'large|long|turning']; lost family []; new family ['car|lat|turning', 'large|long|straight'] |
| t1 | iii_pooledcentre | B1 | SD1_7_gap_le_5m | NoFlag | True | False |  |
| t1 | iii_pooledcentre | B1 | SD1_7_gap_le_5m | FamFlag | False | True |  |
| t1 | iii_pooledcentre | B1 | SD1_7_gap_le_5m | flagged cell set | - | - | lost []; new ['car|lat|turning']; lost family []; new family ['car|lat|turning'] |
| t1 | iii_pooledcentre | B1 | PD_inpath | NoFlag | True | False |  |
| t1 | iii_pooledcentre | B1 | PD_inpath | flagged cell set | - | - | lost []; new ['car|lat|turning']; lost family []; new family [] |
| t1 | iii_pooledcentre | B4 | PD7_primary | flagged cell set | - | - | lost []; new ['car|long|straight', 'large|long|turning']; lost family []; new family ['large|long|straight'] |
| t1 | iii_pooledcentre | B4 | SD1_7_gap_le_5m | NoFlag | True | False |  |
| t1 | iii_pooledcentre | B4 | SD1_7_gap_le_5m | flagged cell set | - | - | lost []; new ['car|lat|turning', 'car|long|new', 'pedestrian|long|static', 'pedestrian|long|turning']; lost family []; new family ['pedestrian|long|static'] |
| t1 | iii_pooledcentre | B4 | PD_inpath | HK1c | False | True |  |
| t1 | iii_pooledcentre | B4 | PD_inpath | flagged cell set | - | - | lost []; new ['car|lat|new', 'car|lat|straight', 'car|lat|turning']; lost family []; new family ['car|lat|straight'] |
| t1 | iii_pooledcentre | B6 | PD7_primary | flagged cell set | - | - | lost []; new ['large|lat|new', 'large|lat|turning', 'large|long|new', 'pedestrian|lat|new', 'pedestrian|lat|static', 'pedestrian|lat|turning', 'pedestrian|long|static']; lost family []; new family ['pedestrian|lat|new', 'pedestrian|lat|static', 'pedestrian|lat|turning', 'pedestrian|long|static'] |
| t1 | iii_pooledcentre | B6 | SD1_7_gap_le_5m | NoFlag | True | False |  |
| t1 | iii_pooledcentre | B6 | SD1_7_gap_le_5m | flagged cell set | - | - | lost []; new ['car|lat|turning']; lost family []; new family [] |
| t1 | iii_pooledcentre | B6 | PD_inpath | NoFlag | True | False |  |
| t1 | iii_pooledcentre | B6 | PD_inpath | FamFlag | False | True |  |
| t1 | iii_pooledcentre | B6 | PD_inpath | flagged cell set | - | - | lost []; new ['car|long|new']; lost family []; new family ['car|long|new'] |
| t1 | iii_pooledcentre | B9 | PD7_primary | flagged cell set | - | - | lost []; new ['large|long|new']; lost family []; new family [] |
| t1 | iii_pooledcentre | RETUNED | PD7_primary | flagged cell set | - | - | lost []; new ['car|lat|new', 'large|long|new', 'pedestrian|long|static', 'pedestrian|long|turning']; lost family []; new family ['car|lat|new', 'pedestrian|long|static', 'pedestrian|long|turning'] |
| t1 | iii_pooledcentre | RETUNED | SD1_7_gap_le_5m | NoFlag | True | False |  |
| t1 | iii_pooledcentre | RETUNED | SD1_7_gap_le_5m | FamFlag | False | True |  |
| t1 | iii_pooledcentre | RETUNED | SD1_7_gap_le_5m | flagged cell set | - | - | lost []; new ['car|lat|turning', 'pedestrian|long|static']; lost family []; new family ['car|lat|turning', 'pedestrian|long|static'] |
| t1 | iii_pooledcentre | RETUNED | PD_inpath | NoFlag | True | False |  |
| t1 | iii_pooledcentre | RETUNED | PD_inpath | FamFlag | False | True |  |
| t1 | iii_pooledcentre | RETUNED | PD_inpath | flagged cell set | - | - | lost []; new ['car|lat|turning', 'car|long|new']; lost family []; new family ['car|long|new'] |
| t1 | iii_pooledcentre | - | - | V_t / H1 | [['B3'], True] | [['B3'], False] | Form B UB {'B3': -0.7602} |
| t3 | i_x3 | B1 | PD7_primary | NoFlag | True | False |  |
| t3 | i_x3 | B1 | PD7_primary | flagged cell set | - | - | lost []; new ['car|long|new']; lost family []; new family [] |
| t3 | i_x3 | B4 | PD7_primary | flagged cell set | - | - | lost []; new []; lost family []; new family ['large|long|static'] |
| t3 | ii_x3 | B1 | PD7_primary | NoFlag | True | False |  |
| t3 | ii_x3 | B1 | PD7_primary | flagged cell set | - | - | lost []; new ['car|long|new', 'large|long|new', 'large|long|straight']; lost family []; new family ['large|long|straight'] |
| t3 | ii_x3 | B4 | PD7_primary | flagged cell set | - | - | lost []; new ['large|long|static']; lost family []; new family ['large|long|static'] |
| t3 | ii_x3 | B4 | SD1_7_gap_le_5m | flagged cell set | - | - | lost []; new ['car|long|turning']; lost family []; new family [] |
| t3 | ii_x3 | B4 | PD_inpath | flagged cell set | - | - | lost []; new ['large|long|straight']; lost family []; new family [] |
| t3 | ii_x3 | B6 | PD7_primary | flagged cell set | - | - | lost []; new ['large|long|new']; lost family []; new family [] |
| t3 | ii_x3 | B6 | SD1_7_gap_le_5m | NoFlag | True | False |  |
| t3 | ii_x3 | B6 | SD1_7_gap_le_5m | FamFlag | False | True |  |
| t3 | ii_x3 | B6 | SD1_7_gap_le_5m | flagged cell set | - | - | lost []; new ['car|long|new']; lost family []; new family ['car|lat|turning'] |
| t3 | ii_x3 | B6 | PD_inpath | NoFlag | True | False |  |
| t3 | ii_x3 | B6 | PD_inpath | flagged cell set | - | - | lost []; new ['car|lat|turning']; lost family []; new family [] |
| t3 | ii_x3 | B9 | PD7_primary | flagged cell set | - | - | lost []; new ['large|long|new']; lost family []; new family [] |
| t3 | ii_x3 | RETUNED | PD7_primary | flagged cell set | - | - | lost []; new ['car|long|straight', 'large|long|new', 'large|long|straight']; lost family []; new family ['large|long|straight'] |
| t3 | ii_x3 | RETUNED | SD1_7_gap_le_5m | NoFlag | True | False |  |
| t3 | ii_x3 | RETUNED | SD1_7_gap_le_5m | flagged cell set | - | - | lost []; new ['car|long|new']; lost family []; new family [] |
| t3 | ii_rec | B1 | PD7_primary | NoFlag | True | False |  |
| t3 | ii_rec | B1 | PD7_primary | flagged cell set | - | - | lost []; new ['car|long|new', 'large|long|new', 'large|long|straight']; lost family []; new family ['large|long|straight'] |
| t3 | ii_rec | B4 | PD7_primary | flagged cell set | - | - | lost []; new ['large|long|static']; lost family []; new family ['large|long|static'] |
| t3 | ii_rec | B4 | SD1_7_gap_le_5m | flagged cell set | - | - | lost []; new ['car|long|turning']; lost family []; new family [] |
| t3 | ii_rec | B4 | PD_inpath | flagged cell set | - | - | lost []; new ['large|long|straight']; lost family []; new family [] |
| t3 | ii_rec | B6 | PD7_primary | flagged cell set | - | - | lost []; new ['large|long|new']; lost family []; new family [] |
| t3 | ii_rec | B6 | SD1_7_gap_le_5m | NoFlag | True | False |  |
| t3 | ii_rec | B6 | SD1_7_gap_le_5m | FamFlag | False | True |  |
| t3 | ii_rec | B6 | SD1_7_gap_le_5m | flagged cell set | - | - | lost []; new ['car|lat|turning', 'car|long|new']; lost family []; new family ['car|lat|turning'] |
| t3 | ii_rec | B6 | PD_inpath | NoFlag | True | False |  |
| t3 | ii_rec | B6 | PD_inpath | flagged cell set | - | - | lost []; new ['car|lat|turning']; lost family []; new family [] |
| t3 | ii_rec | B9 | PD7_primary | flagged cell set | - | - | lost []; new ['large|long|new']; lost family []; new family [] |
| t3 | ii_rec | RETUNED | PD7_primary | flagged cell set | - | - | lost []; new ['car|long|straight', 'large|long|new', 'large|long|straight']; lost family []; new family ['large|long|straight'] |
| t3 | ii_rec | RETUNED | SD1_7_gap_le_5m | NoFlag | True | False |  |
| t3 | ii_rec | RETUNED | SD1_7_gap_le_5m | flagged cell set | - | - | lost []; new ['car|long|new']; lost family []; new family [] |
| t3 | iii | Mstar | - | valid | True | False |  |
| t3 | iii | Mstar | - | shown_above | False | True |  |
| t3 | iii | Mstar | - | shown_above_9_conditions | False | True |  |
| t3 | iii | Mstar | PD_inpath | NoFlag | True | False |  |
| t3 | iii | Mstar | PD_inpath | flagged cell set | - | - | lost []; new ['car|lat|straight']; lost family []; new family [] |
| t3 | iii | B1 | PD7_primary | NoFlag | True | False |  |
| t3 | iii | B1 | PD7_primary | flagged cell set | - | - | lost []; new ['car|long|new', 'large|long|new', 'large|long|straight', 'large|long|turning']; lost family []; new family ['large|long|straight'] |
| t3 | iii | B4 | PD7_primary | flagged cell set | - | - | lost []; new ['large|long|static', 'two_wheeler|long|new', 'two_wheeler|long|straight']; lost family []; new family ['large|long|static'] |
| t3 | iii | B4 | SD1_7_gap_le_5m | flagged cell set | - | - | lost []; new ['car|long|turning']; lost family []; new family [] |
| t3 | iii | B4 | PD_inpath | flagged cell set | - | - | lost []; new ['large|long|straight']; lost family []; new family [] |
| t3 | iii | B6 | PD7_primary | flagged cell set | - | - | lost []; new ['large|long|new', 'pedestrian|lat|static', 'pedestrian|long|static']; lost family []; new family ['pedestrian|lat|static', 'pedestrian|long|static'] |
| t3 | iii | B6 | SD1_7_gap_le_5m | NoFlag | True | False |  |
| t3 | iii | B6 | SD1_7_gap_le_5m | FamFlag | False | True |  |
| t3 | iii | B6 | SD1_7_gap_le_5m | flagged cell set | - | - | lost []; new ['car|lat|turning', 'car|long|new']; lost family []; new family ['car|lat|turning'] |
| t3 | iii | B6 | PD_inpath | NoFlag | True | False |  |
| t3 | iii | B6 | PD_inpath | FamFlag | False | True |  |
| t3 | iii | B6 | PD_inpath | flagged cell set | - | - | lost []; new ['car|lat|turning', 'car|long|new']; lost family []; new family ['car|long|new'] |
| t3 | iii | B9 | PD7_primary | flagged cell set | - | - | lost []; new ['large|long|new']; lost family []; new family [] |
| t3 | iii | RETUNED | PD7_primary | flagged cell set | - | - | lost []; new ['car|long|straight', 'large|long|new', 'large|long|straight', 'large|long|turning']; lost family []; new family ['large|long|straight'] |
| t3 | iii | RETUNED | SD1_7_gap_le_5m | NoFlag | True | False |  |
| t3 | iii | RETUNED | SD1_7_gap_le_5m | flagged cell set | - | - | lost []; new ['car|long|new', 'large|long|straight']; lost family []; new family [] |
| t3 | iii | RETUNED | PD_inpath | FamFlag | False | True |  |
| t3 | iii | RETUNED | PD_inpath | flagged cell set | - | - | lost []; new []; lost family []; new family ['car|long|new'] |
| t3 | iii | - | - | V_t / H1 | [['B0', 'B3'], True] | [['B0', 'B3'], False] | Form B UB {'B0': -0.5819, 'B3': -0.6664} |
| t3 | iii_pooledcentre | Mstar | - | valid | True | False |  |
| t3 | iii_pooledcentre | Mstar | - | shown_above | False | True |  |
| t3 | iii_pooledcentre | Mstar | - | shown_above_9_conditions | False | True |  |
| t3 | iii_pooledcentre | Mstar | PD7_primary | NoFlag | True | False |  |
| t3 | iii_pooledcentre | Mstar | PD7_primary | FamFlag | False | True |  |
| t3 | iii_pooledcentre | Mstar | PD7_primary | flagged cell set | - | - | lost []; new ['car|long|new', 'pedestrian|lat|turning']; lost family []; new family ['car|long|new', 'pedestrian|lat|turning'] |
| t3 | iii_pooledcentre | Mstar | PD_inpath | NoFlag | True | False |  |
| t3 | iii_pooledcentre | Mstar | PD_inpath | flagged cell set | - | - | lost []; new ['car|lat|straight']; lost family []; new family [] |
| t3 | iii_pooledcentre | B1 | PD7_primary | NoFlag | True | False |  |
| t3 | iii_pooledcentre | B1 | PD7_primary | flagged cell set | - | - | lost []; new ['car|long|new', 'large|long|new', 'large|long|straight', 'large|long|turning']; lost family []; new family ['large|long|straight'] |
| t3 | iii_pooledcentre | B1 | PD_inpath | NoFlag | True | False |  |
| t3 | iii_pooledcentre | B1 | PD_inpath | flagged cell set | - | - | lost []; new ['large|long|straight']; lost family []; new family [] |
| t3 | iii_pooledcentre | B4 | PD7_primary | flagged cell set | - | - | lost []; new ['large|long|static', 'pedestrian|long|static', 'two_wheeler|long|new', 'two_wheeler|long|straight']; lost family []; new family ['large|long|static', 'pedestrian|long|static'] |
| t3 | iii_pooledcentre | B4 | SD1_7_gap_le_5m | flagged cell set | - | - | lost []; new ['car|long|turning', 'large|long|static']; lost family []; new family [] |
| t3 | iii_pooledcentre | B4 | PD_inpath | flagged cell set | - | - | lost []; new ['large|long|straight']; lost family []; new family [] |
| t3 | iii_pooledcentre | B6 | PD7_primary | flagged cell set | - | - | lost []; new ['large|long|new', 'pedestrian|lat|new', 'pedestrian|lat|static', 'pedestrian|long|static']; lost family []; new family ['pedestrian|lat|new', 'pedestrian|lat|static', 'pedestrian|long|static'] |
| t3 | iii_pooledcentre | B6 | SD1_7_gap_le_5m | NoFlag | True | False |  |
| t3 | iii_pooledcentre | B6 | SD1_7_gap_le_5m | FamFlag | False | True |  |
| t3 | iii_pooledcentre | B6 | SD1_7_gap_le_5m | flagged cell set | - | - | lost []; new ['car|lat|turning', 'car|long|new']; lost family []; new family ['car|lat|turning'] |
| t3 | iii_pooledcentre | B6 | PD_inpath | NoFlag | True | False |  |
| t3 | iii_pooledcentre | B6 | PD_inpath | FamFlag | False | True |  |
| t3 | iii_pooledcentre | B6 | PD_inpath | flagged cell set | - | - | lost []; new ['car|lat|turning', 'car|long|new']; lost family []; new family ['car|long|new'] |
| t3 | iii_pooledcentre | B9 | PD7_primary | flagged cell set | - | - | lost []; new ['large|long|new']; lost family []; new family [] |
| t3 | iii_pooledcentre | B9 | PD_inpath | FamFlag | False | True |  |
| t3 | iii_pooledcentre | B9 | PD_inpath | flagged cell set | - | - | lost []; new []; lost family []; new family ['car|long|new'] |
| t3 | iii_pooledcentre | RETUNED | PD7_primary | flagged cell set | - | - | lost []; new ['car|long|straight', 'large|long|new', 'large|long|straight', 'large|long|turning']; lost family []; new family ['large|long|straight'] |
| t3 | iii_pooledcentre | RETUNED | SD1_7_gap_le_5m | NoFlag | True | False |  |
| t3 | iii_pooledcentre | RETUNED | SD1_7_gap_le_5m | flagged cell set | - | - | lost []; new ['car|long|new']; lost family []; new family [] |
| t3 | iii_pooledcentre | RETUNED | PD_inpath | NoFlag | True | False |  |
| t3 | iii_pooledcentre | RETUNED | PD_inpath | FamFlag | False | True |  |
| t3 | iii_pooledcentre | RETUNED | PD_inpath | flagged cell set | - | - | lost []; new ['car|long|new', 'large|long|straight']; lost family []; new family ['car|long|new'] |
| t3 | iii_pooledcentre | - | - | V_t / H1 | [['B0', 'B3'], True] | [['B0', 'B3'], False] | Form B UB {'B0': -0.5819, 'B3': -0.6664} |

## Choices where the plan is silent

- (i) is computed exactly as the code of record (sup-t on the bootstrap SE, k6_analyse_v02.flag via R21's re-derivation); 'percentile' in the plan is read as 'the record's bootstrap bound'. For one cell it equals the basic bootstrap bound 2E - Q_{1-L}(E*); the pure percentile UB of HK1c is also reported.
- (ii) the estimator is the record's (mean over logs with records of the per-log rate; in the bootstrap a ratio of two log totals), so its cluster delta-method SE is the ratio's: U/(U-1) sum_u 1[N_u>0](p_u - R)^2 / m^2 over all U = 375 logs.
- (ii) the floor sqrt(delta(1-delta)/N_eff) uses N_eff = N/deff of (iii) (records N, deff from the ANOVA ICC), recomputed on each replicate with the replicate's multiplicities, so the pivot uses the same SE formula in sample and replicate.
- (ii) simultaneity: sup-t over the same cell sets as the record (all evaluable cells; the power family; the pooled cell alone).
- (ii) primary on X3's weights [20261201, i, 3], B = 4000 (plan section 0); also on the record's weights (B = 40000), because the removal level 0.998611 leaves only about 5.6 replicates beyond the quantile at B = 4000.
- (iii) ANOVA ICC for unbalanced clusters (MSB, MSW, n0) over the logs with records in the cell, truncated to [0, 1]; m_bar = N / (logs with records); centre = the record's estimate; the variant centred on x/n is reported as iii_pooledcentre.
- (iii) one-sided Wilson bound with z = Phi^-1(1 - (1 - L)/J), J = the number of cells in the record's sup-t set (Bonferroni); J = 1 for the pooled cell (pooled LB at the arm's level, HK1c UB at 0.995).
- Status rules are the code of record's (c1_analyse_v02.arm_status): a comparator is 'shown above' on a cell, family or pooled flag or an HK1c failure; the 9-condition reading of plan 6.2 (no HK1c term) is reported alongside.
- Families (power rule) and evaluable sets are fixed at the record's; the power rule is not an interval and is not recomputed.
- Where V_t changes, Form B is recomputed with the record's paired percentile bootstrap on the record's weights (B = 40000) at 1 - 0.0125/|V_t|.

Code: `50_CODE/x3/x3_stats_c1_v01.py`, `x3_stats_common_v01.py` (sha256 in the JSON). Nothing here changes the verdict of record, a claim status or a table of record.
