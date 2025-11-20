import os
import json
import time
import re
import base64
from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
from PIL import Image as PILImage
import ollama

import utils


# ============================================================
# Setup output folders
# ============================================================

RESULTS_DIR = "results_jacWithSem"
JSON_DIR = os.path.join(RESULTS_DIR, "json")
VIZ_DIR = os.path.join(RESULTS_DIR, "viz")

os.makedirs(JSON_DIR, exist_ok=True)
os.makedirs(VIZ_DIR, exist_ok=True)


# ============================================================
# Data structures
# ============================================================

@dataclass
class Response:
    scene_description: str | None
    trajectory_predictions: List[Tuple[float, float]] | None
    parsing_error: str | None = None


@dataclass
class InputData:
    front_camera_path: str
    previous_frame_speed: List[float]
    previous_frame_curvature: List[float]

    @property
    def prompt(self) -> str:
        return utils.load_and_format_prompt("prompts/config_prompt.yaml","waypoint_prompt",
    prev_speed=self.previous_frame_speed,
    prev_curvatures=self.previous_frame_curvature)


# ============================================================
# Base64 helper
# ============================================================

def encode_image_to_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


# ============================================================
# Inference
# ============================================================

def predict_trajectory(input_data: InputData) -> Response:
    try:
        image_base64 = encode_image_to_base64(input_data.front_camera_path)

        messages = [
            {
                "role": "user",
                "content": input_data.prompt,
                "images": [image_base64]
            }
        ]

        completion = ollama.chat(
            model="qwen2.5vl",
            messages=messages,
            options={"temperature": 0.4, "num_predict": 400}
        )

        decoded = completion["message"]["content"].strip()

        # Extract list
        match = re.search(r"\[(.*?)\]", decoded, re.DOTALL)
        if not match:
            return Response(
                scene_description=None,
                trajectory_predictions=None,
                parsing_error="Missing waypoint list"
            )

        list_content = match.group(1)
        pairs = re.findall(r"\(([-0-9.]+)\s*,\s*([-0-9.]+)\)", list_content)

        if len(pairs) != 6:
            return Response(
                scene_description=None,
                trajectory_predictions=None,
                parsing_error=f"Expected 6 (v,c) pairs, got {len(pairs)}"
            )

        traj = [(float(v), float(c)) for v, c in pairs]
        description = decoded.split("[", 1)[0].strip()

        return Response(description, traj, None)

    except Exception as e:
        return Response(
            scene_description=None,
            trajectory_predictions=None,
            parsing_error=str(e)
        )


# ============================================================
# Runner
# ============================================================

def run_once(input_json_path: str) -> dict:
    start = time.time()

    scene_name, frames = utils.load_frame_json(input_json_path)
    frame = frames[0]

    prev_speed, prev_curv = utils.compute_prev_actions_from_json(frame["ego_info"])
    prev_speed = np.asarray(prev_speed, float).tolist()
    prev_curv = np.asarray(prev_curv, float).tolist()

    inp = InputData(
        front_camera_path=frame["image_name"],
        previous_frame_speed=prev_speed,
        previous_frame_curvature=prev_curv
    )

    response = predict_trajectory(inp)

    inference_time = time.time() - start

    # If parsing error: return JSON only
    if response.parsing_error:
        out_json = {
            "scene": scene_name,
            "frame": frame["frame_index"],
            "error": response.parsing_error,
            "inference_time": inference_time,
        }

        out_path = os.path.join(JSON_DIR, f"{scene_name}_frame{frame['frame_index']}.json")
        with open(out_path, "w") as f:
            json.dump(out_json, f, indent=2)

        return out_json

    # Compute metrics
    ade, fde, l2 = utils.compute_metrics(
        frame["ego_info"]["gt_positions"],
        response.trajectory_predictions
    )

    # Save viz
    utils.visualize_from_json_frame(
        model="PYqwen2.5vl",
        frame=frame,
        scene_name=scene_name,
        pred_actions=response.trajectory_predictions,
        viz_dir=VIZ_DIR
    )

    # Save JSON result
    json_data = {
        "scene": scene_name,
        "frame": frame["frame_index"],
        "image": frame["image_name"],
        "scene_description": response.scene_description,
        "trajectory": response.trajectory_predictions,
        "ade": ade,
        "fde": fde,
        "l2": l2,
        "inference_time": inference_time,
        "error": None
    }

    out_path = os.path.join(JSON_DIR, f"{scene_name}_frame{frame['frame_index']}.json")
    with open(out_path, "w") as f:
        json.dump(json_data, f, indent=2)

    return json_data


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    print(json.dumps(run_once("input/scene_123.json")))
