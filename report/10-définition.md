# 2. Formalisation du système MTP

## 2.1. Syntaxe

La syntaxe de MTP est définie par l'ensemble des expressions suivantes :

$$
\text{Types } \tau ::= \ B \mid \tau_1 \to \tau_2 \\
\ \mid \text{List}\langle\tau\rangle \mid \text{Record}\{\ell_i:\tau_i\}_{i \in I}
$$

où $B$ représente les types de (int, str, bool, float).


$$
\begin{aligned}
\text{Expressions } e ::= &\ x \mid c \mid \lambda x:\tau. e \mid e_1\ e_2 \mid \text{let } x = e_1 \text{ in } e_2 \\
&\ \mid (\lambda x:\tau_1. e : \tau_2)\ \text{by } m \\
&\ \mid \{l_i = e_i\}_{i \in I} \mid e.l \\
&\ \mid [e_1, \ldots, e_n] \mid \{e_1 : e_1', \ldots, e_n : e_n'\} \\
\end{aligned}
$$

Notez que byLLM supporte plus de types que ceux définis ci-dessus (par exemple, les énums, les dictionnaires, les tuples, etc.). Cependant, pour simplifier la formalisation, nous nous contenterons de ces types.  
Les types unions sont aussi supportés, cependant la formalisation est plus complexe nécessitant des sum types que nous ne traiterons pas ici.

Les contextes de typages sont définis comme suit :

- $\Gamma$ est un contexte de typage pour les variables, c'est-à-dire un ensemble de paires $(x, \tau)$ où $x$ est une variable et $\tau$ son type.
- $M$ est un contexte de modèles, c'est-à-dire un ensemble de modèles $m$ disponibles.

Notez aussi que nous ne typons pas les modèles eux-mêmes. En effet, tous les LLMs prennent et retournent des chaînes de caractères. Notre système vérifie plutôt la cohérence entre les annotations de types et la génération de schémas JSON.

## 2.2. Relation types-schémas JSON

Posons $\llbracket\tau\rrbracket$ la relation qui associe à un type $\tau$ le schéma JSON correspondant. Cette relation est définie de la manière suivante :


$$
\begin{aligned}
\llbracket \text{int} \rrbracket &= \{\text{"type": "integer"}\} \\
\llbracket \text{str} \rrbracket &= \{\text{"type": "string"}\} \\
\llbracket \text{bool} \rrbracket &= \{\text{"type": "boolean"}\} \\
\llbracket \text{float} \rrbracket &= \{\text{"type": "number"}\} \\
\llbracket \text{None} \rrbracket &= \{\text{"type": "null"}\} \\
\llbracket \text{List}\langle\tau\rangle \rrbracket &= \{\text{"type": "array", "items": } \llbracket \tau \rrbracket\} \\
\llbracket \text{Record}\{l_i:\tau_i\}_{i \in I} \rrbracket &= \{\text{"type": "object", "properties": } \{l_i: \llbracket \tau_i \rrbracket\}_{i \in I}\}
\end{aligned}
$$

Les transformation sont directement implémentées dans la fonction `_type_to_schema` du fichier `jac-byllm/byllm/schema.py` du dépôt de JacLang.  
On remarquera que la fonction rajoute aussi des informations supplémentaires aux schémas tel que les eventuels titre et description. Ces informations sont extraites du MT-IR en string donc nous y ferons abstraction car ne risque pas de poser des problèmes de cohérence.

## 2.3. Règles de typage

Les règles de typage de MTP sont définies comme suit :

**Règles de base**

$$
\frac{x:\tau \in \Gamma}{\Gamma; M \vdash x : \tau} \text{(T-Var)}
\qquad
\frac{}{\Gamma; M \vdash c : \text{typeOf}(c)} \text{(T-B)}
$$

$$
\frac{\Gamma, x:\tau_1; M \vdash e : \tau_2}{\Gamma; M \vdash \lambda x:\tau_1. e : \tau_1 \to \tau_2} \text{(T-Abs)}
$$

$$
\frac{\Gamma; M \vdash e_1 : \tau_1 \to \tau_2 \quad \Gamma; M \vdash e_2 : \tau_1}{\Gamma; M \vdash e_1\ e_2 : \tau_2} \text{(T-App)}
$$

Pour les types de bases, nous avons une règle par type comme la règle T-B.

**Règles pour les types structurés**

Pour les records :

$$
\frac{\Gamma; M \vdash e_i : \tau_i \quad \forall i \in I}{\Gamma; M \vdash \{l_i = e_i\}_{i \in I} : \text{Record}\{l_i:\tau_i\}_{i \in I}} \text{(T-Record)}
$$

$$
\frac{\Gamma; M \vdash e : \text{Record}\{l_i:\tau_i\}_{i \in I} \quad j \in I}{\Gamma; M \vdash e.l_j : \tau_j} \text{(T-Proj)}
$$

Pour les listes homogènes :

$$
\frac{\Gamma; M \vdash e_i : \tau \quad \forall i \in \{1, \ldots, n\}}{\Gamma; M \vdash [e_1, \ldots, e_n] : \text{List}\langle\tau\rangle} \text{(T-List)}
$$

**Règle spécifique à MTP**

$$
\frac{\Gamma; M \vdash \lambda x:\tau_1. e : \tau_1 \to \tau_2 \quad m \in M \quad \llbracket \tau_1 \rrbracket \text{ existe} \quad \llbracket \tau_2 \rrbracket \text{ existe}}{\Gamma; M \vdash (\lambda x:\tau_1. e : \tau_2)\ \text{by } m : \tau_1 \to \tau_2} \text{(T-ByLLM)}
$$

Cette règle signifie que `by m` décore une fonction pour que son implémentation soit fournie par le modèle $m$. Le résultat est une fonction de même type que la fonction originale.

Les conditions décrites sont les suivantes :  
1. L'expression doit être une fonction de type $\tau_1 \to \tau_2$.  
2. Le modèle $m$ doit être connu.  
3. le type $\tau_1$ doit pouvoir être converti en un schéma JSON (pour générer le prompt).
4. le type $\tau_2$ doit pouvoir être converti en un schéma JSON (pour valider la sortie).

En pratique, byLLM supporte des fonctions avec un nombre arbitraire de paramètres. Dans notre système par curryfication, ceci revient à des fonctions de type $\tau_1 \to (\tau_2 \to (\ldots \to \tau_n))$.

## 2.4. Sémantique opérationnelle

**$\beta$ réduction**

$$
\frac{}{(\lambda x:\tau. M)\ N \to M[N/x]} \text{($\beta$-reduction)}
$$

**$\mu$ transformation**

$$
\frac{M \to M'}{M\ N \to M'\ N} \text{($\mu_1$-transformation)} \qquad \frac{N \to N'}{M\ N \to M\ N'} \text{($\mu_2$-transformation)}
$$

$$
\frac{e_k \to e_k'}{\{l_1 = e_1, \ldots, l_k = e_k, \ldots, l_n = e_n\} \to \{l_1 = e_1, \ldots, l_k = e_k', \ldots, l_n = e_n\}} \text{($\mu_{\text{Record}}$-transformation)}
$$

$$
\frac{e_i \to e_i'}{[e_1, \ldots, e_i, \ldots, e_n] \to [e_1, \ldots, e_i', \ldots, e_n]} \text{($\mu_{\text{List}}$-transformation)}
$$

**$\xi$ congruence**

$$
\frac{M \to M'}{\lambda x.M \to \lambda x.M'} \text{($\xi$-congruence)} \qquad \frac{e \to e'}{e.l \to e'.l} \text{($\xi_{\text{Record}}$-congruence)}
$$

**Réduction des invocation LLM**

De part la nature non-déterministe des LLMs, il est impossible de définir une sémantique opérationnelle déterministe pour MTP. Ici nous nous contenterons de dire que 2 réductions sont possibles :

$$
\frac{
\begin{aligned}
&v : \tau_1 \quad (\lambda x:\tau_1. e : \tau_2)\ \text{by } m : \tau_1 \to \tau_2 \\
&\text{json\_str} = \text{invoke\_llm}(m, \lambda x:\tau_1. e, v, \llbracket \tau_2 \rrbracket) \\
&v' = \text{validate}(\text{json\_str}, \tau_2)
\end{aligned}
}{((\lambda x:\tau_1. e : \tau_2)\ \text{by } m)\ v \to v'} \text{($\beta$-ByLLM-Success)}
$$

$$
\frac{
\begin{aligned}
&\text{json\_str} = \text{invoke\_llm}(m, \lambda x:\tau_1. e, v, \llbracket \tau_2 \rrbracket) \\
&\text{validate}(\text{json\_str}, \tau_2) = \text{error}
\end{aligned}
}{((\lambda x:\tau_1. e : \tau_2)\ \text{by } m)\ v \to \text{ValidationError}} \text{($\beta$-ByLLM-Fail)}
$$

où :

- $\text{invoke\_llm}(m, \lambda x:\tau_1. e, v, S)$ appelle le LLM $m$ avec :
  - Un prompt généré à partir de la fonction et de la valeur d'entrée $v$
  - Le schéma JSON $S = \llbracket \tau_2 \rrbracket$ pour contraindre la sortie
  - Retourne une chaîne JSON
- $\text{validate}(\text{json\_str}, \tau_2)$ parse et valide le JSON selon le type $\tau_2$ (via Pydantic)
