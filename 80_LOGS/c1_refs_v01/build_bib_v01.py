#!/usr/bin/env python3
"""build_bib_v01.py -- builds 20_DESIGN/refs_v06c.bib (refs editor, 7 Nov 2026).

Inputs (read-only):
  - the cited keys, from extract_keys_v01.py (same folder);
  - cache_v01.json (same folder): the Crossref /works records and arXiv API records fetched on
    7 Nov 2026 for every cited key that has a DOI or an arXiv id;
  - the hand-verified entries below (MANUAL) for works without a Crossref record
    (PMLR, NeurIPS, ICLR, JMLR, IFAC 2002, workshop, arXiv-only), and per-key OVERRIDES.
Output: <W>/20_DESIGN/refs_v06c.bib. Refuses to overwrite an existing file.

Usage: python -I build_bib_v01.py [WORKSPACE_ROOT] [--out PATH]
"""
import json
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import extract_keys_v01 as ex  # noqa: E402

VDATE = "7 Nov 2026"

# ----------------------------------------------------------------- LaTeX helpers
ACC = {'\u0301': "'", '\u0300': '`', '\u0308': '"', '\u0302': '^', '\u0303': '~', '\u0304': '=',
       '\u0307': '.', '\u030c': 'v', '\u0306': 'u', '\u0327': 'c', '\u030a': 'r', '\u030b': 'H', '\u0328': 'k'}
SPECIAL = {'ø': '{\\o}', 'Ø': '{\\O}', 'ß': '{\\ss}', 'æ': '{\\ae}', 'Æ': '{\\AE}', 'ł': '{\\l}', 'Ł': '{\\L}',
           'đ': '{\\dj}', 'ı': '{\\i}', '\u2010': '-', '\u2011': '-', '\u2013': '--', '\u2014': '---',
           '\u2019': "'", '\u2018': '`', '\u201c': '``', '\u201d': "''", '\u00a0': ' ', '&': '\\&', '%': '\\%',
           '\u2009': ' ', '\u00ae': '', '\u2122': ''}


def tex(s):
    out = []
    for ch in s:
        if ch in SPECIAL:
            out.append(SPECIAL[ch]); continue
        if ord(ch) < 128:
            out.append(ch); continue
        d = unicodedata.normalize('NFD', ch)
        if len(d) == 2 and d[1] in ACC:
            base = '\\i' if d[0] == 'i' else d[0]
            out.append('{\\%s{%s}}' % (ACC[d[1]], base) if (ACC[d[1]].isalpha() or base == '\\i') else '{\\%s%s}' % (ACC[d[1]], base))
        else:
            raise ValueError('no LaTeX mapping for %r in %r' % (ch, s))
    return ''.join(out)


def fix_combining(s):
    # Crossref sometimes stores "s" + combining breve for s-caron (e.g. Os\u0306ep); normalise to caron
    s = s.replace('s\u0306', 's\u030c').replace('S\u0306', 'S\u030c')
    return unicodedata.normalize('NFC', s)


PROPER = ['Kalman', 'Gaussian', 'Markovian', 'Bayesian', 'Mondrian', 'Wishart', 'Chi-Squared', 'Argoverse']


def brace_title(t):
    t = re.sub(r'<[^>]+>', '', t)
    t = ' '.join(t.split())

    def seg(m):
        w = m.group(0)
        parts = w.split('-')
        new = []
        for p in parts:
            core = p
            if (len(core) > 1 and any(c.isupper() for c in core[1:])) or core in PROPER or core.rstrip('s') in PROPER:
                new.append('{' + core + '}')
            else:
                new.append(core)
        return '-'.join(new)
    t = re.sub(r'[A-Za-z0-9+\u00c0-\u024f]+(?:-[A-Za-z0-9+\u00c0-\u024f]+)*', seg, t)
    return tex(t)


def person(given, family):
    given = fix_combining((given or '').strip())
    family = fix_combining((family or '').strip())
    # add a period after bare single-letter initials ("Douglas G Altman" -> "G.")
    given = re.sub(r'\b([A-Z])\b(?!\.)', r'\1.', given)
    given = re.sub(r'\.(?=[A-Z])', '. ', given)
    given = given.replace('\u2010', '-').replace('\u2013', '-')
    family = family.replace('\u2010', '-').replace('\u2013', '-')
    return tex(family) + (', ' + tex(given) if given else '')


# ----------------------------------------------------------------- per-key data
JOURNAL_FIX = {
    'Gneiting2007': 'Journal of the Royal Statistical Society: Series B (Statistical Methodology)',
    'Lei2014': 'Journal of the Royal Statistical Society: Series B (Statistical Methodology)',
}
AUTHOR_FIX = {  # full names as printed on the paper where Crossref abbreviates or mis-encodes
    'Sarkka2009': ['S{\\"{a}}rkk{\\"{a}}, Simo', 'Nummenmaa, Aapo'],
    'DuToit2011': ['Du Toit, Noel E.', 'Burdick, Joel W.'],
    'Mehra1970': ['Mehra, R. K.'],
    'BlomBarShalom1988': ['Blom, H. A. P.', 'Bar-Shalom, Y.'],
    'Yin2021': ['Yin, Tianwei', 'Zhou, Xingyi', 'Kr{\\"{a}}henb{\\"{u}}hl, Philipp'],
    'Bates2021': ['Bates, Stephen', 'Angelopoulos, Anastasios N.', 'Lei, Lihua', 'Malik, Jitendra', 'Jordan, Michael I.'],
    'LeeBarberWillett': ['Lee, Yonghoon', 'Barber, Rina Foygel', 'Willett, Rebecca'],
    'Barber2021': ['Barber, Rina Foygel', 'Cand{\\`{e}}s, Emmanuel J.', 'Ramdas, Aaditya', 'Tibshirani, Ryan J.'],
    'Barber2023': ['Barber, Rina Foygel', 'Cand{\\`{e}}s, Emmanuel J.', 'Ramdas, Aaditya', 'Tibshirani, Ryan J.'],
    'BianBarber2023': ['Bian, Michael', 'Barber, Rina Foygel'],
    'Ono2008': ['Ono, Masahiro', 'Williams, Brian C.'],
    'Ding2023': ['Ding, Tiffany', 'Angelopoulos, Anastasios N.', 'Bates, Stephen', 'Jordan, Michael I.', 'Tibshirani, Ryan J.'],
}
TITLE_FIX = {
    'KleinRoodman2005': 'Blind Analysis in Nuclear and Particle Physics',
    'BarShalom2001': 'Estimation with Applications to Tracking and Navigation: Theory, Algorithms and Software',
}
# DOIs are printed in the case used by the publisher's landing page (Crossref returns them lower-cased)

EPRINT = {  # arXiv versions of published papers (kept as eprint fields; not printed by IEEEtran.bst)
    'Angelopoulos2025LTT': '2110.01052', 'Bao2024': '2301.00584', 'Barber2023': '2202.13415', 'Bates2021': '2101.02703',
    'BianBarber2023': '2205.03647', 'Chen2018nees': '1807.08855', 'Djuric2020': '1808.05819', 'Ivanovic2022': '2110.03267',
    'IvanovicPavone2022': '2110.03270', 'Karnchanachari2024': '2403.04133', 'Li2024Ego': '2312.03031',
    'Lindemann2023': '2210.10254', 'McAllister2022': '2204.13319', 'Natraj2026': '2607.22409', 'PhanMinh2020': '1911.10298',
    'Philion2020': '2004.08745', 'Gibbs2023': '2305.12616', 'LeeBarberWillett': '2306.06342', 'Marques2024': '2409.08249',
    'Bao2025': '2507.04716', 'Lekeufack2024': '2310.05921', 'Mohamed2025': '2501.08520', 'Nair2025': '2310.20561',
    'Ren2025': '2401.03799', 'Forsling2025': '2406.00861', 'Ahmed2024': '2312.17420', 'Yan2026': '2509.03311',
    'Mustafa2023': '2302.10846', 'Ding2023': '2306.09335', 'Li2023': '2307.16675', 'Weng2020': '1907.03961',
    'Yin2021': '2006.11275', 'Caesar2020': '1903.11027', 'Salzmann2020': '2001.03093', 'Chen2023voxelnext': '2303.11301',
    'Luiten2021': '2009.07736', 'DSilva2026': '2603.07092', 'Vlahakis2024': '2411.19132', 'Feng2018': '1804.05132',
}
CODE = {  # dataset / software pointers (resolved HTTP 200 on 7 Nov 2026)
    'Caesar2020': 'Dataset: \\url{https://www.nuscenes.org/}',
    'Peri2022': 'Code (LT3D): \\url{https://github.com/neeharperi/LT3D}',
    'Li2023': 'Code: \\url{https://github.com/lixiaoyu2000/Poly-MOT}',
    'Weng2020': 'Code (AB3DMOT): \\url{https://github.com/xinshuoweng/AB3DMOT}',
    'Salzmann2020': 'Code: \\url{https://github.com/StanfordASL/Trajectron-plus-plus}',
    'Luiten2021': 'Code (TrackEval): \\url{https://github.com/JonathonLuiten/TrackEval}',
    'Yin2021': 'Code: \\url{https://github.com/tianweiy/CenterPoint}',
    'Chen2023voxelnext': 'Code: \\url{https://github.com/dvlab-research/VoxelNeXt}',
}
OVERRIDES = {
    'Bao2025': dict(note='Early access, published online 22 Sep. 2026', pages=None),
    'Shi2026': dict(note='Early access', pages=None),
    'LearnTrack2026': dict(pages=None, note='Art. no. 2514815'),
    'Lefevre2014': dict(pages=None, note='Art. no. 1'),
    'LeeBarberWillett': dict(note='Published online 19 Mar. 2026'),
    'Bates2021': dict(note='Art. no. 43'),
    'BarShalom2001': dict(year='2001', publisher='Wiley', address='New York, NY, USA', isbn='978-0-471-41655-5'),
    'Wellek2010': dict(edition='2nd', publisher='Chapman and Hall/CRC', address='Boca Raton, FL, USA', isbn='978-1-4398-0818-4'),
    'Salzmann2020': dict(volume='12363', address='Cham, Switzerland', publisher='Springer'),
    'Marques2024': dict(volume='38', address='Cham, Switzerland', publisher='Springer'),
    'Cleaveland2024': dict(_type='inproceedings', booktitle='Proc. AAAI Conference on Artificial Intelligence'),
    'Ding2023': dict(_type='inproceedings', booktitle='Advances in Neural Information Processing Systems', volume='36'),
}
SERIES_BOOK = {
    'Salzmann2020': ('Computer Vision -- {ECCV} 2020', 'Lecture Notes in Computer Science'),
    'Marques2024': ('Algorithmic Foundations of Robotics {XVI}, Volume 2', 'Springer Proceedings in Advanced Robotics'),
}

PMLR = 'Proceedings of Machine Learning Research'
NIPS = 'Advances in Neural Information Processing Systems'
MANUAL = {
    'Angelopoulos2024': ('inproceedings', [
        ('author', 'Angelopoulos, Anastasios N. and Bates, Stephen and Fisch, Adam and Lei, Lihua and Schuster, Tal'),
        ('title', 'Conformal Risk Control'), ('booktitle', 'Proc. International Conference on Learning Representations (ICLR)'),
        ('pages', '55198--55218'), ('year', '2024'),
        ('url', 'https://proceedings.iclr.cc/paper_files/paper/2024/hash/f3549ef9b5ff520a7e41ff3cc306ab2b-Abstract-Conference.html'),
        ('eprint', '2208.02814'), ('archivePrefix', 'arXiv'), ('primaryClass', 'stat.ME')],
        'ICLR 2024 proceedings page (citation meta: authors, pp. 55198-55218); arXiv 2208.02814v4'),
    'Argoverse2': ('inproceedings', [
        ('author', 'Wilson, Benjamin and Qi, William and Agarwal, Tanmay and Lambert, John and Singh, Jagjeet and Khandelwal, Siddhesh and Pan, Bowen and Kumar, Ratnesh and Hartnett, Andrew and Kaesemodel Pontes, Jhony and Ramanan, Deva and Carr, Peter and Hays, James'),
        ('title', '{Argoverse} 2: Next Generation Datasets for Self-Driving Perception and Forecasting'),
        ('booktitle', 'Proc. Neural Information Processing Systems Track on Datasets and Benchmarks'), ('volume', '1'), ('year', '2021'),
        ('url', 'https://datasets-benchmarks-proceedings.neurips.cc/paper_files/paper/2021/hash/4734ba6f3de83d861c3176a6273cac6d-Abstract-round2.html'),
        ('eprint', '2301.00493'), ('archivePrefix', 'arXiv'), ('primaryClass', 'cs.CV'),
        ('note', 'Dataset: \\url{https://www.argoverse.org/av2.html}')],
        'NeurIPS Datasets and Benchmarks 2021 proceedings page (citation meta, 13 authors, vol. 1); arXiv 2301.00493v1; dataset URL HTTP 200'),
    'Bostrom2020': ('inproceedings', [
        ('author', 'Bostr{\\"{o}}m, Henrik and Johansson, Ulf'), ('title', '{Mondrian} conformal regressors'),
        ('booktitle', 'Proc. Conformal and Probabilistic Prediction and Applications (COPA)'), ('series', PMLR), ('volume', '128'),
        ('pages', '114--133'), ('year', '2020'), ('url', 'https://proceedings.mlr.press/v128/bostrom20a.html')],
        'PMLR v128 page (citation meta: pp. 114-133, 2020)'),
    'Dauner2023': ('inproceedings', [
        ('author', 'Dauner, Daniel and Hallgarten, Marcel and Geiger, Andreas and Chitta, Kashyap'),
        ('title', 'Parting with Misconceptions about Learning-based Vehicle Motion Planning'),
        ('booktitle', 'Proc. 7th Conference on Robot Learning (CoRL)'), ('series', PMLR), ('volume', '229'), ('pages', '1268--1281'),
        ('year', '2023'), ('url', 'https://proceedings.mlr.press/v229/dauner23a.html'),
        ('eprint', '2306.07962'), ('archivePrefix', 'arXiv'), ('primaryClass', 'cs.RO')],
        'PMLR v229 page (citation meta: pp. 1268-1281, 2023); arXiv 2306.07962v2'),
    'Dixit2023': ('inproceedings', [
        ('author', 'Dixit, Anushri and Lindemann, Lars and Wei, Skylar X. and Cleaveland, Matthew and Pappas, George J. and Burdick, Joel W.'),
        ('title', 'Adaptive Conformal Prediction for Motion Planning among Dynamic Agents'),
        ('booktitle', 'Proc. Learning for Dynamics and Control Conference (L4DC)'), ('series', PMLR), ('volume', '211'),
        ('pages', '300--314'), ('year', '2023'), ('url', 'https://proceedings.mlr.press/v211/dixit23a.html'),
        ('eprint', '2212.00278'), ('archivePrefix', 'arXiv'), ('primaryClass', 'cs.RO')],
        'PMLR v211 page (citation meta: pp. 300-314, 2023); arXiv 2212.00278v1'),
    'DixitMei2024': ('inproceedings', [
        ('author', 'Dixit, Anushri and Mei, Zhiting and Booker, Meghan and Storey-Matsutani, Mariko and Ren, Allen Z. and Majumdar, Anirudha'),
        ('title', 'Perceive With Confidence: Statistical Safety Assurances for Navigation with Learning-Based Perception'),
        ('booktitle', 'Proc. 8th Conference on Robot Learning (CoRL)'), ('series', PMLR), ('volume', '270'), ('pages', '2517--2541'),
        ('year', '2025'), ('url', 'https://proceedings.mlr.press/v270/dixit25a.html'),
        ('eprint', '2403.08185'), ('archivePrefix', 'arXiv'), ('primaryClass', 'cs.RO')],
        'PMLR v270 page (citation meta: 6 authors, pp. 2517-2541, published 12 Jan 2025); CoRL 2024'),
    'GibbsCandes2021': ('inproceedings', [
        ('author', 'Gibbs, Isaac and Cand{\\`{e}}s, Emmanuel'), ('title', 'Adaptive Conformal Inference Under Distribution Shift'),
        ('booktitle', NIPS), ('volume', '34'), ('pages', '1660--1672'), ('year', '2021'),
        ('url', 'https://proceedings.neurips.cc/paper_files/paper/2021/hash/0d441de75945e5acbc865406fc9a2559-Abstract.html'),
        ('eprint', '2106.00170'), ('archivePrefix', 'arXiv'), ('primaryClass', 'stat.ME')],
        'NeurIPS 2021 proceedings page (citation meta: vol. 34, pp. 1660-1672); arXiv 2106.00170v3'),
    'Holm1979': ('article', [
        ('author', 'Holm, Sture'), ('title', 'A Simple Sequentially Rejective Multiple Test Procedure'),
        ('journal', 'Scandinavian Journal of Statistics'), ('volume', '6'), ('number', '2'), ('pages', '65--70'), ('year', '1979'),
        ('url', 'https://www.jstor.org/stable/4615733')],
        'OpenAlex W2121044470 (vol. 6, pp. 65-70, 1979); issue 2 from REF_CHECK_v03b; JSTOR page behind a bot challenge (not bypassed); DOI 10.2307/4615733 does not resolve, so no doi field'),
    'JinCandes2023': ('article', [
        ('author', 'Jin, Ying and Cand{\\`{e}}s, Emmanuel J.'), ('title', 'Selection by Prediction with Conformal p-values'),
        ('journal', 'Journal of Machine Learning Research'), ('volume', '24'), ('number', '244'), ('pages', '1--41'), ('year', '2023'),
        ('url', 'https://jmlr.org/papers/v24/22-1176.html'), ('eprint', '2210.01408'), ('archivePrefix', 'arXiv'), ('primaryClass', 'stat.ME')],
        'JMLR page (citation meta: 24(244):1-41, 2023); arXiv 2210.01408v3'),
    'Kiyani2025': ('inproceedings', [
        ('author', 'Kiyani, Shayan and Hassani, Hamed and Pappas, George and Roth, Aaron'),
        ('title', 'Robust Decision-Making with Partially Calibrated Forecasters'),
        ('booktitle', 'Proc. International Conference on Learning Representations (ICLR)'), ('pages', '113667--113686'), ('year', '2026'),
        ('url', 'https://proceedings.iclr.cc/paper_files/paper/2026/hash/b8b6df58745740e54f00d84534bd182d-Abstract-Conference.html'),
        ('eprint', '2510.23471'), ('archivePrefix', 'arXiv'), ('primaryClass', 'stat.ML')],
        'ICLR 2026 proceedings page (citation meta: 4 authors, pp. 113667-113686, 20 Apr 2026); OpenReview mHRuCmc9lo; arXiv 2510.23471v1 (2025, title "Robust Decision Making with Partially Calibrated Forecasts")'),
    'Li2002': ('inproceedings', [
        ('author', 'Li, X. Rong and Zhao, Zhanlue and Jilkov, Vesselin P.'), ('title', "Estimator's Credibility and Its Measures"),
        ('booktitle', 'Proc. 15th IFAC World Congress'), ('address', 'Barcelona, Spain'), ('month', 'jul'), ('year', '2002'),
        ('url', 'https://skoge.folk.ntnu.no/prost/proceedings/ifac2002/data/content/02779/abstract.htm')],
        'IFAC 2002 proceedings abstract page (NTNU-hosted, paper 02779, session T-Fr-M01: title, 3 authors, Barcelona 21-26 Jul 2002); no DOI found on Crossref (IFAC 2002 prefix 10.3182 searched)'),
    'Noarov2025': ('inproceedings', [
        ('author', 'Noarov, Georgy and Ramalingam, Ramya and Roth, Aaron and Xie, Stephan'),
        ('title', 'High-Dimensional Prediction for Sequential Decision Making'),
        ('booktitle', 'Proc. International Conference on Machine Learning (ICML)'), ('series', PMLR), ('volume', '267'),
        ('pages', '46762--46783'), ('year', '2025'), ('url', 'https://proceedings.mlr.press/v267/noarov25b.html'),
        ('eprint', '2310.17651'), ('archivePrefix', 'arXiv'), ('primaryClass', 'cs.LG')],
        'PMLR v267 page (citation meta: pp. 46762-46783, 2025); arXiv 2310.17651v2'),
    'Peri2022': ('inproceedings', [
        ('author', 'Peri, Neehar and Dave, Achal and Ramanan, Deva and Kong, Shu'), ('title', 'Towards Long-Tailed {3D} Detection'),
        ('booktitle', 'Proc. 6th Conference on Robot Learning (CoRL)'), ('series', PMLR), ('volume', '205'), ('pages', '1904--1915'),
        ('year', '2023'), ('url', 'https://proceedings.mlr.press/v205/peri23a.html'),
        ('eprint', '2211.08691'), ('archivePrefix', 'arXiv'), ('primaryClass', 'cs.CV'),
        ('note', 'Code (LT3D): \\url{https://github.com/neeharperi/LT3D}')],
        'PMLR v205 page (citation meta: pp. 1904-1915, published 6 Mar 2023); CoRL 2022; arXiv 2211.08691v2; code URL HTTP 200'),
    'Sahoo2021': ('inproceedings', [
        ('author', 'Sahoo, Roshni and Zhao, Shengjia and Chen, Alyssa and Ermon, Stefano'), ('title', 'Reliable Decisions with Threshold Calibration'),
        ('booktitle', NIPS), ('volume', '34'), ('pages', '1831--1844'), ('year', '2021'),
        ('url', 'https://proceedings.neurips.cc/paper/2021/hash/0e65972dce68dad4d52d063967f0a705-Abstract.html')],
        'NeurIPS 2021 proceedings page (citation meta: vol. 34, pp. 1831-1844)'),
    'Tang2026': ('inproceedings', [
        ('author', 'Tang, Jingwu and Wu, Jiayun and Wu, Zhiwei Steven and Zhang, Jiahao'),
        ('title', 'Dimension-Free Decision Calibration for Nonlinear Loss Functions'),
        ('booktitle', 'Proc. International Conference on Learning Representations (ICLR)'), ('pages', '86293--86321'), ('year', '2026'),
        ('url', 'https://proceedings.iclr.cc/paper_files/paper/2026/hash/8ad060589ed7e18aea4ee1cc8a486c89-Abstract-Conference.html'),
        ('eprint', '2504.15615'), ('archivePrefix', 'arXiv'), ('primaryClass', 'cs.LG')],
        'ICLR 2026 proceedings page (citation meta: pp. 86293-86321; lists "Steven Wu"); arXiv 2504.15615v1 gives "Zhiwei Steven Wu"'),
    'Tibshirani2019': ('inproceedings', [
        ('author', 'Tibshirani, Ryan J. and Barber, Rina Foygel and Cand{\\`{e}}s, Emmanuel and Ramdas, Aaditya'),
        ('title', 'Conformal Prediction Under Covariate Shift'), ('booktitle', NIPS), ('volume', '32'), ('year', '2019'),
        ('url', 'https://proceedings.neurips.cc/paper_files/paper/2019/hash/8fb21ee7a2207526da55a679f0332de2-Abstract.html'),
        ('eprint', '1904.06019'), ('archivePrefix', 'arXiv'), ('primaryClass', 'stat.ME')],
        'NeurIPS 2019 proceedings page (citation meta: vol. 32, no page range given); arXiv 1904.06019v3'),
    'Vovk2012': ('inproceedings', [
        ('author', 'Vovk, Vladimir'), ('title', 'Conditional Validity of Inductive Conformal Predictors'),
        ('booktitle', 'Proc. Asian Conference on Machine Learning (ACML)'), ('series', PMLR), ('volume', '25'), ('pages', '475--490'),
        ('year', '2012'), ('url', 'https://proceedings.mlr.press/v25/vovk12.html'),
        ('eprint', '1209.2673'), ('archivePrefix', 'arXiv'), ('primaryClass', 'cs.LG')],
        'PMLR v25 page (citation meta: pp. 475-490, 2012); arXiv 1209.2673v2'),
    'Zhao2021': ('inproceedings', [
        ('author', 'Zhao, Shengjia and Kim, Michael P. and Sahoo, Roshni and Ma, Tengyu and Ermon, Stefano'),
        ('title', 'Calibrating Predictions to Decisions: A Novel Approach to Multi-Class Calibration'),
        ('booktitle', NIPS), ('volume', '34'), ('pages', '22313--22324'), ('year', '2021'),
        ('url', 'https://proceedings.neurips.cc/paper_files/paper/2021/hash/bbc92a647199b832ec90d7cf57074e9e-Abstract.html'),
        ('eprint', '2107.05719'), ('archivePrefix', 'arXiv'), ('primaryClass', 'stat.ML')],
        'NeurIPS 2021 proceedings page (citation meta: vol. 34, pp. 22313-22324); arXiv 2107.05719v1'),
    'Zhu2026': ('inproceedings', [
        ('author', 'Zhu, Zihan and Kiyani, Shayan and Pappas, George J. and Hassani, Hamed'),
        ('title', 'Conformal Risk-Averse Decision Making with Action Conditional Guarantee'),
        ('booktitle', 'Proc. International Conference on Machine Learning (ICML)'), ('series', PMLR), ('volume', '306'),
        ('pages', '167248--167276'), ('year', '2026'), ('url', 'https://proceedings.mlr.press/v306/zhu26z.html'),
        ('eprint', '2606.05551'), ('archivePrefix', 'arXiv'), ('primaryClass', 'stat.ML')],
        'PMLR v306 page (citation meta: pp. 167248-167276, 29 Sep 2026); arXiv 2606.05551v2'),
    'IvanovicA2024': ('inproceedings', [
        ('author', 'Ivanovic, Andrei and Itkina, Masha and McAllister, Rowan and Gilitschenski, Igor and Shkurti, Florian'),
        ('title', 'On the Importance of Uncertainty Calibration in Perception-Based Motion Planning'),
        ('booktitle', 'Long-Term Human Motion Prediction ({LHMP}) Workshop, IEEE International Conference on Robotics and Automation (ICRA)'),
        ('year', '2024'), ('url', 'https://motionpredictionicra2024.github.io/proceedings/lhmp2024_id06.pdf'),
        ('note', 'Workshop paper, ID 6')],
        'LHMP 2024 workshop page (paper 6, same 5 authors) and PDF (HTTP 200); no DOI, no arXiv version'),
}
ARXIV_ONLY = {  # key: (authors, title, id, version, version date, primary, extra note)
    'Angelopoulos2021': ('Angelopoulos, Anastasios N. and Bates, Stephen',
                         'A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification',
                         '2107.07511', 'v6', '7 Dec. 2022', 'cs.LG', ''),
    'Chen2026': ('Chen, Shuyi and Zhou, Wenbin and Zhu, Shixiang', 'Learning Polyhedral Conformal Sets for Robust Optimization',
                 '2605.08506', 'v3', '6 Sep. 2026', 'cs.LG', ''),
    'Chiu2020': ('Chiu, Hsu-kuang and Prioletti, Antonio and Li, Jie and Bohg, Jeannette',
                 'Probabilistic {3D} Multi-Object Tracking for Autonomous Driving', '2001.05673', 'v1', '16 Jan. 2020', 'cs.CV', ''),
    'Marques2026': ('Marques, Lu{\\\'{\\i}}s and Berenson, Dmitry', 'Local Conformal Calibration of Dynamics Uncertainty from Semantic Images',
                    '2605.13028', 'v3', '17 Aug. 2026', 'cs.RO', 'Accepted to the 17th World Symposium on the Algorithmic Foundations of Robotics (WAFR 2026)'),
    'Osterburg2026': ('Osterburg, Timo and Sch{\\"{u}}tte, Stefan and Bertram, Torsten',
                      '{CANMOT}: Class-Aware Noise Modeling for Multi-Object Tracking in Autonomous Driving',
                      '2606.03590', 'v2', '3 Oct. 2026', 'cs.RO',
                      'Accepted to IEEE/RSJ IROS 2026. Code: \\url{https://github.com/rst-tu-dortmund/CANMOT}'),
    'Pouria2026': ('Pouria, Fatemeh Cheraghi and Golchoubian, Mahsa and Driggs-Campbell, Katherine',
                   'Rethinking {Gaussian} Trajectory Predictors: Calibrated Uncertainty for Safe Planning',
                   '2603.10407', 'v2', '12 Jul. 2026', 'cs.RO', ''),
    'Shah2026': ('Shah, Jibran Iqbal and Ivanovic, Andrei and Zhu, Kelly and Itkina, Masha and McAllister, Rowan and Gilitschenski, Igor and Shkurti, Florian',
                 'The Impact of Class Uncertainty Propagation in Perception-Based Motion Planning',
                 '2602.16035', 'v1', '17 Feb. 2026', 'cs.RO', ''),
    'Weisman2026': ('Weisman, Olga and Shlezinger, Nir and Laufer-Goldshtein, Bracha',
                    'Conformalized {Kalman} Filters for State Estimation with Trustworthy Confidence Regions',
                    '2609.27506', 'v1', '23 Sep. 2026', 'eess.SP', ''),
    'Zhu2019cbgs': ('Zhu, Benjin and Jiang, Zhengkai and Zhou, Xiangxin and Li, Zeming and Yu, Gang',
                    'Class-Balanced Grouping and Sampling for Point Cloud {3D} Object Detection',
                    '1908.09492', 'v1', '26 Aug. 2019', 'cs.CV', 'Technical report'),
}


cache_doi_case = {}


def crossref_entry(key, m):
    o = OVERRIDES.get(key, {})
    t = m.get('type')
    typ = o.get('_type') or {'journal-article': 'article', 'proceedings-article': 'inproceedings', 'book-chapter': 'inproceedings',
                             'monograph': 'book', 'book': 'book'}[t]
    authors = AUTHOR_FIX.get(key) or [person(a.get('given'), a.get('family') or a.get('name')) for a in m.get('author', [])]
    title = TITLE_FIX.get(key) or m['title'][0]
    title = brace_title(title)
    fields = [('author', ' and '.join(authors)), ('title', title)]
    cont = (m.get('container-title') or [''])
    if typ == 'article':
        fields.append(('journal', tex(JOURNAL_FIX.get(key) or cont[0].replace('The Annals', 'The Annals'))))
    elif typ == 'inproceedings':
        if key in SERIES_BOOK:
            fields += [('booktitle', SERIES_BOOK[key][0]), ('series', SERIES_BOOK[key][1])]
        elif 'booktitle' in o:
            fields.append(('booktitle', o['booktitle']))
        else:
            name = re.sub(r'^(19|20)\d\d\s+', '', cont[0])
            fields.append(('booktitle', 'Proc. ' + tex(name)))
    vol = o.get('volume', m.get('volume'))
    if vol:
        fields.append(('volume', vol))
    if m.get('issue') and typ != 'book':
        fields.append(('number', m['issue']))
    pg = o['pages'] if 'pages' in o else m.get('page')
    if pg:
        a = pg.split('-')
        a = [x.lstrip('0') or '0' for x in a]
        pg = a[0] if len(a) == 1 or a[0] == a[1] else a[0] + '--' + a[1]
        fields.append(('pages', pg))
    for f in ('edition', 'publisher', 'address', 'isbn'):
        if o.get(f):
            fields.append((f, o[f]))
    if typ == 'inproceedings' and key in SERIES_BOOK:
        pass
    yr = o.get('year')
    if not yr:
        for f in ('published-print', 'issued'):
            try:
                yr = str(m[f]['date-parts'][0][0]); break
            except Exception:
                continue
    fields.append(('year', yr))
    fields.append(('doi', cache_doi_case.get(key, m['DOI'])))
    if key in EPRINT:
        fields += [('eprint', EPRINT[key]), ('archivePrefix', 'arXiv')]
    note = [o['note']] if o.get('note') else []
    if key in CODE:
        note.append(CODE[key])
    if note:
        fields.append(('note', '. '.join(note)))
    return typ, fields


def arxiv_entry(key):
    a, t, i, v, d, pc, extra = ARXIV_ONLY[key]
    note = 'arXiv:%s%s, %s' % (i, v, d) + ('. ' + extra if extra else '')
    year = '20' + i[:2]
    return 'misc', [('author', a), ('title', t), ('howpublished', 'arXiv:%s [%s]' % (i, pc)), ('year', year),
                    ('eprint', i), ('archivePrefix', 'arXiv'), ('primaryClass', pc), ('note', note),
                    ('url', 'https://arxiv.org/abs/%s%s' % (i, v))]


def fmt(key, typ, fields, comments):
    lines = ['% ' + c for c in comments]
    lines.append('@%s{%s,' % (typ, key))
    w = max(len(f) for f, _ in fields)
    for f, v in fields:
        lines.append('  %s = {%s},' % (f.ljust(w), v))
    lines[-1] = lines[-1].rstrip(',')
    lines.append('}')
    return '\n'.join(lines)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    w = args[0] if args else ex.DEFAULT_W
    out = os.path.join(w, '20_DESIGN', 'refs_v06c.bib')
    if '--out' in sys.argv:
        out = sys.argv[sys.argv.index('--out') + 1]
    if os.path.exists(out):
        sys.exit('refusing to overwrite ' + out)
    cache = json.load(open(os.path.join(HERE, 'cache_v01.json'), encoding='utf-8'))
    cache_doi_case.update(cache.get('doi_case', {}))
    status = json.load(open(os.path.join(HERE, 'status_v01.json'), encoding='utf-8'))
    d = os.path.join(w, '20_DESIGN')
    import glob
    paths = sorted(glob.glob(os.path.join(d, 'ms_v06_parts', '*_v04.md')))
    paths += [os.path.join(d, 'SUPPLEMENT_v06a.md'), os.path.join(d, 'SUPPLEMENT_v06b_add.md')]
    counts, _, _, _, _ = ex.scan(paths)
    keys = sorted(counts, key=lambda k: k.lower())
    chunks = []
    for k in keys:
        if k in MANUAL:
            typ, fields, ver = MANUAL[k][0], MANUAL[k][1], MANUAL[k][2]
        elif k in ARXIV_ONLY:
            typ, fields = arxiv_entry(k)
            r = cache['arxiv'][k]
            ver = 'arXiv API %s (%d authors, primary %s, first posted %s); %s' % (
                r['id'], len(r['authors']), r['primary'], r['published'][:10],
                cache.get('extra_ver', {}).get(k, 'Crossref title search found no published version'))
        else:
            m = cache['crossref'][k]
            typ, fields = crossref_entry(k, m)
            ver = 'Crossref %s' % m['DOI']
            if k in cache.get('extra_ver', {}):
                ver += '; ' + cache['extra_ver'][k]
        st = status.get(k, 'verified')
        chunks.append(fmt(k, typ, fields, ['verified: %s, %s' % (ver, VDATE), 'status: %s' % st]))
    head = ['% refs_v06c.bib -- references for manuscript v06c (IEEE Access), built 7 Nov 2026 by build_bib_v01.py.',
            '% One entry per key cited in 20_DESIGN/ms_v06_parts/*_v04.md and SUPPLEMENT_v06a.md / SUPPLEMENT_v06b_add.md',
            '%% (%d keys, extract_keys_v01.py). Keys are exactly as cited; see REFS_V06C_CHECK_v01.md for flags.' % len(keys),
            '% Remove the paywall dagger marks after keys (e.g. DuToit2011 + dagger) and locators ([Angelopoulos2024, Thm 1] -> \\cite[Thm.~1]{...})',
            '% when converting brackets to \\cite. Notes use \\url{}: load the url (or hyperref) package. eprint/archivePrefix/',
            '% primaryClass are ignored by IEEEtran.bst unless the style is extended; the doi field is printed only by newer IEEEtran.bst.', '']
    with open(out, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('\n'.join(head) + '\n' + '\n\n'.join(chunks) + '\n')
    print('wrote %s (%d entries)' % (out, len(chunks)))


if __name__ == '__main__':
    main()
