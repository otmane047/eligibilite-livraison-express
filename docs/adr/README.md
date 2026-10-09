# Registre des Décisions d'Architecture (Architecture Decision Records - ADR)

Ce répertoire contient l'ensemble des **Architecture Decision Records (ADR)** pour le projet **`eligibilite-livraison-express`** (M2 IA dans le Cloud - TP1).

Les ADR documentent les choix techniques structurants, les contextes de décision, les alternatives évaluées et les conséquences opérationnelles pour assurer la pérennité et la clarté de l'architecture logicielle et MLOps.

---

## Index des Décisions

| Identifiant | Titre | Statut | Date | Portée / Thématique |
| :--- | :--- | :--- | :--- | :--- |
| [**ADR-001**](file:///./ADR-001-stockage-des-commandes.md) | Stratégie de stockage et persistance des commandes (Order Store) | **Accepté** | 2026-10-06 | Base de données SQL (SQLite / PostgreSQL), Repository Pattern, OpenAPI `/v1/orders` |
| [**ADR-002**](file:///./ADR-002-stockage-des-artefacts-de-modele.md) | Stratégie de stockage et gestion des artefacts de modèle Machine Learning | **Accepté** | 2026-10-06 | Stockage Objet Cloud (S3 / MinIO), MLflow Model Registry, In-Memory Caching, OpenAPI `/v1/model` |

---

## Format d'un ADR

Chaque enregistrement suit le standard international MADR (*Markdown Architectural Decision Records*) et comprend les sections suivantes :
1. **Contexte et Problématique** : Description du besoin métier, des contraintes d'API et des objectifs techniques.
2. **Facteurs de Décision** : Critères d'évaluation clés (performance, portabilité, coût, principes SOLID/YAGNI).
3. **Options Considérées** : Tableau comparatif objectif des solutions techniques envisageables avec leurs avantages et inconvénients.
4. **Décision Retenue** : Solution adoptée et argumentation détaillée.
5. **Architecture Technique & Implémentation** : Interfaces Python, schémas de données et modèles de composants.
6. **Conséquences** : Bilan des impacts positifs et des compromis (*trade-offs*) acceptés.
7. **Feuille de Route** : Déclinaison par séance de travaux pratiques (Séances 1 à 7).
