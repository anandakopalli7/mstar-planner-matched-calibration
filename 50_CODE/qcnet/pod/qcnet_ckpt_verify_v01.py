"""qcnet_ckpt_verify_v01 (QCNet arm, 2 Nov 2026): load the downloaded QCNet_AV2 checkpoint without running pickled code,
build QCNet from the checkpoint's own hyper-parameters and load the weights strictly.

Loading order: torch.load(weights_only=True); if torch refuses a global, a restricted unpickler that admits only tensor
rebuild functions, OrderedDict, NumPy scalars/dtypes and maps Lightning's AttributeDict to dict (any other global stops the
script). Writes a JSON record (hyper-parameters, parameter count, tensor count, load path used). No data is touched.
Usage: python -I qcnet_ckpt_verify_v01.py --qcnet <QCNet repo> --ckpt <file> --out <json>
"""
import argparse
import hashlib
import json
import pickle
import sys
import types


def restricted_pickle_module(blocked):
    allowed = {
        ("collections", "OrderedDict"), ("torch._utils", "_rebuild_tensor_v2"), ("torch._utils", "_rebuild_parameter"),
        ("torch._utils", "_rebuild_tensor"), ("torch", "Size"), ("torch", "device"),
        ("numpy.core.multiarray", "scalar"), ("numpy", "dtype"), ("numpy.core.multiarray", "_reconstruct"), ("numpy", "ndarray"),
        ("builtins", "set"), ("builtins", "frozenset"), ("builtins", "tuple"), ("builtins", "list"), ("builtins", "dict"),
    }

    class RUnpickler(pickle.Unpickler):
        def find_class(self, module, name):
            if (module, name) in allowed or (module == "torch" and name.endswith("Storage")) or (module == "torch" and name in ("float32", "float64", "int64", "bool", "uint8")):
                return super().find_class(module, name)
            if name == "AttributeDict":
                return dict
            blocked.append(module + "." + name)
            raise pickle.UnpicklingError("blocked global %s.%s" % (module, name))

    return types.SimpleNamespace(Unpickler=RUnpickler, load=pickle.load, loads=pickle.loads, __name__="restricted_pickle")


def load_ckpt(path):
    import torch
    try:
        return torch.load(path, map_location="cpu", weights_only=True), "weights_only"
    except Exception as e:  # noqa: BLE001
        print("weights_only load refused:", repr(e)[:300], flush=True)
    blocked = []
    try:
        return torch.load(path, map_location="cpu", pickle_module=restricted_pickle_module(blocked)), "restricted_unpickler"
    except Exception as e:  # noqa: BLE001
        raise SystemExit("restricted load failed: %r; blocked=%s" % (e, blocked))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--qcnet", required=True)
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    sys.path.insert(0, a.qcnet)
    import torch
    from predictors import QCNet  # QCNet repository code at the pinned commit
    ck, how = load_ckpt(a.ckpt)
    hp = dict(ck["hyper_parameters"])
    model = QCNet(**hp)
    res = model.load_state_dict(ck["state_dict"], strict=True)
    n_par = sum(p.numel() for p in model.parameters())
    sd_digest = hashlib.sha256()
    for k in sorted(ck["state_dict"]):
        sd_digest.update(k.encode())
        sd_digest.update(ck["state_dict"][k].detach().cpu().contiguous().numpy().tobytes())
    rec = {"load_path": how, "hyper_parameters": {k: (v if isinstance(v, (int, float, str, bool, type(None))) else str(v)) for k, v in hp.items()},
           "strict_load": str(res), "n_parameters": int(n_par), "n_state_tensors": len(ck["state_dict"]),
           "state_dict_sha256": sd_digest.hexdigest(), "checkpoint_keys": sorted(ck.keys()),
           "epoch": ck.get("epoch"), "global_step": ck.get("global_step"), "torch": torch.__version__}
    with open(a.out, "w") as f:
        json.dump(rec, f, indent=1)
    print(json.dumps({k: rec[k] for k in ("load_path", "strict_load", "n_parameters", "n_state_tensors", "epoch")}), flush=True)
    for k in ("dataset", "input_dim", "output_dim", "output_head", "num_historical_steps", "num_future_steps", "num_modes",
              "pl2pl_radius", "time_span", "pl2a_radius", "a2a_radius", "num_t2m_steps", "pl2m_radius", "a2m_radius"):
        print(k, hp.get(k), flush=True)
    print("QCNET CKPT VERIFIED", flush=True)


if __name__ == "__main__":
    main()
