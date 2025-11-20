# 1. Introduction

L'objectif de notre demarche est d'adopter le point de vue d'un développeur souhaitant intégrer la bibliothèque à son projet. Nous commençons par implémenter quelques applications simples pour prendre en main la syntaxe de `jac` et de `byllm` (un traducteur, un générateur de niveaux) et l'opérateur `by`.

Nous testons ensuite les fonctionnalités multimodales de `byllm()` à travers un projet de prédiction de trajectoire future d'un véhicule. Finalement, nous comparerons ce programme au même réalisé en Python, en utilisant des techniques plus traditionnelles, selon différentes métriques.

[Contributions]():

- Exemples simples d'utilisation de jac/byllm et de l'opérateur by.
    - Presentation d'un traducteur et d'un generateur de profils d'etudiant implémentée avec jac/byllm et opérateur by
- TrajectoryPrediction
    - Prototype multimodal utilisant byllm(). Prédis les trajectoires futures à partir des informations passées de l'ego d'un véhicule et d'une photo frontale.
- Benchmark
    - Comparaison qualitative (LoC, Temps d'inference, evaluation de l'output)
- Reflexions personnelle.
