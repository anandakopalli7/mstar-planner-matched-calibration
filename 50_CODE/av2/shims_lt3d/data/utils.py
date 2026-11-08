"""Stand-in for LT3D data/utils.py at commit e33189aa (Claude line, 2 Nov 2026): the two functions tracking/ab3dmot.py imports,
copied verbatim from LT3D data/utils.py (lines 123-152); nothing else (the original imports mmdet3d for AV2_CLASS_NAMES)."""
from collections import defaultdict
from typing import Dict, List, Union

import numpy as np


def index_array_values(array_dict: Dict, index: Union[int, np.ndarray]) -> Dict:
    return {
        k: v[index] if isinstance(v, np.ndarray) else v for k, v in array_dict.items()
    }


def concatenate_array_values(array_dicts: List[Dict]) -> Dict[str, np.ndarray]:
    """
    Concatenates numpy arrays in list of dictionaries
    Handles inconsistent keys (will skip missing keys)
    Does not concatenate non-numpy values (int, str), sets to value if all values are equal
    """
    combined = defaultdict(list)
    for array_dict in array_dicts:
        for k, v in array_dict.items():
            combined[k].append(v)
    concatenated = {}
    for k, vs in combined.items():
        if all(isinstance(v, np.ndarray) for v in vs):
            if any(v.size > 0 for v in vs):
                concatenated[k] = np.concatenate([v for v in vs if v.size > 0])
            else:
                concatenated[k] = vs[0]
        elif all(vs[0] == v for v in vs):
            concatenated[k] = vs[0]
    return concatenated
