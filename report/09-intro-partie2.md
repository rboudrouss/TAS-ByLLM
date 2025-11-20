# 1. Motivation pour la formalisation

L'implémentation de MTP dans Jac est une contribution concrète, mais elle est limitée à un seul langage. Pour généraliser la solution, il est nécessaire de la formaliser de manière indépendante du langage. Cela permettra de raisonner sur le paradigme MTP de manière abstraite et de le porter à d'autres langages.

De plus, byLLM implémente plusieurs vérifications au runtime : la génération de schémas JSON lève une exception si le type n'est pas supporté en entrée et la validation pydantic lève une exception si le type de sortie n'est pas respecté. Sauf que ces vérifications sont effectuées à l'exécution, ce qui n'est pas idéal. Dans cette deuxième partie, nous proposons une esquisse de formalisation du paradigme MTP, incluant des garanties de sûreté de type statique.
