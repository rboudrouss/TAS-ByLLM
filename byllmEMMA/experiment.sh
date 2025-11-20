#!/bin/sh

# ==============================
# CONFIG
# ==============================
PYTHON_SCRIPT="predictHF.py"
# JAC script (optional 3rd arg, default: predictWithSem.jac)
JAC_SCRIPT="$3"

# Number of runs
N="$1"

if [ -z "$N" ]; then
    echo "Usage: ./run_all_experiments.sh <N> [results_dir]"
    exit 1
fi

if [ -z "$JAC_SCRIPT" ]; then
    echo "Usage: ./run_all_experiments.sh <N> [results_dir] [jac_script]"
    exit 1
fi

# ===============================================
# Custom results folder (default: results)
# ===============================================
RESULTS_DIR="${2:-results}"

# derived paths
PY_TMP="$RESULTS_DIR/tmp_runs_python.jsonl"
JAC_TMP="$RESULTS_DIR/tmp_runs_jac.jsonl"
PY_OVERALL="$RESULTS_DIR/overall_python.json"
JAC_OVERALL="$RESULTS_DIR/overall_jac.json"
FINAL="$RESULTS_DIR/overall_comparison.json"

mkdir -p "$RESULTS_DIR"
rm -f "$PY_TMP" "$JAC_TMP"

echo "======================================"
echo "Running PYTHON pipeline $N times"
echo "Result folder: $RESULTS_DIR"
echo "======================================"

i=1
while [ $i -le "$N" ]; do
    echo "Python run $i"
    python3 "$PYTHON_SCRIPT" >> "$PY_TMP"
    i=$((i+1))
done

echo "======================================"
echo "Running JAC pipeline $N times"
echo "======================================"

i=1
while [ $i -le "$N" ]; do
    echo "Jac run $i"
    jac "$JAC_SCRIPT" >> "$JAC_TMP"
    i=$((i+1))
done

# ============================================================
# PYTHON: Aggregate metrics
# ============================================================

python3 << EOF
import json
import numpy as np

path = "$PY_TMP"
out = "$PY_OVERALL"

runs = []
for line in open(path):
    line=line.strip()
    if not line:
        continue
    try:
        runs.append(json.loads(line))
    except:
        continue

valid = [r for r in runs if r.get("error") is None]
errors = [r for r in runs if r.get("error") is not None]

def mean(xs):
    return float(np.mean(xs)) if xs else None

out_data = {
    "pipeline": "python",
    "total_runs": len(runs),
    "valid_runs": len(valid),
    "error_runs": len(errors),
    "error_ratio": len(errors) / len(runs) if runs else None,
    "mean_ade": mean([r["ade"] for r in valid if "ade" in r]),
    "mean_fde": mean([r["fde"] for r in valid if "fde" in r]),
    "mean_l2": mean([r["l2"] for r in valid if "l2" in r]),
    "mean_inference_time": mean([r["inference_time"] for r in runs]),
}

json.dump(out_data, open(out, "w"), indent=2)
print("Python aggregated →", out)
EOF


# ============================================================
# JAC: Aggregate metrics
# ============================================================
python3 << EOF
import json
import numpy as np

path = "$JAC_TMP"
out = "$JAC_OVERALL"

runs = []
for line in open(path):
    line=line.strip()
    if not line:
        continue
    try:
        runs.append(json.loads(line))
    except:
        continue

valid = [r for r in runs if r.get("error") is None]
errors = [r for r in runs if r.get("error") is not None]

def mean(xs):
    return float(np.mean(xs)) if xs else None

out_data = {
    "pipeline": "jac",
    "total_runs": len(runs),
    "valid_runs": len(valid),
    "error_runs": len(errors),
    "error_ratio": len(errors) / len(runs) if runs else None,
    "mean_ade": mean([r["ade"] for r in valid if "ade" in r]),
    "mean_fde": mean([r["fde"] for r in valid if "fde" in r]),
    "mean_l2": mean([r["l2"] for r in valid if "l2" in r]),
    "mean_inference_time": mean([r["inference_time"] for r in runs]),
}

json.dump(out_data, open(out, "w"), indent=2)
print("Jac aggregated →", out)
EOF


# ============================================================
# FINAL MERGE + WINNER
# ============================================================
python3 << EOF
import json

py = json.load(open("$PY_OVERALL"))
jc = json.load(open("$JAC_OVERALL"))

def pick_winner(py_val, jc_val, lower_is_better=True):
    if py_val is None or jc_val is None:
        return "unknown"
    if lower_is_better:
        return "python" if py_val < jc_val else "jac"
    else:
        return "python" if py_val > jc_val else "jac"

comparison = {
    "ade_diff": (py["mean_ade"] - jc["mean_ade"]) if py["mean_ade"] and jc["mean_ade"] else None,
    "fde_diff": (py["mean_fde"] - jc["mean_fde"]) if py["mean_fde"] and jc["mean_fde"] else None,
    "l2_diff":  (py["mean_l2"] - jc["mean_l2"]) if py["mean_l2"] and jc["mean_l2"] else None,
    "inference_time_diff": py["mean_inference_time"] - jc["mean_inference_time"],
    "error_ratio_diff": py["error_ratio"] - jc["error_ratio"],
}

winners = {
    "ADE": {
        "python": py["mean_ade"],
        "jac": jc["mean_ade"],
        "winner": pick_winner(py["mean_ade"], jc["mean_ade"]),
    },
    "FDE": {
        "python": py["mean_fde"],
        "jac": jc["mean_fde"],
        "winner": pick_winner(py["mean_fde"], jc["mean_fde"]),
    },
    "L2": {
        "python": py["mean_l2"],
        "jac": jc["mean_l2"],
        "winner": pick_winner(py["mean_l2"], jc["mean_l2"]),
    },
    "Inference Time": {
        "python": py["mean_inference_time"],
        "jac": jc["mean_inference_time"],
        "winner": pick_winner(py["mean_inference_time"], jc["mean_inference_time"]),
    },
    "Error Rate": {
        "python": py["error_ratio"],
        "jac": jc["error_ratio"],
        "winner": pick_winner(py["error_ratio"], jc["error_ratio"]),
    }
}

final = {
    "python": py,
    "jac": jc,
    "comparison": comparison,
    "winner": winners,
}

json.dump(final, open("$FINAL", "w"), indent=2)

print("\n======================================")
print("Comparison written to $FINAL")
print("======================================\n")
EOF
