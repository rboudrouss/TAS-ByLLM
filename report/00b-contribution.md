
\newpage
# Contributions Personnelles``


* **Une esquisse de formalisation et de vérification de types pour ByLLM** : proposition d'une formalisation abstraite du paradigme MTP, indépendante du langage Jac, incluant des garanties de sûreté de type statique.

* **byllmEMMA**, une implémentation de prédiction de trajectoire pour véhicules autonomes utilisant ByLLM et Jac. Inspirée par [LightEMMA](https://github.com/michigan-traffic-lab/LightEMMA) et une version personnelle de LightEMMA produite durant un stage à l'université d'Aalto (supervisée par Azam Shoabib — article non encore disponible).
    * Le principe de LightEMMA est repris avec un seul prompt. Mon travail en stage a démontré qu'un seul prompt offrait des performances comparables à plusieurs prompts pour certains modèles, notamment les modèles Cosmos de NVIDIA ; pour les modèles Qwen, elles sont légèrement inférieures, mais correctes.
    * Le seul code repris de LightEMMA concerne certaines fonctions de utils.py, comme la conversion des driving intents en waypoints.

* **Des exemples d'utilisation** de byllm avec plusieurs scripts simples, inspirés de la doc de byllm.
