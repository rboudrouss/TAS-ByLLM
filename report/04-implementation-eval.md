# 4. Implémentation et évaluation

## 4.1. Implémentation dans Jac

MTP est implémenté dans Jac, un sur-ensemble de Python développé par Jaseci Labs et distribué comme package PyPI. Jac étend Python avec de nouvelles primitives de langage tout en restant compatible avec l'écosystème Python existant. L'opérateur `by` constitue une primitive native de Jac, tandis que MT-IR et MT-Runtime sont intégrés respectivement comme passe de compilation et plugin d'exécution.

Le pipeline de compilation Jac transforme le code source en plusieurs étapes. L'AST Jac est d'abord généré, puis transformé en AST Python enrichi d'annotations de types. Durant cette transformation, une passe de compilation dédiée construit MT-IR en extrayant les informations sémantiques. Le bytecode Python standard est ensuite produit, avec MT-IR stocké séparément pour être accessible à MT-Runtime lors de l'exécution dans la machine virtuelle Python.

## 4.2. Évaluation

Les auteurs évaluent MTP selon quatre axes : la réduction de complexité du code, la précision des programmes, l'efficacité en termes de tokens et de temps d'exécution, et la robustesse face aux pratiques de codage. L'évaluation s'appuie sur une suite de 13 benchmarks couvrant diverses tâches (résolution de problèmes mathématiques, traduction, génération de contenu, raisonnement) et compare MTP aux frameworks LMQL et DSPy.

### 4.2.1. Réduction de la complexité du code

Les auteurs mesurent le nombre de lignes de code modifiées pour intégrer une fonctionnalité LLM dans un programme existant. Sur l'ensemble des benchmarks, MTP nécessite entre 2.3× et 7.5× moins de lignes que LMQL, et entre 1.3× et 10.7× moins que DSPy. Cette réduction s'explique par l'abstraction offerte par l'opérateur `by` qui élimine la construction manuelle de prompts requise par LMQL et les annotations de types détaillées imposées par DSPy.

Une étude utilisateur menée auprès de 20 développeurs confirme ces résultats quantitatifs. Les participants ont implémenté trois tâches de complexité croissante avec chaque framework. MTP obtient les meilleurs taux de réussite sur deux des trois tâches et montre la performance la plus stable. Les retours qualitatifs soulignent la simplicité de MTP, plusieurs participants notant que "le code MTP est plus court" et que "la conversion automatique entre types de données se fait facilement".

### 4.2.2. Précision des programmes

L'évaluation de la précision porte sur les 13 benchmarks avec GPT-4o, chacun exécuté 100 fois. La précision moyenne atteint 90.85% pour LMQL, 98.23% pour DSPy et 98.92% pour MTP. MTP surpasse DSPy sur 9 des 13 benchmarks, démontrant que l'automatisation du prompt engineering ne dégrade pas la qualité des résultats.

Sur le benchmark GSM8K (300 problèmes mathématiques), les auteurs observent une tendance intéressante à travers l'évolution des modèles. Avec les modèles récents (GPT-4o, Llama 3.1), la précision de MTP s'améliore continuellement tandis que celle de DSPy stagne voire régresse légèrement. Cette observation suggère que les modèles plus performants comprennent mieux la sémantique du code, réduisant le besoin de prompt engineering complexe. MTP atteint ainsi près de 90% de précision sur GPT-4o, surpassant même DSPy en mode compilé qui nécessite des exemples d'entraînement supplémentaires.

### 4.2.3. Efficacité en tokens et temps d'exécution

MTP consomme systématiquement moins de tokens que DSPy sur tous les benchmarks. Cette réduction se traduit directement par des économies de coûts d'API allant jusqu'à 4.5× sur certains benchmarks. Les prompts générés par MT-Runtime sont plus concis car MT-IR extrait uniquement les informations sémantiques pertinentes, évitant la verbosité des prompts DSPy.

Le temps d'exécution suit la même tendance. MTP obtient des accélérations allant jusqu'à 4.75× par rapport à DSPy sur certains benchmarks, grâce à la réduction du nombre de tokens à traiter par le LLM. L'overhead introduit par MT-Runtime reste minimal car la synthèse de prompts s'effectue de manière efficace.

### 4.2.4. Robustesse aux pratiques de codage

Les auteurs testent la sensibilité de MTP à la dégradation de la qualité du code en renommant progressivement les identifiants du programme de génération de niveaux. Avec 25% et 50% d'identifiants renommés de manière abrégée, MTP maintient 98% de précision. À 75% de renommage, la précision chute à 70%, et à 100% elle atteint 20%. Ces résultats montrent que MTP tolère une dégradation modérée de la qualité du code, mais que la sémantique reste essentielle au bon fonctionnement du système.