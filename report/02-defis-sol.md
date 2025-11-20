# 2. Solution proposée : Meaning-Typed Programming

L'objectif de ce travail est d'exploiter les informations sémantiques présentes dans le code pour automatiser le prompt engineering. Plutôt que d'exiger des développeurs qu'ils construisent manuellement des prompts détaillés ou des annotations, l'approche proposée utilise la structure et la sémantique du code pour générer des entrées pour les LLMs.

## 2.1. Objectifs de conception

Pour atteindre cet objectif, les auteurs identifient trois axes de travail :

**O1 - Abstraction de langage**  
Fournir une interface de programmation simple et flexible qui cache la complexité du prompt engineering aux développeurs.

**O2 - Extraction de sémantique**  
Développer des mécanismes d'extraction des informations sémantiques du code nécessaires à la génération automatique de prompts.

**O3 - Système d'exécution**  
Mettre en place un système capable de combiner sémantique statique et valeurs dynamiques pour orchestrer la génération de prompts et l'interprétation des résultats.

## 2.2. Défis techniques

Ces objectifs posent quatre défis techniques :

**C1 - Simplicité et flexibilité de l'abstraction**  
L'abstraction doit supporter différentes méthodes d'intégration LLM tout en restant accessible aux développeurs. La difficulté est de trouver un équilibre entre une interface simple qui réduit la courbe d'apprentissage et une flexibilité suffisante pour couvrir divers cas d'usage à différents endroits du code.

**C2 - Sélection des informations sémantiques**  
Inclure tout le code source dans les prompts serait coûteux en tokens, il faut donc identifier et extraire uniquement les informations sémantiques pertinentes. Cette tâche est complexifiée par la dispersion de ces informations dans plusieurs fichiers, ce qui requiert une analyse de la codebase.

**C3 - Accès au contexte d'exécution**  
Le système doit accéder aux valeurs des variables à l'exécution pour les combiner avec la sémantique statique. Si cet accès est direct pour les paramètres de fonctions, il est plus complexe pour les méthodes d'objets qui nécessitent également l'accès aux attributs de l'instance.

**C4 - Robustesse face aux sorties LLM**  
Les LLMs produisent des sorties non-déterministes qui peuvent dévier des formats attendus. Le système doit parser ces sorties, gérer les erreurs et implémenter des mécanismes de retry lorsque nécessaire.

## 2.3. Architecture de la solution

Pour répondre à ces objectifs, le paradigme Meaning-Typed Programming (`MTP`) repose sur trois composants :

1. **L'opérateur `by`** : une abstraction au niveau du langage Jac qui permet l'intégration de fonctionnalités LLM (répond à **O1**).

2. **MT-IR (Meaning-Typed Intermediate Representation)** : une représentation intermédiaire générée lors de la compilation qui capture les informations sémantiques du code (répond à **O2**).

3. **MT-Runtime** : un moteur d'exécution qui gère l'intégration avec les LLMs, combinant les informations sémantiques avec les valeurs au runtime pour générer les prompts et interpréter les sorties (répond à **O3**).

Le système MTP fonctionne selon un pipeline en deux phases. Lors de la compilation, MT-IR extrait les informations sémantiques du code source. À l'exécution, MT-Runtime utilise ces informations combinées aux valeurs dynamiques pour générer les prompts, invoquer le LLM, et interpréter les résultats.