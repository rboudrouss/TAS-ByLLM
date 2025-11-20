# 1. Introduction

L'exploration personnelle de byLLM ne s'inscrit ni strictement dans la continuité de l'évaluation du MTP, déjà très complète, ni comme une critique destinée à reproduire ses résultats. L'objectif est d'adopter le point de vue d'un développeur souhaitant intégrer la bibliothèque à son projet. Nous commençons par implémenter quelques applications simples pour prendre en main la syntaxe de `jac` et de `byllm` (un traducteur, un générateur de niveaux) et l'opérateur `by`, puis testons les fonctionnalités multimodales de `byllm()` à travers un programme de prédiction de trajectoire future d'un véhicule. Finalement, nous comparerons ce programme au même réalisé en Python, en utilisant des techniques plus traditionnelles, selon différentes métriques.

Resultat de l'exploration:

- Examples simples d'utilisation de jac/byllm et de l'opérateur by.
    - Presentation d'un traducteur et d'un generateur de profils d'etudiant implémentée avec jac/byllm et opérateur by
- TrajectoryPrediction
    - Prototype multimodal utilisant byllm(). Prédis les trajectoires futures à partir des informations passées de l'ego d'un véhicule et d'une photo frontale.
- Benchmark
    - Comparaison qualitative (LoC, Temps d'inference, evaluation de l'output)
- Reflexions personnelle.



# 2. Prediction de trajectore de vehicule.


L'objectif de ce projet est de prédire la trajectoire future d'un véhicule en utilisant des données multimodales : des séquences temporelles de positions (x, y) et des images capturées par une caméra embarquée. Nous utilisons le modèle qwen2.5vl via byllm() pour exploiter à la fois les données textuelles et visuelles.