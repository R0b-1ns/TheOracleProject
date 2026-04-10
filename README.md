# LISEZ LES GOLEMS

# 🔮 The Oracle Protocol

Marché de prédictions décentralisé sur **Tezos Ghostnet**, avec système de réputation ELO et niveaux de confiance.
--- 
## Les consignes du prof 
Ce salon est dédié à me transmettre la composition des équipes pour votre projet.

Le projet consistera à imaginer votre propre dApp, essentiellement en créant votre propre smart contrat sur un thème que je vous donnerai bientôt.

Les livrables seront :
1) Un court pdf qui présente :
ce qu'est votre cas d'utilisation
pourquoi une blockchain est utile pour ce cas d'utilisation
quelles sont les fonctionnalités disponibles
des diagrammes qui montrent à quoi pourrait ressembler l'interface utilisateur de votre dapp
d'éventuels diagrammes montrant comment votre smart contrat interagirait avec les composants hors-chaine de votre projet


2) Le contenu de votre smart contrat et des tests, sous la forme d'un lien SmartPy + le contenu lui-même (au cas où il y a un souci avec le lien SmartPy)
Attention, la qualité des tests est aussi importante que celle du contrat

Notez bien qu'on ne vous demande de programmer rien d'autre que le contrat et ses textes. Le reste est juste à expliquer dans les slides sans le programmer.

Le thème du projet : les prédictions.
Attention cependant : ne faites pas un projet qui se consiste simplement à ce que des utilisateurs misent une somme sur une prédiction avec 2 possibilités, puis après un certain temps un oracle fournit la réponse au contrat, et ceux qui ont misé sur la bonne réponse se partagent les gains proportionnellement à la somme misée. Essayez de faire quelque-chose de plus original et plus avancé.

---
## Contrat
Le contrat est dans contrat. 

## Rapport 
Pour écrire le rapport c'est mieux de comprendre le code, comme c'est chiant vous pouvez ouvrire le `docs/explication_code_interactif.html` Qui est une page qui vous explique séction par séction comment ça marche dans les grandes lignes.

Dans le rapport vous pouvez inclure les diagrames/shémas suivants:
- https://stitch.withgoogle.com/preview/12966035675158303670?node-id=e6d5089a3f1249d99795dcb1fbd46e10 Liens vers une maquette de l'app les design devront apparaitre quelque part
- `docs/diagramme de séquence.svg` comme sont nom l'indique c'est un diagramme de séquence du contrat et de la potentiel app qui l'utiliserai
- `docs/uses cases` Les use case de l'application, le premier représente un utilisateur normal, le second un utilisateur malveillant
