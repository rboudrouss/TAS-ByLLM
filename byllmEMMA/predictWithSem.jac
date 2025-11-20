"""
This script performs autonomous driving scene analysis and trajectory prediction
using a vision language model accessed through byllm.
"""
import from byllm.llm  { Model }
import from byllm.types { Image }
import from typing { List, Dict, Any, Tuple }
import os;
import json;
import time;
import utils;

glob llm = Model(model_name="ollama/qwen2.5vl");

# ============================================================
# Output directories
# ============================================================

let RESULTS_DIR = "results_jacWithSem";
let JSON_DIR = os.path.join(RESULTS_DIR, "json");
let VIZ_DIR = os.path.join(RESULTS_DIR, "viz");

let json_dir=os.makedirs(JSON_DIR, exist_ok=True);
let vz_dir=os.makedirs(VIZ_DIR, exist_ok=True);

# ============================================================
# Data structures
# ============================================================

obj drivingAction{
    has speed: float;
    has curvature: float;
}

obj VehiculeEgoInfo{
    has frontCameraImage: Image;
    has pastSpeeds: List[float];
    has pastCurvatures: List[float];
}
sem drivingAction = "A tuple defining the ego vehicle's speed and curvature ";
sem VehiculeTrajectoryWaypoint.speed = "The ego vehicle's speed at this waypoint in m per s. at 0";
sem VehiculeTrajectoryWaypoint.curvature = "Ego vehicle's curvature at this waypoint, where positive indicates turning left and negative indicates turning right.";

sem VehiculeEgoInfo = "Structured data used for driving scene understanding and trajectory prediction.";
sem VehiculeEgoInfo.frontCameraImage = "Front view camera image showing the current driving scene.";
sem VehiculeEgoInfo.pastSpeeds = "Ego vehicle's speed for the past 3 seconds with 0.5 sec resolution (last index is the most recent).";
sem VehiculeEgoInfo.pastCurvatures = "Ego vehicle's curvature for the past 3 seconds with 0.5 sec resolution (last index is the most recent). A positive curvature indicates the ego is turning left. A negative curvature indicates the ego is turning right.";

# ============================================================
# LLM call
# ============================================================

def predictSixFutureVehiculeTrajectoryWaypoint(pastVehiculeEgoInfo: VehiculeEgoInfo)
 -> List[VehiculeTrajectoryWaypoint] by llm(temperature=0.4);

sem predictSixFutureVehiculeTrajectoryWaypoint ="""
    Predict the speed and curvature for the next 6 waypoints, with 0.5-second resolution.
    The predicted speed and curvature changes must obey the physical constraints of the vehicle.
    Predict Exactly 6 pairs of speed and curvature, in the format:
    [(v1, c1), (v2, c2), (v3, c3), (v4, c4), (v5, c5), (v6, c6)].
    """;

# ============================================================
# LLM call
# ============================================================



# ============================================================
# Helper to build and save result JSON
# ============================================================

def save_result_json(scene_name: str, frame: Dict[str, Any], result: Dict[str, Any]) {
    let filename = F"{scene_name}_frame{frame['frame_index']}_jac.json";
    let out_path = os.path.join(JSON_DIR, filename);

    with open(out_path, "w") as f {
        json.dump(result, f, indent=2);
    }
}


with entry {
    # Measure full run time (including byllm call)
    let start_time = time.time();

    (scene_name, frames)  = utils.load_frame_json("input/scene_123.json");
    frame = frames[0];

    (prev_speed, prev_curv) = utils.compute_prev_actions_from_json(
        frame["ego_info"]
    );

    vehiculeEgoInfo = VehiculeEgoInfo(
        frontCameraImage = Image(frame["image_name"]),
        pastSpeeds = prev_speed,
        pastCurvatures = prev_curv,
    );

    # Default parsing error state
    let parsing_error: str | None = None;
    let predicted_waypoint: List[VehiculeTrajectoryWaypoint] | None = None;

    # LLM call
    try {
        predicted_waypoint = predictSixFutureVehiculeTrajectoryWaypoint(vehiculeEgoInfo);
    } except Exception as e {
        parsing_error = F"llm_call_failed: {e}";
    }

    # Validate structured output
    if parsing_error is None {
        if predicted_waypoint is None {
            parsing_error = "predicted_waypoint is None";
        } elif len(predicted_waypoint) <6 {
            parsing_error = F"expected 6 waypoints, got {len(predicted_waypoint)}";
        }
    }


    # Convert list of VehiculeTrajectoryWaypoint objects to a list of (speed, curvature) tuples (floats)
    if parsing_error is None {
    let traj_tuples = [(float(wp.speed), float(wp.curvature)) for wp in predicted_waypoint[:6]];
    }
    let inference_time = time.time() - start_time;

    # Case 1: parsing error -> no viz, no metrics, but still save JSON
    if parsing_error is not None {
        let result = {
            "scene": scene_name,
            "frame": frame["frame_index"],
            "error": parsing_error,
            "inference_time": inference_time,
        };

        save_result_json(scene_name, frame, result);
        # Print a single JSON line for the aggregator
        print(json.dumps(result));
    } else {
        # Safe to use response here
        (ade, fde, l2) = utils.compute_metrics(
            frame["ego_info"]["gt_positions"],
            traj_tuples,
        );


        # Save visualization inside results/viz
        utils.visualize_from_json_frame(
            model = "JACqwen2.5vl",
            frame = frame,
            scene_name = scene_name,
            pred_actions = traj_tuples,
            viz_dir = VIZ_DIR,
        );

        let result = {
            "scene": scene_name,
            "frame": frame["frame_index"],
            "image": frame["image_name"],
            "scene_description": "",
            "trajectory": traj_tuples,
            "ade": ade,
            "fde": fde,
            "l2": l2,
            "inference_time": inference_time,
            "error": None,
        };

        save_result_json(scene_name, frame, result);
        # Print a single JSON line for the aggregator
        print(json.dumps(result));
    }
}
