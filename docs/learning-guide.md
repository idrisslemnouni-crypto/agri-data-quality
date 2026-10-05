# Comprendre l'ETL

Lire source.py : la taille et le hash empêchent de changer silencieusement de version. Lire validate : distinguer cellule absente, clé dupliquée, valeur invalide et couverture manquante entre tables.

La météo comporte 36 lignes par comté/année. Un join direct avec un rendement annuel multiplie les observations : agréger d'abord la météo puis joindre. Les moyennes publiées sont non pondérées par surface, sans prétention nationale de production.

Les unités de sol ne sont pas confirmées. Conserver le nom source et éviter une conversion inventée est une décision scientifique. Un rendement zéro est signalé, pas supprimé automatiquement.

Exercice : exécuter sql/checks.sql, retrouver les 23 980 rendements sans sol et vérifier qu'ils restent dans yield_coverage. Les lignes invalides des tests sont artificielles et distinctes du rapport réel, dont la quarantaine est vide.

La transaction et la construction temporaire préservent l'ancien résultat si le chargement échoue. Expliquer les tests d'idempotence, de clé étrangère et de conservation du fichier précédent.
