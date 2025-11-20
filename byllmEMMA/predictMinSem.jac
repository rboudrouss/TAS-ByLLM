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

let RESULTS_DIR = "results_jacMinSem";
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
    has pastDrivingActions: Tuple[drivingAction, ...];
}

obj InputData{
    has vehiculeEgoInfo: VehiculeEgoInfo;
    has outputSecondInterval: float;
    has outputCount: int = 6;
}

def predictFutureVehiculeDrivingAction(inputData: InputData)
->  Tuple[drivingAction, ...] by llm(temperature=0.4);

sem InputData = """
    Input data structure for predicting future driving actions of the ego vehicle.
    Contains the current ego vehicle information and parameters for the output trajectory prediction.
""";
sem InputData.vehiculeEgoInfo = "The current ego vehicle information including camera image and past speeds/curvatures.";
sem InputData.outputSecondInterval = "Time interval in seconds between each predicted driving actions in the output trajectory.";
sem InputData.outputCount = "Number of future driving actions to predict.";

sem drivingAction = "A tuple defining the ego vehicle's speed and curvature ";
sem drivingAction.speed = "The ego vehicle's speed at this waypoint in m per s.";
sem drivingAction.curvature = "Ego vehicle's curvature at this waypoint, where positive indicates turning left and negative indicates turning right.";



def predictFutureVehiculeDrivingAction(inputData: InputData) ->  Tuple[drivingAction, ...] by llm(temperature=0.4);

sem predictFutureVehiculeDrivingAction ="""
    Given the input ego vehicle information, predict the future driving actions (speeds and curvatures)
    for the next `outputCount` waypoints, each spaced by `outputSecondInterval` seconds.""";
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
        pastDrivingActions = tuple(
            drivingAction(speed=s, curvature=c)
            for (s, c) in zip(prev_speed, prev_curv)
        ),
    );
    inputData = InputData(
        vehiculeEgoInfo = vehiculeEgoInfo,
        outputSecondInterval = 0.5,
        outputCount = 6,
    );



    # Default parsing error state
    let parsing_error: str | None = None;
    let predicted_waypoint: List[VehiculeTrajectoryWaypoint] | None = None;

    # LLM call
    try {
        predicted_waypoint = predictFutureVehiculeDrivingAction(inputData);
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
    let traj_tuples = [(float(wp.speed), float(wp.curvature)) for wp in predicted_waypoint[:6]];
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
