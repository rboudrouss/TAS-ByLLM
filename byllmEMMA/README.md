# byllmEMMA — README
byllmEMMA is a even lightweight implementation of the already lightweight lightEMMA (End to end multimodal model for autonomous driving) model. ours aims was to

* Implement trajectory prediction for one frame (here from the nuscnene dataset).
* Compare the performance of the task performed by :
    * pyhton scripts using ollama library. (predictHF.py HF was originaly used to refer to HuggingFace models but here it refers to ollama models because we change mid-way)
    * Jac+Byllm script (predictMinSem.jac)
    * jac+Byllm using semstrings (predictWithString.jac)
    * jac+Byllm using semstrings and a prompt in parameters (used mostly to compare outputs evalutation with python code). (predict.jac)

## Requirements
* byllm
* jac
* ollama
* numpy
* matplotlib
* PIL
* openCV
... from utils.py library where data are processed and formated before and after prediction.

```
pip install -r requirements.txt
```
if the requirements.txt file is not working,run the code and install the required python packages manually using after installing the main dependencies (byllm, jac, ollama).


## Usage

### Using python scripts

````
python predictHF.py
````

### Using jac+byllm scripts

```
jac predict.jac
```


## Input (``./input`` folder)

Unfortunaly, I couldn't make argparse work with jac scripts so the input data path name are hardcoded in the scripts.

Input data contain one frame from the nuscenes dataset and a json file with the ego vehicle that contains past speed , past curvature and other useful information for trajectory prediction. It's a simplified version of the nuscenes dataset json files.

The input data are formated using the utils.py library ( to convert driving intent - tuples of speed and curvature- into coordinates waypoints).

for script working with prompt, the prompt is loaded fromthe ``./prompts`` file, it contain a YAML file with the text prompt that can contain personnalized variables.

## Output (``./results_\*`` folder)

* a json file with the predicted trajectory coordinates.
* a png file with the plotted trajectory.



## benchamrk (```./experiment.sh```)
A bash script to compare the python and jac+byllm implementations.

### usage
```
sh experiment.sh 5 RESULT_OUTPUT  jac_FILEPATH
```

compare the script on 5 runs, save the results in the RESULT_OUTPUT folder, using the jac_FILEPATH jac script.

## metrics comparison

The metrics used to compare the different implementations are :
* minADE (minimum Average Displacement Error)
* minFDE (minimum Final Displacement Error)
* Miss Rate (MR)
* computation time
The results are saved in a json file in the results folder.

### samples results

```
{
  "python": {
    "pipeline": "python",
    "total_runs": 10,
    "valid_runs": 10,
    "error_runs": 0,
    "error_ratio": 0.0,
    "mean_ade": 2.3901285518669346,
    "mean_fde": 4.576925840684433,
    "mean_l2": 2.390128551866935,
    "mean_inference_time": 131.46311509609222
  },
  "jac": {
    "pipeline": "jac",
    "total_runs": 10,
    "valid_runs": 9,
    "error_runs": 1,
    "error_ratio": 0.1,
    "mean_ade": 2.825730360722321,
    "mean_fde": 5.1226576199573035,
    "mean_l2": 2.8257303607223214,
    "mean_inference_time": 108.13730931282043
  },
  "comparison": {
    "ade_diff": -0.43560180885538635,
    "fde_diff": -0.5457317792728702,
    "l2_diff": -0.43560180885538635,
    "inference_time_diff": 23.32580578327179,
    "error_ratio_diff": -0.1
  },
  "winner": {
    "ADE": {
      "python": 2.3901285518669346,
      "jac": 2.825730360722321,
      "winner": "python"
    },
    "FDE": {
      "python": 4.576925840684433,
      "jac": 5.1226576199573035,
      "winner": "python"
    },
    "L2": {
      "python": 2.390128551866935,
      "jac": 2.8257303607223214,
      "winner": "python"
    },
    "Inference Time": {
      "python": 131.46311509609222,
      "jac": 108.13730931282043,
      "winner": "jac"
    },
    "Error Rate": {
      "python": 0.0,
      "jac": 0.1,
      "winner": "python"
    }
  }
}
```
