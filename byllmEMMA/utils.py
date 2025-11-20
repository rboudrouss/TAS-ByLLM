import os
import cv2
import re
import math
import json
import yaml
import numpy as np
from pyquaternion import Quaternion
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import datetime


import yaml

def load_and_format_prompt(yaml_path: str, prompt_name: str, **kwargs) -> str:
    # Load YAML
    with open(yaml_path, "r") as f:
        data = yaml.safe_load(f)

    if "prompts" not in data:
        raise ValueError("YAML file missing top-level key 'prompts'")

    prompts = data["prompts"]
    if prompt_name not in prompts:
        raise ValueError(f"Prompt '{prompt_name}' not found in YAML.")

    raw = prompts[prompt_name]
    if raw is None:
        raise ValueError(f"Prompt '{prompt_name}' is null in YAML.")

    # Safe formatting so unknown placeholders stay literal
    class SafeDict(dict):
        def __missing__(self, key):
            return "{" + key + "}"

    return raw.format_map(SafeDict(**kwargs))


def save_result_to_json(
    model: str,
    scene_name: str,
    frame_index: int,
    image_path: str,
    scene_description: str,
    trajectory_predictions: list,
    ade: float,
    fde: float,
    l2,
    timestamp: str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
):
    # Use the provided image path (could be a URL or local path)
    img_url = image_path

    data = {
        "scene_name": scene_name,
        "frame_index": frame_index,
        "image_url": img_url,
        "scene_description": scene_description,
        "trajectory_predictions": trajectory_predictions,
        "metrics": {
            "ADE": ade,
            "FDE": fde,
            "L2": l2,
        },
        "timestamp": timestamp,
    }

    output_file = f"{model}_{scene_name}_frame{frame_index}_{timestamp}.json"

    # Write JSON file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def visualize_from_json_frame(
    model,
    frame,
    scene_name,
    pred_actions,
    viz_dir="viz",
    timestamp=datetime.datetime.now().strftime("%Y%m%d_%H%M%S"),
):
    img_path = frame["image_name"]
    if not os.path.exists(img_path):
        print(f"[!] Missing image {img_path}")
        return

    # Ground truth positions
    gt_positions = frame["ego_info"]["gt_positions"]

    # Predicted trajectory positions
    pred_positions = integrate_driving_commands(pred_actions)

    # Camera parameters
    cam_params = frame["camera_params"]

    # Create output directory
    os.makedirs(viz_dir, exist_ok=True)

    # Add timestamp

    # Output path with timestamp
    out_path = os.path.join(
        viz_dir,
        f"{model}_{scene_name}_frame{frame['frame_index']}_{timestamp}.png"
    )
    # Visualization
    OverlayTrajectory(
        img_path=img_path,
        wp_world1=gt_positions,
        wp_world2=pred_positions,
        cam_to_ego=cam_params,
        ego_pos=(0, 0),
        ego_heading=0.0,
        save_path=out_path,
    )


def compute_prev_actions_from_json(ego_info, dt=0.5):
    """
    Compute prev_speed and prev_curvature from a scene JSON entry.

    ego_info: dict containing keys:
        - "obs_positions": list of [x, y] in ego frame
    dt: timestep between obs points (default = 0.5 seconds)

    Returns:
        prev_speed: list of float
        prev_curvatures: list of float
    """

    obs_positions = ego_info["obs_positions"]
    positions = [np.array(p, dtype=float) for p in obs_positions]

    # --------------------------
    # SPEED: distance / dt
    # --------------------------
    prev_speed = []
    for i in range(1, len(positions)):
        p1 = positions[i - 1]
        p2 = positions[i]
        dist = np.linalg.norm(p2 - p1)
        prev_speed.append(dist / dt)

    # --------------------------
    # CURVATURE
    # κ = angle_between(v1,v2) / arc_length
    # --------------------------
    prev_curvatures = []
    for i in range(1, len(positions) - 1):
        p0 = positions[i - 1]
        p1 = positions[i]
        p2 = positions[i + 1]

        v1 = p1 - p0
        v2 = p2 - p1

        s1 = np.linalg.norm(v1)
        s2 = np.linalg.norm(v2)

        if s1 < 1e-6 or s2 < 1e-6:
            prev_curvatures.append(0.0)
            continue

        # angle between segments
        dot = np.dot(v1, v2)
        cos_theta = np.clip(dot / (s1 * s2), -1.0, 1.0)
        theta = float(np.arccos(cos_theta))

        # average arc length
        s = 0.5 * (s1 + s2)
        curvature = theta / s if s > 1e-6 else 0.0
        prev_curvatures.append(curvature)

    return prev_speed, prev_curvatures
def load_frame_json(path):
    with open(path, "r") as f:
        data = json.load(f)

    scene_name = data["scene_info"]["name"]
    frames = data["frames"]
    return scene_name, frames

def quaternion_to_yaw(quaternion):
    """
    Convert a quaternion (w, x, y, z) to yaw (rotation about the z-axis) in radians.

    Parameters:
    quaternion (tuple): A tuple (w, x, y, z) representing the quaternion.

    Returns:
    float: Yaw angle in radians.
    """
    w, x, y, z = quaternion
    yaw = math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y**2 + z**2))
    return yaw


def global_to_ego_frame(cur_pos, cur_heading, positions):
    """
    Transforms a list of global positions to the ego vehicle's local frame.

    Args:
        cur_pos (tuple): The current position of the ego vehicle (x, y).
        cur_heading (float): The heading of the ego vehicle in radians.
        positions (list of tuples): A list of global positions [(x1, y1), (x2, y2), ...].

    Returns:
        list of tuples: Transformed positions in the ego frame.
    """
    x0, y0 = cur_pos
    cos_h, sin_h = np.cos(-cur_heading), np.sin(
        -cur_heading
    )  # Negate heading for inverse rotation

    transformed_positions = []
    for x, y in positions:
        dx, dy = x - x0, y - y0  # Translate
        x_ego = cos_h * dx - sin_h * dy  # Rotate
        y_ego = sin_h * dx + cos_h * dy  # Rotate
        transformed_positions.append((x_ego, y_ego))

    return transformed_positions


def compute_speed(points, past_timestamps):
    """
    Computes the speed at each point using Euclidean distance between adjacent points.

    Parameters:
        points (list of tuples): List of (x, y) coordinates.
        time_interval (float): Time interval between points (default is 0.5s).

    Returns:
        list of floats: Speed values at each segment.
    """
    speeds = []
    for i in range(1, len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i + 1]

        t1 = past_timestamps[i]
        t2 = past_timestamps[i + 1]

        # Compute Euclidean distance
        distance = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        time_interval = (t2 - t1) / 1e6  # Convert to seconds

        # Compute speed (distance / time)
        speed = distance / time_interval

        if speed < 0.2:
            speed = 0.0

        speeds.append(round(speed, 3))

    return speeds


def compute_curvature(points):
    """
    Computes the curvature at each point using its neighboring points.
    The curvature is computed using the osculating circle formula.

    Parameters:
        points (list of tuples): List of (x, y) coordinates.

    Returns:
        list of floats: Curvature values for each valid point.
    """
    curvatures = []
    for i in range(1, len(points) - 1):
        x1, y1 = points[i - 1]
        x2, y2 = points[i]
        x3, y3 = points[i + 1]

        # Compute distances
        a = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        b = np.sqrt((x3 - x2) ** 2 + (y3 - y2) ** 2)
        c = np.sqrt((x3 - x1) ** 2 + (y3 - y1) ** 2)

        # Compute signed area using determinant formula
        area = (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2)) / 2.0

        # Curvature formula: 4 * area / (a * b * c)
        if a * b * c != 0:  # Avoid division by zero
            curvature = 4 * area / (a * b * c)
            if curvature > 0.2:
                curvature = 0.0
            elif curvature < -0.2:
                curvature = -0.0
        else:
            curvature = 0  # Assign zero curvature for degenerate cases

        curvatures.append(round(curvature, 3))

    return curvatures


def integrate_driving_commands(commands, dt=0.5):
    """
    Computes the trajectory given an initial position (0,0), orientation 0, and a list of driving commands.

    Parameters:
    commands (list of tuples): List of (speed, curvature) pairs.
    dt (float): Time step duration in seconds (default is 0.5s).

    Returns:
    list of tuples: List of (x, y, theta) positions over time.
    """
    x, y, heading = 0.0, 0.0, 0.0
    trajectory = [(x, y)]

    for v, kappa in commands:
        x += v * np.cos(heading) * dt
        y += v * np.sin(heading) * dt
        heading += kappa * v * dt  # Update heading
        trajectory.append((x, y))

    return trajectory[1:]  # Exclude the initial position




def OverlayTrajectory(
    img_path: str,
    wp_world1: list,
    wp_world2: list,
    cam_to_ego,
    ego_pos: tuple,
    ego_heading: float,
    save_path: str,
):
    # Load the image from file
    original_img = cv2.imread(img_path)
    if original_img is None:
        raise ValueError(f"Failed to load image from path: {img_path}")

    img = original_img.copy()  # Work on a copy to keep the original unchanged

    # --- Form Transformation Matrices ---
    T_ego_global = np.eye(4)
    T_ego_global[:3, :3] = np.array(
        [
            [np.cos(ego_heading), -np.sin(ego_heading), 0],
            [np.sin(ego_heading), np.cos(ego_heading), 0],
            [0, 0, 1],
        ]
    )
    T_ego_global[:3, 3] = np.array([ego_pos[0], ego_pos[1], 0])

    T_cam_ego = np.eye(4)
    T_cam_ego[:3, :3] = Quaternion(cam_to_ego["rotation"]).rotation_matrix
    T_cam_ego[:3, 3] = cam_to_ego["translation"]

    T_cam_global = T_ego_global @ T_cam_ego
    T_global_cam = np.linalg.inv(T_cam_global)

    # Only using ground truth and prediction colors
    colors = {
        "wp_world1": (0.0, 0.23, 0.34, 1.0),    # Dark blue for ground truth
        "wp_world2": (0.56, 0.79, 0.90, 1.0),   # Light blue for prediction
    }

    # Set up the figure and axis
    fig, ax = plt.subplots(figsize=(img.shape[1] / 100, img.shape[0] / 100), dpi=100)
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    ax.set_position([0, 0, 1, 1])
    ax.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    ax.axis("off")
    ax.set_xlim(0, img.shape[1])
    ax.set_ylim(img.shape[0], 0)

    # Define common styling properties
    linewidth = 3
    linestyle = "solid"
    arrowstyle = "->"
    mutation_scale = 20
    arrow_extension = 10

    # Process only ground truth and prediction trajectories
    for wp_world, key in zip(
        [wp_world1, wp_world2], ["wp_world1", "wp_world2"]
    ):
        color = colors[key]

        # Transform 3D World Points to Camera Coordinates
        points3d_world = [np.array([p[0], p[1], 0]) for p in wp_world]
        points3d_cam = np.array(
            [(T_global_cam @ np.append(p, 1))[:3] for p in points3d_world]
        )

        valid = points3d_cam[:, 2] > 0
        if not valid.any():
            continue

        # Project valid points onto the image plane
        points_valid = points3d_cam[valid]
        proj = (cam_to_ego["camera_intrinsic"] @ points_valid.T).T
        points3d_img = proj[:, :2] / proj[:, 2][:, np.newaxis]

        if len(points3d_img) <= 1:
            continue

        # Draw trajectory line
        x, y = zip(*points3d_img)
        ax.plot(x, y, linestyle=linestyle, color=color, linewidth=linewidth)

        # Draw arrows on each segment
        for i in range(1, len(points3d_img)):
            start = np.array(points3d_img[i - 1])
            end = np.array(points3d_img[i])
            vector = end - start
            norm = np.linalg.norm(vector)
            if norm != 0:
                end = end + arrow_extension * (vector / norm)
            ax.annotate(
                "",
                xy=end,
                xytext=start,
                arrowprops=dict(
                    arrowstyle=arrowstyle,
                    color=color,
                    lw=linewidth,
                    mutation_scale=mutation_scale,
                ),
            )

    # Convert Matplotlib figure to OpenCV image
    canvas = FigureCanvas(fig)
    canvas.draw()
    # Get RGBA UInt8 buffer from Matplotlib
    buf = canvas.buffer_rgba()
    width, height = canvas.get_width_height()

    # Convert to a NumPy array with correct shape
    buf = np.frombuffer(buf, dtype=np.uint8)
    buf = buf.reshape((height, width, 4))  # ALWAYS RGBA (4 channels)

    # Drop alpha
    rgb = buf[:, :, :3]

    # Convert RGB → BGR for OpenCV
    img = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

    # Close the matplotlib figure to prevent memory leaks
    plt.close(fig)

    # Save the Updated Image
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    cv2.imwrite(save_path, img)


def save_dict_to_json(data, file_path):
    """
    Saves a dictionary to a JSON file.

    Args:
        data (dict): Dictionary to save
        file_path (str): Path where the JSON file should be saved
    """
    # Ensure the directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Write the dictionary to a JSON file
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def load_json_file(file_path):
    """
    Loads a JSON file into a dictionary.

    Args:
        file_path (str): Path to the JSON file to load

    Returns:
        dict: The loaded dictionary or empty dict if the file doesn't exist
    """
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def load_config(config_path):
    """
    Loads a YAML file into a dictionary.

    Args:
        file_path (str): Path to the config file to load

    Returns:
        dict: The loaded dictionary
    """
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def get_scene_number(scene_name):
    """
    Extract numeric part from scene name (e.g., "scene-0495" -> 495)

    Args:
        scene_name (str): Scene name

    Returns:
        int: Extracted scene number or infinity if not found
    """
    match = re.search(r"(\d+)", scene_name)
    if match:
        return int(match.group(1))
    return float("inf")

def update_scene_json(scene_file_path, frame_data, metadata=None):
    """
    Updates a scene JSON file with new frame data in the hierarchical structure.
    If the file doesn't exist, creates it with the proper structure.

    Args:
        scene_file_path (str): Path to the scene JSON file
        frame_data (dict): Data for a single frame to add to the scene
        metadata (dict, optional): Scene metadata to update/add
    """
    # Load existing data or create new structure
    scene_data = load_json_file(scene_file_path)

    # Initialize structure if needed
    if not scene_data:
        scene_data = {
            "scene_info": {
                "name": frame_data.get("scene_name", ""),
                "description": frame_data.get("description", ""),
                "first_sample_token": frame_data.get("first_sample_token", ""),
                "last_sample_token": frame_data.get("last_sample_token", "")
            },
            "frames": [],
            "metadata": metadata or {}
        }

    # Add the new frame
    scene_data["frames"].append(frame_data)

    # Update metadata if provided
    if metadata:
        scene_data["metadata"].update(metadata)

    # Update total frames count
    scene_data["metadata"]["total_frames"] = len(scene_data["frames"])

    # Save updated data
    save_dict_to_json(scene_data, scene_file_path)

def format_long_text(text, max_line_length=80):
    """
    Break long text into structured paragraphs for better readability in JSON.
    Instead of trying to add literal newlines (which get escaped in JSON),
    split the text into separate paragraph elements in a list.

    Args:
        text (str): The text to format
        max_line_length (int): Maximum length per paragraph

    Returns:
        list: List of paragraph strings
    """
    if not text:
        return []

    # Split text into paragraphs first (if there are any)
    paragraphs = text.split('\n')

    # Further split long paragraphs
    result = []
    for paragraph in paragraphs:
        if len(paragraph.strip()) == 0:
            continue

        # If paragraph is short enough, add it as is
        if len(paragraph) <= max_line_length:
            result.append(paragraph.strip())
        else:
            # Split long paragraph into chunks
            words = paragraph.split()
            current_line = []
            current_length = 0

            for word in words:
                # Check if adding this word would exceed the line length
                if current_length + len(word) + (1 if current_length > 0 else 0) > max_line_length:
                    # Add the current line to result and start a new line
                    if current_line:
                        result.append(' '.join(current_line))
                    current_line = [word]
                    current_length = len(word)
                else:
                    # Add the word to the current line
                    current_line.append(word)
                    current_length += len(word) + (1 if current_length > 0 else 0)

            # Add the last line if there's anything left
            if current_line:
                result.append(' '.join(current_line))

    return result


def compute_metrics(gt_positions, pred_actions):
    """
    Compute ADE, FDE and L2 distances between ground truth and predicted trajectories.

    Args:
        gt_positions: list of (x, y) tuples for ground truth
        pred_positions: list of (x, y) tuples for predicted trajectory

    Returns:
        ade: float
        fde: float
        l2_distances: list of float (l2 error per point)
    """
    pred_positions = integrate_driving_commands(pred_actions, dt=0.5)

    if len(gt_positions) != len(pred_positions):
        raise ValueError(
            f"GT and Pred must have same length, got {len(gt_positions)} and {len(pred_positions)}."
        )

    # L2 per point
    l2_distances = [
        float(np.linalg.norm(np.array(gt) - np.array(pred)))
        for gt, pred in zip(gt_positions, pred_positions)
    ]

    # ADE: mean L2
    ade = float(np.mean(l2_distances))

    # FDE: L2 of final point
    fde = float(l2_distances[-1])

    return ade, fde, l2_distances


invoke-model(
    llm,
    {temperature:0.4},
    predictFutureVehiculeDrivingAction,
    [inputData],
    [ (InputData), Tuple[drivingAction, ...] ]
)
