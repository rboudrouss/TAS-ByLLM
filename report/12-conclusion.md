# 4. Conclusion de la formalisation

## 4.1. Résumé des contributions

Dans cette seconde partie, nous avons proposé une formalisation du paradigme Meaning-Typed Programming (MTP) sous la forme d'un système de types avec sémantique opérationnelle. Cette formalisation permet de raisonner de manière abstraite sur les propriétés du système, indépendamment de son implémentation dans le langage Jac.

Le système formel défini comprend une syntaxe pour les types et expressions intégrant l'opérateur `by`, une fonction de traduction type-schéma $\llbracket\cdot\rrbracket$ traduisant les types en schémas JSON, des règles de typage étendant un système classique avec la règle T-ByLLM, et une sémantique opérationnelle modélisant l'exécution via les règles de réduction classiques ($\beta$, $\mu$, $\xi$) et les règles spécifiques aux invocations LLM ($\beta$-ByLLM-Success et $\beta$-ByLLM-Fail).

Nous avons établi plusieurs propriétés fondamentales du système MTP. La sûreté de type est garantie par les propriétés de progression et de préservation (section 3.1), démontrant que toute expression bien typée et fermée est soit une valeur, soit peut être réduite, et que la réduction préserve les types. La soundness du système est assurée par quatre lemmes (section 3.2) : la totalité et le déterminisme de la fonction de traduction type-schéma, la soundness de la validation (les schémas capturent fidèlement la sémantique des types), l'uniformité de la traduction entre phases statiques et dynamiques, et le théorème principal de soundness de bout en bout établissant que les valeurs produites respectent toujours leurs types déclarés.

## 4.2. Limitations de la formalisation

Notre formalisation présente plusieurs limitations qu'il convient de reconnaître. Pour simplifier la présentation, nous avons omis plusieurs types supportés par l'implémentation réelle de byLLM, notamment les types union, les énumérations, les dictionnaires avec clés dynamiques et les tuples. De même, bien que notre syntaxe inclue le polymorphisme paramétrique ($\forall \alpha. \tau$), nous n'avons pas défini les règles de typage correspondantes, l'extension complète nécessitant de traiter la génération de schémas pour les types polymorphes.

La modélisation des LLMs reste également abstraite. Nous avons représenté l'invocation LLM comme une fonction $\text{invoke\_llm}$ sans spécifier la structure exacte des prompts générés, les mécanismes de retry ou les stratégies de gestion d'erreurs. Notre sémantique opérationnelle capture le non-déterminisme via deux règles de réduction (Success/Fail), mais ne modélise ni les distributions de probabilité sur les sorties, ni les garanties probabilistes de correction, ni l'impact des hyperparamètres.

Enfin, plusieurs aspects centraux du fonctionnement de MTP ne sont pas formalisés : le processus d'extraction des informations sémantiques (MT-IR), la transformation de la sémantique en prompts textuels, et les aspects de coûts et performances (tokens, latence, caching, batching). Ces éléments relèvent davantage de l'analyse de programmes et de l'ingénierie que de la théorie des types.

## 4.3. Extensions possibles

Plusieurs directions permettraient d'enrichir et de renforcer cette formalisation. L'ajout de types union ($\tau_1 \cup \tau_2$) et intersection ($\tau_1 \cap \tau_2$) nécessiterait des règles de sous-typage et une extension de la fonction $\llbracket\cdot\rrbracket$ pour traduire ces types en schémas JSON (via `anyOf`, `allOf`), ainsi qu'une preuve de soundness pour ces nouveaux constructeurs. Des types dépendants permettraient d'exprimer des contraintes sur les valeurs, tandis qu'un système de types avec effets ou monades modéliserait explicitement le non-déterminisme, l'I/O et les erreurs des appels LLM.

Une sémantique probabiliste, où chaque réduction $t \to t'$ serait associée à une probabilité et les propriétés de sûreté exprimées en termes probabilistes, permettrait de raisonner formellement sur la fiabilité des applications MTP. La mécanisation des preuves dans un assistant comme Coq, Isabelle ou Lean vérifierait rigoureusement leur correction et permettrait l'extraction d'une implémentation certifiée de MT-Runtime. Enfin, des analyses statiques estimant le nombre de tokens consommés ou détectant les patterns inefficaces aideraient les développeurs à optimiser leurs applications.

Une extension particulièrement intéressante serait d'établir la **completeness** de la traduction type-schéma : montrer que si une valeur $v$ est de type $\tau$, alors elle satisfait nécessairement le schéma $\llbracket\tau\rrbracket$. Combinée avec la soundness (Lemme 3), cette propriété établirait une équivalence sémantique complète entre types et schémas, renforçant ainsi les garanties du système.
