#!/bin/sh

# ==============================
# USAGE
# ==============================
# ./compare.sh <results_dir>
# ==============================

RESULTS_DIR="$1"

if [ -z "$RESULTS_DIR" ]; then
    echo "Usage: ./compare.sh <results_dir>"
    exit 1
fi

PY_TMP="$RESULTS_DIR/tmp_runs_python.jsonl"
JAC_TMP="$RESULTS_DIR/tmp_runs_jac.jsonl"
PY_OVERALL="$RESULTS_DIR/overall_python.json"
JAC_OVERALL="$RESULTS_DIR/overall_jac.json"
FINAL="$RESULTS_DIR/overall_comparison.json"

if [ ! -f "$PY_TMP" ] || [ ! -f "$JAC_TMP" ]; then
    echo "[ERROR] Missing tmp jsonl files inside $RESULTS_DIR"
    exit 1
fi

echo "Comparing runs from folder: $RESULTS_DIR"


# ============================================================
# PYTHON AGGREGATE
# ============================================================
python3 << EOF
import json
import numpy as np

path = "$PY_TMP"
out = "$PY_OVERALL"

runs = []
for line in open(path):
    line = line.strip()
    if not line:
        continue
    try:
        runs.append(json.loads(line))
    except:
        continue

def mean(xs):
    return float(np.mean(xs)) if xs else None

valid = [r for r in runs if r.get("error") is None]
errors = [r for r in runs if r.get("error") is not None]

out_data = {
    "pipeline": "python",
    "total_runs": len(runs),
    "valid_runs": len(valid),
    "error_runs": len(errors),
    "error_ratio": len(errors) / len(runs) if runs else None,
    "mean_ade": mean([r.get("ade") for r in valid]),
    "mean_fde": mean([r.get("fde") for r in valid]),
    "mean_l2": mean([r.get("l2") for r in valid]),
    "mean_inference_time": mean([r.get("inference_time") for r in runs]),
}

json.dump(out_data, open(out, "w"), indent=2)
print("Python aggregated →", out)
EOF


# ============================================================
# JAC AGGREGATE
# ============================================================
python3 << EOF
import json
import numpy as np

path = "$JAC_TMP"
out = "$JAC_OVERALL"

runs = []
for line in open(path):
    line = line.strip()
    if not line:
        continue
    try:
        runs.append(json.loads(line))
    except:
        continue

def mean(xs):
    return float(np.mean(xs)) if xs else None

valid = [r for r in runs if r.get("error") is None]
errors = [r for r in runs if r.get("error") is not None]

out_data = {
    "pipeline": "jac",
    "total_runs": len(runs),
    "valid_runs": len(valid),
    "error_runs": len(errors),
    "error_ratio": len(errors) / len(runs) if runs else None,
    "mean_ade": mean([r.get("ade") for r in valid]),
    "mean_fde": mean([r.get("fde") for r in valid]),
    "mean_l2": mean([r.get("l2") for r in valid]),
    "mean_inference_time": mean([r.get("inference_time") for r in runs]),
}

json.dump(out_data, open(out, "w"), indent=2)
print("Jac aggregated →", out)
EOF


# ============================================================
# FINAL COMPARISON
# ============================================================
python3 << EOF
import json

py = json.load(open("$PY_OVERALL"))
jc = json.load(open("$JAC_OVERALL"))

def pick(a, b):
    if a is None or b is None:
        return "unknown"
    return "python" if a < b else "jac"

final = {
    "python": py,
    "jac": jc,
    "comparison": {
        "ade_diff": py["mean_ade"] - jc["mean_ade"],
        "fde_diff": py["mean_fde"] - jc["mean_fde"],
        "l2_diff": py["mean_l2"] - jc["mean_l2"],
        "inference_time_diff": py["mean_inference_time"] - jc["mean_inference_time"],
        "error_ratio_diff": py["error_ratio"] - jc["error_ratio"],
    },
    "winner": {
        "ADE": pick(py["mean_ade"], jc["mean_ade"]),
        "FDE": pick(py["mean_fde"], jc["mean_fde"]),
        "L2": pick(py["mean_l2"], jc["mean_l2"]),
        "Inference Time": pick(py["mean_inference_time"], jc["mean_inference_time"]),
        "Error Rate": pick(py["error_ratio"], jc["error_ratio"]),
    }
}

json.dump(final, open("$FINAL", "w"), indent=2)
print("\nComparison written to $FINAL\n")
EOF
