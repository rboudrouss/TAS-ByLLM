# byllm Samples

## Setup

install ollama

```bash
sudo apt install ollama
ollama pull llama3
```

install byllm
```bash
python -m venv .venv
source .venv/bin/activate
pip install byllm
```

run the code
```
jac test.jac
```

## Samples

### Driving Trajectory Prediction (Inspired by LightEMMA)

Take a front camera image and ego information (example from nuscnenes) and return the future trajectory, compared by the grount truth trajectory using ADE, FDE and L2 error. (On figure, dark blue is ground truth)

![scene](./samples/trajectoryPrediction/viz/scene-123_frame0.png)
```
===========Scene Description:===================================
The image shows a road scene with a clear view of the road ahead. There are no visible pedestrians or other vehicles in the immediate vicinity, and the lane markings are well-defined. The road appears to be straight ahead, and there are no traffic lights or other obstructions. The surroundings suggest a suburban or urban environment with no significant distractions or hazards.
===========Trajectory Predictions:=============================
[(3.5, -0.005), (3.6, -0.003), (3.7, -0.002), (3.8, -0.001), (3.9, 0.0), (4.0, 0.001)]
Image saved at viz/scene-123_frame0.png
[✓] Visualization Saved: viz/scene-123_frame0.png
===========Evaluation metrics:=========================
Average Displacement Error (ADE): 5.255119771349066 m
Final Displacement Error (FDE): 11.040168522264503 m
L2 Error: [1.430008741232025, 0.6602189030919969, 3.5301110464119967, 6.090069047227627, 8.780142367866251, 11.040168522264503]
```

### level Generator

Produce the next 2D level with obstacle, enemies, difficulty level.

### translator

Translate your text in any language.