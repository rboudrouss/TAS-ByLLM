# 3. Propriétés

## 3.1. Type Safety

Montrons que le système de type de MTP garantit la sûreté de type. Plus précisément, montrons que pour tout programme $P$ typable, l'exécution de $P$ ne lève jamais d'erreur de type. Pour ce faire, nous devons montrer la progression et la préservation du typage.

Pour cette démonstration nous supposons que les LLMs sont stables et que la validation réussit toujours. Donc que la règle $\beta$-ByLLM-Fail ne peut pas se produire.

### 3.1.1. Progression

Nous devons montrer que si $\vdash t : T$ et $t$ est fermé alors soit $t$ est une valeur, soit il existe $t'$ tel que $t \to t'$. 

Par induction sur la forme de $t$ :

1. **Cas $t$ est une constante** : $t$ est une valeur de type B avec $B \in \{Int, Str, Bool, Float, None\}$.
2. **Cas $t = \lambda x. e$** : $t$ est une valeur.
3. **Cas $t = ((\lambda x:\tau_1. e: \tau_2) \text{ by } m)$** : $t$ est une valeur de type $\tau_1 \to \tau_2$.
4. **Cas $t = [e_1, \ldots, e_n]$** : Par hypothèse d'induction :
   - Soit $\exists k$ tel que $e_k \to e_k'$, auquel cas nous pouvons réduire avec $\mu_{\text{List}}$.
   - Soit $\forall k$, $e_k$ est une valeur, auquel cas $t$ est une valeur.
5. **Cas $t = {l_1 = e_1, \ldots, l_n = e_n}$** : Par hypothèse d'induction :
   - Soit $\exists k$ tel que $e_k \to e_k'$, auquel cas nous pouvons réduire avec $\mu_{\text{Record}}$.
   - Soit $\forall k$, $e_k$ est une valeur, auquel cas $t$ est une valeur.
6. **Cas $t = e_1.l$** : on a donc $\vdash e_1 : \text{Record}\{l_i:\tau_i\}_{i \in I}$. Par hypothèse d'induction, soit :
   - $e_1 \to e_1'$, auquel cas nous pouvons réduire avec $\xi_{\text{Record}}$.
   - $e_1$ est une valeur, auquel cas $t$ est une valeur.
7. **Cas $t = e_1\ e_2$** : on a donc $\vdash e_1 : \tau_1 \to \tau_2$ et $\vdash e_2 : \tau_1$. Donc soit :
   - $e_1$ est d'expression $\lambda x. e$, donc par hypothèse d'induction :
     - Soit $e_1$ et $e_2$ sont des valeurs, auquel cas nous pouvons réduire avec $\beta$-réduction.
     - Soit $e_2 \to e_2'$, auquel cas nous pouvons réduire avec $\mu_2$.
     - Soit $e_1 \to e_1'$, auquel cas nous pouvons réduire avec $\mu_1$.
     - Soit les deux derniers cas se cumulent, auquel cas nous pouvons réduire avec $\mu_1$ ou $\mu_2$.
   - $e_1$ est d'expression $((\lambda x:\tau_1. e: \tau_2) \text{ by } m)$, donc par hypothèse d'induction :
     - Soit $e_1$ et $e_2$ sont des valeurs, auquel cas nous pouvons réduire soit avec `E-ByLLM-Success`.
     - Les autres cas sont les mêmes que pour le cas précédent.
    

### 3.1.2. Préservation du typage

Nous devons montrer que si $\Gamma; M \vdash t : \tau$ et $t \to t'$ alors $\Gamma; M \vdash t' : \tau$.

On pose le lemme suivant :

**Lemme de substitution** : Si $\Gamma, x:\tau_1; M \vdash e : \tau_2$ et $\Gamma; M \vdash v : \tau_1$, alors $\Gamma; M \vdash e[v/x] : \tau_2$.

Par induction sur la dérivation de $t \to t'$ :

1. **Cas $\beta$-réduction** : $(\lambda x:\tau_1. e)\ v \to e[v/x]$ avec $\Gamma; M \vdash \lambda x:\tau_1. e : \tau_1 \to \tau_2$ et $\Gamma; M \vdash v : \tau_1$.

   Par inversion de T-Abs, on a $\Gamma, x:\tau_1; M \vdash e : \tau_2$.

   Par le lemme de substitution, $\Gamma; M \vdash e[v/x] : \tau_2$.

2. **Cas $\mu_1$-transformation** : $e_1\ e_2 \to e_1'\ e_2$ avec $e_1 \to e_1'$.

   On a $\Gamma; M \vdash e_1 : \tau_1 \to \tau_2$ et $\Gamma; M \vdash e_2 : \tau_1$.

   Par hypothèse d'induction, $\Gamma; M \vdash e_1' : \tau_1 \to \tau_2$.

   Par T-App, $\Gamma; M \vdash e_1'\ e_2 : \tau_2$.

3. **Cas $\mu_2$-transformation** : similaire à $\mu_1$.

4. **Cas $\mu_{\text{List}}$-transformation** : $[e_1, \ldots, e_i, \ldots, e_n] \to [e_1, \ldots, e_i', \ldots, e_n]$ avec $e_i \to e_i'$.

   On a $\Gamma; M \vdash e_j : \tau$ pour tout $j \in \{1, \ldots, n\}$.

   Par hypothèse d'induction, $\Gamma; M \vdash e_i' : \tau$.

   Par T-List, $\Gamma; M \vdash [e_1, \ldots, e_i', \ldots, e_n] : \text{List}\langle\tau\rangle$.

5. **Cas $\mu_{\text{Record}}$-transformation** : similaire à $\mu_{\text{List}}$.

6. **Cas $\xi_{\text{Record}}$-congruence** : $e.l \to e'.l$ avec $e \to e'$.

   On a $\Gamma; M \vdash e : \text{Record}\{l_i:\tau_i\}_{i \in I}$ avec $l \in \{l_i\}_{i \in I}$.

   Par hypothèse d'induction, $\Gamma; M \vdash e' : \text{Record}\{l_i:\tau_i\}_{i \in I}$.

   Par T-Proj, $\Gamma; M \vdash e'.l : \tau_l$.

7. **Cas $\beta$-ByLLM-Success** : $((\lambda x:\tau_1. e : \tau_2)\ \text{by } m)\ v \to v'$ où $v' = \text{validate}(\text{invoke\_llm}(m, \lambda x:\tau_1. e, v, \llbracket \tau_2 \rrbracket), \tau_2)$.

   On a $\Gamma; M \vdash (\lambda x:\tau_1. e : \tau_2)\ \text{by } m : \tau_1 \to \tau_2$ et $\Gamma; M \vdash v : \tau_1$.

   Par T-App, le type de retour est $\tau_2$.

   Par définition de $\text{validate}$, si la validation réussit, alors $v'$ est bien typé selon $\tau_2$ (via Pydantic).

   Donc $\Gamma; M \vdash v' : \tau_2$.


*Preuve* : Par induction sur la dérivation de $\Gamma, x:\tau_1; M \vdash e : \tau_2$.

## 3.2. Soundness de la traduction type-schéma

Au-delà de la sûreté de type classique, le système MTP doit garantir la **correspondance sémantique** entre trois niveaux d'abstraction : les types déclarés statiquement, les schémas JSON générés pour contraindre les LLMs, et la validation des sorties à l'exécution. Cette section établit formellement que la traduction $\llbracket\cdot\rrbracket$ préserve la sémantique des types et est utilisée de manière uniforme à travers toutes les phases du système.

Clarifions d'abord la nature de la relation $\llbracket\cdot\rrbracket$ : il ne s'agit pas d'une règle de réduction opérationnelle (comme $\to$), mais d'une **fonction de traduction statique** qui associe à chaque type un schéma JSON. Cette fonction est utilisée à deux moments distincts : lors du typage (règle T-ByLLM) pour vérifier que les types peuvent être traduits, et lors de l'exécution (règles $\beta$-ByLLM-Success et $\beta$-ByLLM-Fail) pour générer les schémas passés au LLM. La soundness du système repose sur le fait que **la même fonction $\llbracket\cdot\rrbracket$ est utilisée partout** et qu'elle capture fidèlement la sémantique des types.

### 3.2.1. Propriétés de la fonction de traduction

Nous établissons d'abord que $\llbracket\cdot\rrbracket$ est une fonction totale et déterministe, garantissant qu'elle peut être utilisée de manière fiable dans toutes les phases du système.

**Lemme 1 (Totalité de la traduction)** : Pour tout type $\tau$ bien formé utilisable dans une expression $(\lambda x:\tau_1. e : \tau_2)\ \text{by } m$ bien typée selon T-ByLLM, il existe un schéma JSON $\llbracket\tau\rrbracket$.

*Preuve* : Par construction de la règle T-ByLLM, qui exige explicitement que $\llbracket\tau_1\rrbracket$ et $\llbracket\tau_2\rrbracket$ existent. La fonction $\llbracket\cdot\rrbracket$ est définie inductivement sur la structure des types (section 2.2), couvrant tous les types de base $B$ et les constructeurs de types (List, Record). Par induction structurelle sur $\tau$ :

- **Cas de base** : Pour tout type de base $B \in \{\text{int}, \text{str}, \text{bool}, \text{float}, \text{None}\}$, $\llbracket B \rrbracket$ est défini explicitement.
- **Cas inductif** :
  - Pour $\text{List}\langle\tau'\rangle$, si $\llbracket\tau'\rrbracket$ existe par hypothèse d'induction, alors $\llbracket\text{List}\langle\tau'\rangle\rrbracket$ existe.
  - Pour $\text{Record}\{l_i:\tau_i\}_{i \in I}$, si $\llbracket\tau_i\rrbracket$ existe pour tout $i \in I$ par hypothèse d'induction, alors $\llbracket\text{Record}\{l_i:\tau_i\}_{i \in I}\rrbracket$ existe.

**Lemme 2 (Déterminisme de la traduction)** : Pour tout type $\tau$, la fonction $\llbracket\cdot\rrbracket$ produit un unique schéma JSON.

*Preuve* : Par induction sur la structure de $\tau$. Chaque cas de la définition de $\llbracket\cdot\rrbracket$ (section 2.2) est une fonction déterministe qui associe à chaque type exactement un schéma JSON. Il n'y a pas d'ambiguïté dans la définition.

Ces deux lemmes garantissent qu'il n'existe pas de désynchronisation entre le type annoté par le développeur et le schéma JSON transmis au LLM. Pour un type donné, le schéma généré est toujours identique, quelle que soit la phase (typage ou exécution).

### 3.2.2. Soundness de la validation

La deuxième garantie établit que la validation des sorties LLM préserve la conformité aux types, c'est-à-dire que les schémas JSON capturent fidèlement la sémantique des types MTP.

**Lemme 3 (Soundness de la validation)** : Si $\text{validate}(\text{json\_str}, \tau) = v$ alors $\vdash v : \tau$.

*Preuve* : La fonction $\text{validate}$ est implémentée via Pydantic, qui effectue une vérification structurelle complète basée sur le schéma $\llbracket\tau\rrbracket$. Nous montrons par induction sur la structure de $\tau$ que toute valeur acceptée par le schéma $\llbracket\tau\rrbracket$ est bien typée selon $\tau$ :

- **Cas de base** : Pour les types de base $B$, la validation vérifie que la valeur JSON correspond au type primitif attendu (entier pour int, chaîne pour str, etc.). Si la validation réussit, alors $v$ est bien une constante de type $B$ par construction.
- **Cas inductif** :
  - Pour $\text{List}\langle\tau'\rangle$, le schéma $\llbracket\text{List}\langle\tau'\rangle\rrbracket$ exige un tableau JSON dont chaque élément satisfait $\llbracket\tau'\rrbracket$. La validation applique récursivement la validation à chaque élément selon $\tau'$. Par hypothèse d'induction, chaque élément validé est de type $\tau'$, donc $v$ est de type $\text{List}\langle\tau'\rangle$ par T-List.
  - Pour $\text{Record}\{l_i:\tau_i\}_{i \in I}$, le schéma $\llbracket\text{Record}\{l_i:\tau_i\}_{i \in I}\rrbracket$ exige un objet JSON possédant exactement les champs $l_i$ avec des valeurs satisfaisant $\llbracket\tau_i\rrbracket$. Par hypothèse d'induction, chaque champ validé est de type $\tau_i$, donc $v$ est de type $\text{Record}\{l_i:\tau_i\}_{i \in I}$ par T-Record.

Ce lemme établit qu'il n'existe pas de faux positifs dans la validation : toute sortie LLM acceptée par le système est garantie conforme au type déclaré. Autrement dit, les schémas JSON générés par $\llbracket\cdot\rrbracket$ capturent exactement la sémantique des types MTP.

### 3.2.3. Uniformité de la traduction

La troisième garantie établit que les vérifications statiques et dynamiques utilisent la même fonction de traduction, assurant ainsi qu'il n'y a pas de divergence entre les contraintes vérifiées au typage et celles appliquées à l'exécution.

**Lemme 4 (Uniformité statique-dynamique)** : Pour toute expression $(\lambda x:\tau_1. e : \tau_2)\ \text{by } m$ bien typée selon T-ByLLM, les schémas utilisés dans les règles de réduction $\beta$-ByLLM-Success et $\beta$-ByLLM-Fail sont exactement $\llbracket\tau_1\rrbracket$ et $\llbracket\tau_2\rrbracket$.

*Preuve* : Par inspection des règles de typage et de réduction :

- La règle T-ByLLM vérifie l'existence de $\llbracket\tau_1\rrbracket$ et $\llbracket\tau_2\rrbracket$ lors du typage statique.
- Les règles $\beta$-ByLLM-Success et $\beta$-ByLLM-Fail utilisent explicitement $\llbracket\tau_2\rrbracket$ dans l'invocation $\text{invoke\_llm}(m, \lambda x:\tau_1. e, v, \llbracket\tau_2\rrbracket)$ et dans la validation $\text{validate}(\text{json\_str}, \tau_2)$.
- Par déterminisme de $\llbracket\cdot\rrbracket$ (Lemme 2), pour un type $\tau_2$ donné, le schéma $\llbracket\tau_2\rrbracket$ calculé lors du typage est identique à celui utilisé lors de l'exécution.
- Aucune autre fonction de traduction n'est utilisée dans le système.

Ce lemme garantit qu'il n'existe pas de divergence entre ce qui est vérifié statiquement et ce qui est appliqué dynamiquement. Les contraintes de types sont uniformes à travers toutes les phases d'exécution.

### 3.2.4. Théorème principal de soundness

Nous établissons maintenant le résultat principal qui combine les garanties précédentes et montre que le système MTP est sound de bout en bout.

**Théorème (Soundness de bout en bout)** : Pour toute expression $e$ bien typée avec $\Gamma; M \vdash e : \tau$ contenant des sous-expressions `by m`, si $e \to^* v$ où $v$ est une valeur et aucune réduction n'a produit de ValidationError, alors $\Gamma; M \vdash v : \tau$.

*Preuve* : Par induction sur le nombre de pas de réduction $e \to^* v$ :

- **Cas de base** : Si $e = v$, alors le résultat est immédiat par hypothèse.
- **Cas inductif** : Si $e \to e' \to^* v$, alors :
  - Par préservation du typage (Théorème 3.1.2), $\Gamma; M \vdash e' : \tau$.
  - Si la réduction $e \to e'$ utilise $\beta$-ByLLM-Success, alors :
    - Le schéma utilisé est $\llbracket\tau_2\rrbracket$ par construction de la règle.
    - Par le Lemme 4 (uniformité), ce schéma est identique à celui vérifié lors du typage.
    - La validation $\text{validate}(\text{json\_str}, \tau_2)$ produit une valeur $v'$.
    - Par le Lemme 3 (soundness de la validation), $\Gamma; M \vdash v' : \tau_2$.
  - Si la réduction $e \to e'$ utilise une autre règle, la préservation du typage s'applique directement.
  - Par hypothèse d'induction sur $e' \to^* v$, on obtient $\Gamma; M \vdash v : \tau$.

Ce théorème établit que le système MTP garantit la sûreté de type de bout en bout, même en présence d'appels LLM non-déterministes, tant que ces appels réussissent leur validation. Les erreurs de type ne peuvent survenir que lors d'échecs de validation explicites (ValidationError), qui sont détectés et signalés par le système avant toute utilisation de la valeur invalide. La traduction $\llbracket\cdot\rrbracket$ assure que les contraintes de types sont fidèlement représentées dans les schémas JSON et uniformément appliquées à travers toutes les phases du système.
