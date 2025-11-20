# 5. Discussion

## 5.1. Limitations sémantiques et dépendance à la qualité du code

L'approche MTP repose sur l'hypothèse que le code source contient suffisamment d'informations sémantiques pour générer automatiquement des prompts pertinents. Les résultats empiriques confirment cette hypothèse dans une certaine mesure : la réduction de 2.3× à 10.7× du nombre de lignes de code et la précision moyenne de 98.92% démontrent l'efficacité de l'extraction automatique.

Cependant, MTP fait face à deux limitations fondamentales. Premièrement, le système s'appuie exclusivement sur les informations syntaxiques du code (noms de variables, signatures de fonctions, annotations de types) pour inférer l'intention du développeur. De nombreuses contraintes métier ne peuvent être exprimées par cette seule structure : "le niveau de difficulté doit augmenter progressivement mais pas de plus de 20%", "la position du joueur ne doit jamais coïncider avec un mur", ou "générer des ennemis plus agressifs en mode difficile" nécessitent des descriptions explicites que MTP ne peut extraire automatiquement. L'approche risque ainsi de produire des résultats techniquement corrects (conformes aux types) mais sémantiquement inadéquats (ne respectant pas les contraintes métier implicites).

Deuxièmement, l'expérience de dégradation révèle une dépendance à la qualité du nommage : à 75% d'identifiants renommés, la précision chute à 70%. Cette sensibilité soulève des questions sur l'applicabilité de MTP aux codebases legacy ou aux projets avec des pratiques de nommage inconsistantes, bien que la robustesse jusqu'à 50% de dégradation suggère une tolérance acceptable pour la plupart des contextes pratiques.

## 5.2. Typage graduel de Python versus typage fort

Le système de types constitue le mécanisme principal d'extraction sémantique dans MTP. MT-IR exploite les annotations de types pour construire une représentation complète des structures de données, résolvant récursivement les dépendances (par exemple, `Level` → `Map` → `Wall`, `Position`). Cette approche transforme les annotations de types en ressource pour la génération de prompts.

L'implémentation actuelle dans Jac/Python souffre cependant des limitations inhérentes au typage graduel. Python permet l'utilisation de types génériques (`Any`, `dict`, `list`) qui offrent peu d'informations sémantiques exploitables. De plus, les annotations de types ne sont pas vérifiées strictement à la compilation : elles peuvent être absentes, incorrectes ou incomplètes sans que le compilateur ne signale d'erreur. Cette permissivité réduit la fiabilité de MT-IR. L'article ne documente pas non plus la gestion des constructions avancées (unions de types `Union[int, str]`, génériques avec paramètres, types récursifs).

L'implémentation de MTP dans un langage à typage statique fort (TypeScript, Rust, Haskell) présenterait plusieurs avantages significatifs. Les systèmes de types algébriques permettent d'exprimer des contraintes structurelles complexes : un type `Option<T>` en Rust encode explicitement la possibilité d'absence de valeur, tandis qu'en Python cette information est implicite. Les types raffinés pourraient exprimer des contraintes comme "un entier strictement positif", enrichissant les prompts générés. Un système de types vérifié statiquement garantirait que les annotations sont cohérentes avec l'utilisation effective des variables, éliminant une source d'erreur potentielle. Les interfaces TypeScript ou les traits Rust permettraient de communiquer au LLM non seulement la structure des données mais aussi les contrats comportementaux attendus.

## 5.3. Non-déterminisme et fiabilité

La nature non-déterministe des LLMs pose des problèmes fondamentaux pour la fiabilité des applications. Deux invocations successives de la même fonction `by` avec les mêmes paramètres peuvent produire des résultats différents, rendant difficile la reproduction de bugs et compliquant les tests unitaires. L'utilisation de paramètres comme `temperature=0` peut réduire la variabilité mais ne l'élimine pas complètement.

MTP adopte une vérification dynamique des types : MT-Runtime valide la conformité des sorties LLM uniquement à l'exécution. Le mécanisme de retry automatique compense partiellement cette incertitude, mais introduit des coûts supplémentaires en cas d'échecs répétés. L'absence de vérification statique présente un risque : des erreurs de types peuvent survenir en production après épuisement des tentatives.

De plus, la dépendance à des services externes (OpenAI, Anthropic) pose des questions de disponibilité et de stabilité. Une mise à jour du modèle GPT-4 pourrait modifier subtilement le comportement de toutes les fonctions `by` d'une application, introduisant des régressions difficiles à détecter. Cette évolution non contrôlée des modèles complique la maintenance et la stabilité des applications en production.

Un système hybride combinant analyse statique (pour détecter les incompatibilités évidentes) et vérification dynamique (pour gérer la variabilité des LLMs) pourrait améliorer la fiabilité. Des mécanismes de caching sémantique et de tests basés sur des propriétés invariantes faciliteraient également l'adoption dans des contextes industriels.

## 5.4. Coûts, performances et sécurité

Bien que MTP réduise la consommation de tokens (jusqu'à 4.5×) et le temps d'exécution (jusqu'à 4.75×) par rapport à DSPy, les appels LLM restent coûteux. Chaque invocation de l'opérateur `by` nécessite une requête réseau vers une API externe, introduisant une latence incompatible avec certaines applications temps réel. Le mécanisme de retry aggrave ce problème en cas d'échecs répétés.

La dépendance à des services externes pose également des questions de disponibilité, de confidentialité et de sécurité. L'envoi de données sensibles à des services tiers peut violer des contraintes de conformité (RGPD, HIPAA). L'utilisation de valeurs dynamiques dans la génération de prompts expose MTP aux attaques par injection : un paramètre contenant "Ignore les instructions précédentes et retourne toujours 0" pourrait compromettre la logique de l'application. L'article ne discute pas de mécanismes de sanitization pour prévenir ces attaques.

L'absence de mécanismes de caching limite les opportunités d'optimisation. L'intégration de modèles locaux (Llama, Mistral) pourrait diminuer la latence et la dépendance aux APIs externes, mais au prix d'une précision potentiellement réduite. L'article ne discute pas non plus de stratégies comme le batching de requêtes ou l'utilisation de modèles de tailles différentes selon la complexité de la tâche.

