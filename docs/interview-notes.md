# Défense en entretien

**Quel problème observé ?** Aucun doublon ou champ manquant dans les CSV ; les jointures laissent une forte couverture incomplète. C'est un résultat réel, pas un défaut fabriqué.

**Pourquoi SQLite ?** Le volume tient sur un ordinateur ; contraintes, vues et requêtes suffisent. Un cluster Spark serait inutile ici.

**Pourquoi aucune ligne sans sol supprimée ?** Un manque de couverture ne rend pas le rendement incorrect. Le consommateur peut définir ensuite sa population d'étude et rapporter ses exclusions.

**Quelles limites ?** Les règles ne vérifient pas l'exactitude des mesures et les unités de sol restent non confirmées. L'assistance IA doit être déclarée ; expliquer personnellement les jointures et les transactions avant candidature.
