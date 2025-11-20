# 5. Conclusion et perspectives

Ce projet a permis d'explorer les capacités de byllm() pour une tâche complexe de prédiction de trajectoire multimodale. Bien que l'implémentation en Jac soit plus concise, les performances restent inférieures à une approche Python classique avec un prompt.

On se rapproche des performances de la version Python uniquement en utilisant un prompt manuel, mais est‑ce vraiment dans l'esprit de byllm() ?

L’ajout des Semantic String Definitions, qui enrichissent la sémantique du code et n’apparaissent pas dans le papier original, révèle une évolution notable par rapport à l’ambition initiale de s’affranchir du prompt engineering. On se rapproche du concept de DSPy tout en restant flexible.

Malgrès cela, il ne faut pas negliger la simplicité d'implementation et la reduction du code necessaire qui rend son utilisation bien plus agreable pour des développeurs.

A la lecture des excellents resultats des benchmarks du papier original (avec chatGPT4o), nous nous doutons que des modèles plus puissants GPT-4o pourraient nettement améliorer nos performances actuelles.

Pour les développeurs interagissant régulièrement avec des API d’IA, cette approche constitue une alternative élégante et efficace, et il est probable qu’elle gagne encore en pertinence.