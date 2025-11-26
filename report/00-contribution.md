
# Organisation du rapport

Le rapport est organisé en 3 parties :

- **Partie I : Synthèse de l’article MTP**  
Synthèse de l'article "MTP: A Meaning-Typed Language Abstraction for AI-Integrated Programming" (\url{https://dl.acm.org/doi/10.1145/3763092})

\vspace{0.2cm}

- **Partie II – Contribution personnelle : esquisse de formalisation et vérification de types pour ByLLM**  
Cette partie présente une formalisation abstraite du paradigme MTP indépendante du langage Jac, incluant des garanties de sûreté.

\vspace{0.2cm}

- **Partie III – Contribution personnelle : jacEMMA**  
Cette partie décrit des example d'utilisation de byllm et une implémentation personnelle d’un système de prédiction de trajectoire pour véhicules autonomes utilisant ByLLM et Jac. Inspirée par [LightEMMA](https://github.com/michigan-traffic-lab/LightEMMA) et une version personnelle de LightEMMA produite durant un stage à l'université d'Aalto (supervisée par Azam Shoabib — article non encore disponible).
   - Le principe de LightEMMA est repris avec un seul prompt. Mon travail en stage a démontré qu'un seul prompt offrait des performances comparables à plusieurs prompts pour certains modèles, notamment les modèles Cosmos de NVIDIA ; pour les modèles Qwen, elles sont légèrement inférieures, mais correctes.
   - Le seul code repris de LightEMMA concerne certaines fonctions de `utils.py`, comme la conversion des driving intents en waypoints.

Toutes nos contributions peuvent être trouvées dans le dépôt GitHub suivant : \url{https://github.com/rboudrouss/TAS-ByLLM}

Vous trouverez aussi ici le lien vers un fork de JacLang contenant l'ajout d'une commande `jac tools ir semantic` qui permet de visualiser le registre sémantique généré par le MT-IR : \url{https://github.com/rboudrouss/jaseci}