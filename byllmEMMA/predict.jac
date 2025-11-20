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

let RESULTS_DIR = "results_promptvsprompt";
let JSON_DIR = os.path.join(RESULTS_DIR, "json");
let VIZ_DIR = os.path.join(RESULTS_DIR, "viz");

let json_dir=os.makedirs(JSON_DIR, exist_ok=True);
let vz_dir=os.makedirs(VIZ_DIR, exist_ok=True);

# ============================================================
# Data structures
# ============================================================

obj Response{
    has sceneDescription: str;
    has trajectoryPredictions: List[Tuple[float, ...]];
}

obj Input{
    has frontCameraImage: Image;
    has previousFrameSpeed: List[float];
    has previousFrameCurvature: List[float];
    has instructions: str;
}

sem Response = "Final output of the autonomous driving reasoning task, including a scene level analysis and six future trajectory predictions.";

sem Response.sceneDescription = """A concise and clear paragraph describing the driving scene
visible in the front camera image. This includes lane markings, traffic lights, vehicles, pedestrians, and all relevant objects.
 The description must focus only on the scene and never infer the ego vehicle's actions or intentions.""";

sem Response.trajectoryPredictions = """Six predicted future waypoint values describing how the ego vehicle should drive over
the next three seconds. Each waypoint contains a speed in m per s and a curvature value, ordered at zero point five second intervals.
The six waypoints correspond to the format [(v1,c1),(v2,c2),(v3,c3),(v4,c4),(v5,c5),(v6,c6)].""";

sem Input = "Structured data used for driving scene understanding and trajectory prediction.";
sem Input.frontCameraImage = "The front view camera image showing the current driving scene.";
sem Input.previousFrameSpeed = "A list of ego speed values in m per s covering the last three seconds with zero point five second resolution. The final value is the most recent.";
sem Input.previousFrameCurvature = """A list of ego curvature values covering the last three seconds with zero point five second resolution.
Positive curvature indicates a left turn, negative curvature indicates a right turn.""";

def predict_trajectory(input: Input) -> Response by llm(temperature=0.4);



sem Waypoint = "A predicted waypoint defining the ego vehicle's speed and curvature at a future time step.";
sem Waypoint.speed = "The predicted ego speed at this waypoint in m per s.";
sem Waypoint.curvature = "The predicted ego curvature at this waypoint, where positive indicates turning left and negative indicates turning right.";


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

    input = Input(
        frontCameraImage = Image(frame["image_name"]),
        previousFrameSpeed = prev_speed,
        previousFrameCurvature = prev_curv,
        instructions = utils.load_and_format_prompt(
            "prompts/config_prompt.yaml",
            "waypoint_prompt",
            prev_speed = prev_speed,
            prev_curvatures = prev_curv
        )
    );

    # Default parsing error state
    let parsing_error: str | None = None;
    let response: Response | None = None;

    # LLM call
    try {
        response = predict_trajectory(input);
    } except Exception as e {
        parsing_error = F"llm_call_failed: {e}";
    }

    # Validate structured output
    if parsing_error is None {
        if response is None {
            parsing_error = "response is None";
        } elif response.trajectoryPredictions is None {
            parsing_error = "trajectoryPredictions is None";
        } elif len(response.trajectoryPredictions) != 6 {
            parsing_error = F"expected 6 waypoints, got {len(response.trajectoryPredictions)}";
        }
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
            response.trajectoryPredictions,
        );

        # Save visualization inside results/viz
        utils.visualize_from_json_frame(
            model = "JACqwen2.5vl",
            frame = frame,
            scene_name = scene_name,
            pred_actions = response.trajectoryPredictions,
            viz_dir = VIZ_DIR,
        );

        let result = {
            "scene": scene_name,
            "frame": frame["frame_index"],
            "image": frame["image_name"],
            "scene_description": response.sceneDescription,
            "trajectory": response.trajectoryPredictions,
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
