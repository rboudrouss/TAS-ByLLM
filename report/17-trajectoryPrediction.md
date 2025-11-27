# 3. Prototype: byllmEMMA - Prédiction de trajectoire de véhicule

L'objectif de notre prototype est de prédire la trajectoire future d'un véhicule en utilisant sa vitesse et sa courbure passées ainsi qu'une image capturée par une caméra frontale.

L'idée est venue de la méthode [LightEMMA](https://github.com/michigan-traffic-lab/LightEMMA) (End to End Multi-Modal Attention for Vehicle Trajectory Prediction) qui utilise des modèles multimodaux pour prédire des trajectoires d'un véhicule à partir de sa caméra frontale et d'informations temporelles sur l'ego du véhicule. C'est une tâche complexe qui nécessite un prompt engineering poussé pour obtenir un résultat correct. Ce projet permettra de pousser les capacités sémantiques de byllm pour une tâche relativement complexe.

## 3.1. Méthode

Deux objectifs principaux dans notre projet :

* répliquer le comportement de [LightEMMA](https://github.com/michigan-traffic-lab/LightEMMA) sur une frame d'une situation de conduite

* comparer les resultats d'une implémentation en Jac avec byllm par rapport à une implémentation classique en Python.

Là où le modèle utilise la librairie Transformers pour charger et inférer un modèle multimodal, nous allons utiliser byllm interrogeant un modèle local via Ollama. L'implémentation classique utilisera la librairie Ollama pour faire des appels au modèle local.

LightEMMA requète deux fois le VLM pour intégrer une description de la scène et des intentions de conduite dans le prompt final. Nous utiliserons un seul prompt unique pour la méthode traditionnelle.

Bien que la philosophie de **byllm** soit d'extraire la sémantique du code pour former un prompt automatiquement, le langage Jac propose le type ```Semstrings``` qui permet d'inclure des informations supplémentaires au sujet de variables, fonctions, attributs ou objets. Nous comparerons les résultats avec et sans ces Semstrings pour évaluer leur impact ; nous testerons également une version contenant un prompt manuel passé à la fonction de prédiction comme attribut d'objet.

Formellement, on définit $P$ comme la fonction de prédiction de trajectoire future :

$$
P(I,\ \mathbf{v}_{1:t},\ \boldsymbol{\kappa}_{1:t},\ s)
= \bigl[(v_{t+1},\kappa_{t+1}),\dots,(v_{t+6},\kappa_{t+6})\bigr],
$$

- $I$ : image frontale
- $\mathbf{v}_{1:t}$ : vitesses passées
- $\boldsymbol{\kappa}_{1:t}$ : courbures passées
- $s$ : contexte supplémentaire optionnel (Semstrings ou prompt manuel)

et la sortie est une liste de 6 tuples (driving actions) représentant la vitesse et la courbure prévues pour les 3 prochaines secondes (0,5 s d'intervalle) :

$$
(v_{t+k},\ \kappa_{t+k}) \in \mathbb{R}^2, \qquad k = 1,\dots,6.
$$

- Pour faciliter la notation, on définit :
    - $P_{ss}$ : version de $P$ avec Semstrings (contexte sémantique ajouté)
    - $P_{pm}$ : version de $P$ avec prompt manuel (prompt passé comme attribut)
    - $P_{def}$ : version de $P$ sans contexte supplémentaire (défaut, philosophie du papier original)
    - $P_{py}$ : implémentation Python classique sans byllm

Bien que $P_{pm}$ et $P_{py}$ utilisent le même prompt, il est interessant de comparer leur robustesse lors de l'evaluation de l'output.

### Métriques
Pour évaluer les performances de chaque version, nous convertissons l’output en une liste de waypoints et utilisons les métriques suivantes :

**Précision de la trajectoire**

- **ADE** (Average Displacement Error) : erreur moyenne entre les positions prédites et réelles (voir Figure \ref{fig:fede}).
- **FDE** (Final Displacement Error) : erreur sur la position finale.
- **L2 error** : distance moyenne point à point entre prédictions et valeurs réelles.

**Efficacité**

- Temps d’inférence moyen par appel de fonction.
- Nombre de lignes de code (LoC) pour chaque version ($P$ et structures de données seulement ; ce n'est pas la même métrique utilisée dans l'article).

**Robustesse**

- Pourcentage d’erreurs de parsing de la sortie.


\begin{figure}[tb]
\centering
\includegraphics[width=0.4\textwidth]{imgs/FEDE.png}
\caption{Comparaison ADE/FDE. Source : Rethinking Trajectory Forecasting Evaluation - Boris Ivanovic, Marco Pavone}
\label{fig:fede}
\end{figure}

## 3.2 Choix du modèle

**Modèle multimodal local qwen2.5VL_8b via Ollama.**

Assez petit pour inférer rapidement sur une machine locale, c'est également un modèle déjà benchmarké pour des tâches de prédiction de trajectoire sur le même dataset.

Par contrainte temporelle, nous n'avons pas pu tester d'autres modèles, mais il serait intéressant de comparer les performances de qwen2.5VL_8b avec des modèles plus puissants, je pense au modèle [Cosmos-Reason1-7B](https://huggingface.co/IDEA-CCNL/Cosmos-Reason1-7B) qui a montré des performance superieure sur ce genre de tache avec un prompt unique (Figure ).

![\label{fig:frame9}](./image-2.png)

\begin{figure}[tb]
\centering
\includegraphics[width=0.2\textwidth]{image-2.png}
\caption{benchmark de lightEMMA sur le dataset nuScenes (10 scènes de 12 frames chacune) qui compare Qwen2.5 VL-7B-Instruct et Cosmos-Reason1-7B avec different systeme de prompt. Source : Effectué par moi même}
\label{fig:img4}
\end{figure}

## 3.2. Choix d'Évaluation

### Données d'évaluation

Nous utilisons une frame du dataset [nuScenes](https://www.nuscenes.org/) avec la liste de ses vitesses et courbures passées pendant 3 s à 0,5 s d'intervalle (6 valeurs) ainsi qu'une photo capturée par la caméra avant du véhicule (voir Figure \ref{fig:frame}).

50 essais ont été réalisés pour $P$, $P_{pm}$, $P_{def}$ et $P_{py}$.

\begin{figure}[h!]
\centering
\includegraphics[width=0.4\textwidth]{imgs/camfront_scene_123_frame0.jpg}
\captionof{figure}{Image used.}
\label{fig:frame}
\end{figure}

## 3.3 Implémentation

\begin{figure}[tb]
\centering
\includegraphics[width=0.2\textwidth]{imgs/image-4.png}
\caption{Implementation Python}
\label{fig:img4}
\end{figure}

\begin{figure}[tb]
\centering
\begin{minipage}[t]{0.32\textwidth}
\centering
\includegraphics[width=\textwidth]{imgs/image-1.png}
\caption{Implementation de $P_{def}$}
\label{fig:img1}
\end{minipage}\hfill
\begin{minipage}[t]{0.32\textwidth}
\centering
\includegraphics[width=\textwidth]{imgs/image-2.png}
\caption{Implementation de $P_{ss}$}
\label{fig:img2}
\end{minipage}\hfill
\begin{minipage}[t]{0.32\textwidth}
\centering
\includegraphics[width=\textwidth]{imgs/image-3.png}
\caption{Implementation de $P_{pm}$}
\label{fig:img3}
\end{minipage}
\end{figure}

Fig \ref{fig:img1}, \ref{fig:img2} et \ref{fig:img3} représentent respectivement l'implémentation de $P_{def}$, $P_{ss}$ et $P_{pm}$ en Jac avec byllm, tandis que \ref{fig:img4} montre l'implémentation de $P_{py}$ en Python classique. La simplicité de l'implémentation en Jac est évidente comparée à la version Python, qui nécessite en plus de mettre en place un parser.

De \ref{fig:img1} à \ref{fig:img3}, on remarque des différences dans le naming des variables et le typage ; nous avons essayé de rendre le code sémantiquement plus explicite pour maximiser la compréhension de byllm.

## 3.4. Illustration de la formation du prompt par MT-IR et MT-runtime

Selon le papier MTP, un dictionnaire MT-IR est généré a la compilation associant chaque appel à `By` à son arbre sémantique (\ref{fig:mtir}).

Ici l'arbre est construit recursivement a partir de la signature, des inputs et outputs de la fonction recupéré via l'AST du code source(\ref{fig:ast}). l'arbre differe legerement si by est utilisé sur une fonction, une méthode ou une classe(\ref{fig:algo}).

MT-IR est ensuite utilisé pour generer un prompt durant le runtime (\ref{fig:prompt}).

\begin{figure}[tb]
    \centering

    % --- (a)
    \begin{subfigure}{0.48\textwidth}
        \centering
        \includegraphics[width=\linewidth]{ast.png}
        \caption{Analyse et extraction AST}
        \label{fig:ast}
    \end{subfigure}
    \hfill
    % --- (b)
    \begin{subfigure}{0.48\textwidth}
        \centering
        \includegraphics[width=\linewidth]{mtir.png}
        \caption{MT-IR généré pour l'appel By}
        \label{fig:mtir}
    \end{subfigure}

    \vspace{0.4cm}

    % --- (c)
    \begin{subfigure}{0.48\textwidth}
        \centering
        \includegraphics[width=\linewidth]{prompt.png}
        \caption{Prompt généré par MT-runtime}
        \label{fig:prompt}
    \end{subfigure}
    \hfill
    % --- (d)
    \begin{subfigure}{0.48\textwidth}
        \centering
        \includegraphics[width=\linewidth]{image-8.png}
        \caption{Algorithme de construction de MT-IR}
        \label{fig:algo}
    \end{subfigure}

    \caption{Étapes successives de la construction et de l’utilisation de MT-IR}
    \label{fig:mtir-global}
\end{figure}

## 3.4. Résultats

Tableau récapitulatif (moyennes sur 50 essais sur un Apple M5 (10) @ 4.61 GHz avec 16 Go de RAM) :

| Métrique                              | $P_{def}$ | $P_{ss}$ | $P_{pm}$  | $P_{py}$ |
|---------------------------------------|------:|------:|------:|-----:|
| mean  ADE                         | 5.81  | 5.54  | 2.82  | 2.39 |
| mean FDE                          | 9.13  | 8.95  | 5.12  | 4.57 |
| mean L2 error                     | 5.81  | 5.54  | 2.82 | 2.39 |
| Temps d'inférence moyen (ms)          | 134.1| 114.2| 108.1   | 11.48  |
| Taux d'erreurs de typage (%)         | 4%    | 3%    | 0.8%  | 0.2%   |
| Lignes de code (LoC)                  | 16    | 26   | 28   | 73  |

Par exemple, on peux visualiser d'une trajectoire (\ref{fig:results}) avec un mean ADE de 2.39 m.

**Temps d'inférence moyen en ms** : 10 fois plus court pour $P_{py}$ que pour les versions avec byllm. Peut s'expliquer par un biais matériel (byLLM ne supporte peut-etre pas l'architecture CUDA).

***Displacement Errors (ADE, FDE, L2)** : $P_{py}$ et $P_{pm}$ ont des performances similaires, bien meilleures que $P_{def}$ et $P_{ss}$. Même si la philosophie de byllm n'est pas exactement respectée, il semble que dans ce cas précis, un prompt manuel bien conçu peut considérablement améliorer les performances sans avoir à gérer le parsing de la sortie. $P_{def}$ obtient les moins bonnes performances, mais le fait que ses résultats soient très proches de ceux de $P_{ss}$ qui contient beacoup d'information additionnelle amène à s’interroger sur le rôle réel des Semstrings dans la synthèse du prompt.

**Taille du code (LoC)** : de loin la plus petite pour les versions byllm, montrant la simplicité d'implémentation du paradigme.

Avec byllm, la frontière entre prompt engineering et "semantic coding engineering" devient parfois floue. On tente de créer des variables et structures de données très spécifiques pour guider la génération du prompt et d'ajouter des indications sémantiques, mais cela ne garantit pas des performances optimales. En effet, pour des tâches complexes comme la prédiction de trajectoire via VLM, la sémantique du code ne semble pas suffisante pour générer un prompt efficace pour un modèle de taille modeste comme qwen2.5VL_8b.

Ou bien mon implémentation en Jac présente certaines coding practices peu adaptées, ce qui a pu empêcher d’exploiter pleinement le potentiel de byllm. Des essais supplémentaires en variant les conventions de nommage seraient nécessaires pour confirmer ou invalider cette hypothèse.


\begin{figure}[tb]
\centering
\includegraphics[width=0.5\textwidth]{image.png}
\caption{Exemple de visualisation des résultats (comparaison des trajectoires prédites (bleu clair) et réelles (bleu foncé) pour une itération).}
\label{fig:results}
\end{figure}