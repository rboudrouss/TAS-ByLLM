# 3. Architecture et composants de MTP

## 3.1. L'opérateur `by` : abstraction au niveau du langage

Pour répondre au défi **C1**, les auteurs introduisent l'opérateur `by` comme abstraction centrale de MTP. Sa syntaxe de base est la suivante :

```python
<code construct> by llm_ref(model_hyperparameters)
```

où `llm_ref` est une référence à un modèle de langage et `model_hyperparameters` sont des paramètres optionnels pour configurer le comportement du modèle. Cette syntaxe permet de réaliser la tâche définie à gauche de `by` en utilisant le modèle de langage spécifié à droite.

L'opérateur `by` peut être utilisé dans trois contextes différents : les définitions de fonctions, l'initialisation d'objets et les définitions de méthodes de classe. Dans la suite de ce chapitre, `M` représente l'ensemble des modèles de langage disponibles, et `eval(·)` désigne la fonction d'évaluation sémantique.

### 3.1.1. `by` dans les définitions de fonctions

Considérons une fonction $f$ avec des paramètres $p_1$, $p_2$, ..., $p_n$ de types $T_1$, $T_2$, ..., $T_n$ respectivement, et un type de retour $T_r$. En utilisant l'opérateur `by`, cette fonction peut être intégrée avec un LLM $m \in M$ ayant des hyperparamètres $\theta$ comme suit :

```python
def f(p1: T1, ..., pn: Tn) -> Tr by m(theta)  
```

À l'exécution, l'invocation de cette fonction avec les arguments $v_1, ..., v_n$ pour retourner $v_r$ de type $T_r$ est sémantiquement équivalente à :

```python
vr = eval(f(v1, ..., vn))
   = invoke-model(m, theta, f, [v1, ..., vn], [(T1, ..., Tn), Tr])  
```

Le modèle m reçoit la signature de la fonction f, les arguments effectifs ($v_1$, ..., $v_n$) avec leurs types correspondants ($T_1$, ..., $T_n$), et le type de retour attendu $T_r$. En exploitant ce contexte sémantique, le modèle peut raisonner sur le comportement attendu de la fonction et générer une sortie appropriée conforme à $T_r$.

### 3.1.2. `by` dans l'initialisation d'objets

L'opérateur `by` peut également être utilisé lors de l'initialisation d'objets pour permettre à un LLM de compléter les valeurs manquantes. Considérons une classe `C` avec des attributs $a_1$, ..., $a_n$ de types $T_1$, ..., $T_n$. Si seuls les $k$ premiers attributs sont fournis lors de l'initialisation ($k < n$), les attributs restants peuvent être complétés par $m \in M$ avec des hyperparamètres $\theta$ :

```python
C(a1, ..., ak) by m(theta)  
```

À l'exécution, lors de la création d'un tel objet, le système appelle le modèle avec le nom de la classe C, les valeurs des attributs fournis ($v_1$, ..., $v_k$), leurs types ($T_1$, ..., $T_k$) et les types des attributs restants ($T_{k+1}$, ..., $T_n$). Le modèle utilise ces informations pour générer des valeurs appropriées pour les attributs manquants afin d'instancier complètement un objet obj de type C :

```python
obj = eval(C(v1, ..., vk) by m(theta))
    = invoke-model(m, theta, C, [v1, ..., vk], [(T1, ..., Tk), (Tk+1, ..., Tn)])  
```

### 3.1.3. `by` dans les méthodes de classe

L'opérateur `by` peut aussi être utilisé pour définir des méthodes au sein d'une classe. Considérons une méthode mth au sein d'une classe C, qui prend des paramètres $p_1$, ..., $p_n$ de types $T_1$, ..., $T_n$, et retourne une valeur de type $T_r$. Cette méthode peut être implémentée en utilisant $m \in M$, configuré avec des hyperparamètres $\theta$ :

```python
class C:
    def mth(p1: T1, ..., pn: Tn) -> Tr by m(theta)  
```

À l'exécution, lorsque cette méthode est appelée sur une instance d'objet obj avec les valeurs d'entrée $v_1$, ..., $v_n$, l'évaluation pour retourner $v_r$ de type $T_r$ procède comme suit :

```python
vr = eval(obj.mth(v1, ..., vn))
   = invoke-model(m, theta, C.mth, obj, [v1, ..., vn], [C, (T1, ..., Tn), Tr])  
```

Contrairement aux appels de fonctions autonomes, les méthodes de classe ont accès à l'état interne de l'instance. Lors de l'évaluation, le modèle reçoit la signature de la méthode C.mth, l'instance d'objet obj, les valeurs d'entrée avec leurs types, et le type de retour attendu. L'objet inclut tous les attributs de la classe avec leurs valeurs courantes et leurs informations de type, permettant au modèle d'utiliser ce contexte dans son raisonnement.

### 3.1.4. Garanties comportementales

L'opérateur `by` offre deux garanties importantes grâce à MT-IR et MT-Runtime :

**Sûreté de type** : Le système vérifie systématiquement que la sortie générée par le LLM correspond bien au type $T_r$ attendu. Si la conversion échoue, une erreur de type est levée.

**Comportement temporel** : Le moment d'exécution de l'opérateur `by` dépend du contexte d'utilisation. Pour les fonctions et méthodes, l'exécution se produit uniquement lorsque la fonction est appelée. En revanche, pour l'initialisation d'objets, l'opérateur `by` s'exécute directement au moment de l'instanciation de l'objet.

## 3.2 MT-IR (Meaning-Typed Intermediate Representation)

À chaque site d'appel `by`, le système doit effectuer une analyse pour extraire les informations sémantiques du code nécessaires à la génération de prompts. Ces informations (types, signatures de fonctions) existent dans le code source mais risquent d'être perdues lors de la compilation en bytecode. Il faut donc les capturer avant cette transformation.

Les auteurs proposent MT-IR, une représentation intermédiaire qui stocke ces informations sémantiques. Comme une Intermediate Representation classique facilite la génération de code machine, MT-IR facilite la génération de prompts. À l'exécution, MT-Runtime utilise MT-IR sans accéder au code source original.

La construction de MT-IR se déroule en plusieurs phases :

### 3.2.1 Génération du registre sémantique

Lors de la compilation, le système construit un registre sémantique à partir de l'AST de chaque module. Ce registre centralise les noms de variables, fonctions, classes et leurs types. Contrairement à une table des symboles classique qui stocke uniquement les définitions, ce registre inclut aussi les usages et établit des liens entre eux.

### 3.2.2 Extraction sémantique par site d'appel `by`

Pour chaque site d'appel `by`, le système extrait d'abord les informations directes : nom de fonction/méthode/classe, types des paramètres, type de retour, modèle et hyperparamètres (lignes 3-9 de l'algorithme 1). Ces éléments correspondent aux paramètres passés à MT-Runtime selon l'équation donnée plus tôt : $(f, [v_1, ..., v_n], [(T_1, ..., T_n), T_r], m, \theta)$.

Ensuite, le système vérifie si les types sont primitifs (int, float, str). Pour les types non-primitifs, il parcourt récursivement le registre pour extraire leurs définitions complètes. Par exemple, un type `Level` peut dépendre de `Map`, qui lui-même dépend de `Wall` et `Position`. Les liens usage-définition du registre permettent cette traversée jusqu'aux types primitifs. Cette résolution récursive, implémentée par la fonction `ExtractTypeDefinition`, permet de capturer toute la hiérarchie de types nécessaire et répond au défi **C2**.

### 3.2.3 Implémentation dans le langage Jac

MTP est implémenté dans Jac, un sur-ensemble de Python distribué comme package PyPI. Jac fournit une commande CLI `jac` qui remplace le compilateur Python standard en ajoutant une phase de compilation personnalisée avant de générer du bytecode Python standard.

Le processus de compilation MTP dans Jac comporte six étapes. D'abord, un passage de compilation génère MT-IR en extrayant les éléments sémantiques de l'AST. Ces informations sont affinées par plusieurs analyses. L'AST Jac est ensuite transformé en AST Python, où les constructions `by` sont remplacées par des appels MT-Runtime. Une vérification de types MyPy enrichit ensuite MT-IR avec des informations de types supplémentaires. MT-IR est enregistré dans la bibliothèque MT-Runtime pour être disponible à l'exécution. Enfin, le bytecode Python est généré, préservant dans MT-IR les informations sémantiques qui auraient été perdues dans une compilation classique.

## 3.3 MT-Runtime : moteur d'exécution automatisé

Les programmes AI-Integrated effectuent l'inférence LLM pendant l'exécution, car le prompt nécessite à la fois les informations sémantiques et les valeurs dynamiques disponibles au moment de l'appel `by`. Cela requiert un système capable de fusionner MT-IR avec les valeurs des variables à l'exécution pour produire le prompt final. Les auteurs proposent MT-Runtime, un moteur intégré à la machine virtuelle python qui se déclenche automatiquement lors des appels `by`. Ce composant répond à l'objectif **O3** et traite les défis **C3** et **C4**.

### 3.3.1 Synthèse de prompts

À chaque appel `by`, MT-Runtime récupère la portion de MT-IR associée à ce site d'appel et l'utilise pour instancier un template de prompt. Le système construit alors un prompt qui combine la sémantique statique, les valeurs des variables pertinentes, et le type de retour attendu.

Puisque MT-Runtime s'exécute dans la machine virtuelle, il accède directement aux valeurs des variables. La sémantique provient de MT-IR tandis que les valeurs sont extraites du graphe d'objets du langage. Le prompt résultant structure ces informations de manière spécifique : le nom de la fonction et les éventuels commentaires définit l'action à réaliser, les types et leurs définitions imbriquées sont regroupés dans une section dédiée, et le schéma de sortie attendu est explicitement spécifié.

### 3.3.2 Conversion vers le type attendu

Une fois la réponse du LLM obtenue, MT-Runtime doit la transformer en une variable du type attendu. Cette étape traite le défi **C4**.

Le prompt ayant déjà demandé au modèle de produire une sortie conforme au schéma d'objet Python, MT-Runtime utilise `ast.literal_eval()` pour évaluer directement cette sortie. Par exemple, pour une variable de type `Person` avec les attributs `name: str` et `dob: str`, le LLM génère `Person(name="Albert Einstein", dob="03/14/1879")`, qui s'évalue immédiatement en un objet `Person` valide.

Si la conversion échoue, MT-Runtime construit un nouveau prompt qui signale l'erreur au modèle. Ce prompt de correction indique la sortie incorrecte et rappelle le type attendu. Le système réitère ce processus jusqu'à obtenir une sortie valide ou atteindre le nombre maximal de tentatives configuré par le développeur. Dans ce dernier cas, une exception de type est levée.
