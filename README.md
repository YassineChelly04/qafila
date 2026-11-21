# ERP logistique Odoo — démonstrateur

Installation locale Odoo 19 + SS avec Podman rootless (RHEL/Linux). Modules activés : Contacts, Ventes, Achats et Inventaire. Les services s'exécutent sur ce seul hôte ; cette installation est une maquette exploitable, pas un cluster HA.

## Installation

1. `cp .env.example .env`, puis remplacez **tous** les mots de passe par des valeurs uniques. `.env` contient des secrets ; il est ignoré par Git.
2. `chmod +x install.sh && ./install.sh`
3. Accédez à `http://127.0.0.1:8069`. Le port est limité à localhost.

`install.sh` crée la base `logistics_demo`, installe les modules logistiques, crée cinq clients fictifs et un utilisateur logistique, puis lance les conteneurs persistants. Le premier démarrage télécharge les images officielles et peut prendre plusieurs minutes. L'identifiant admin est `admin` (mot de passe défini dans `ODOO_ADMIN_PASSWORD`) ; l'utilisateur métier est `logistique@example.invalid` (mot de passe défini dans `ODOO_DEMO_USER_PASSWORD`). Changez ces identifiants après connexion. Pour arrêter : `podman stop odoo-demo-app odoo-demo-db`. Les volumes `odoo-ha-pg` et `odoo-ha-data` conservent les données.

## Jeu de données demandé

Les cinq sociétés de démonstration sont Atlas Distribution, Carthage Retail, Maghreb Pharma, Sahara Agro et Tunis Tech Supply. Elles sont créées automatiquement avec une adresse `.invalid` réservée aux exemples.

## Architecture HA cible (production)

```text
Internet → VIP/DNS → 2× HAProxy + Keepalived (TLS)
                    → 2+ nœuds Odoo stateless (workers, addons identiques)
                    → PostgreSQL HA (Patroni + etcd/Consul, primaire + réplique)
                    → stockage filestore partagé/répliqué (S3 compatible ou NFS HA)
Sauvegardes chiffrées PostgreSQL + filestore hors site, supervision et alertes
```

Prévoir au minimum trois hôtes indépendants pour le quorum et la tolérance à la panne d'un hôte, un stockage réseau redondant, un répartiteur avec contrôle de santé et une procédure de restauration testée. Toutes les instances Odoo doivent partager la même base PostgreSQL et le même filestore. Une réplique PostgreSQL seule ne rend pas Odoo hautement disponible. L'hôte présent n'a qu'environ 3,5 Gio de RAM et ne peut héberger en sécurité toutes ces briques ni maintenir le service en cas de panne de l'hôte. La configuration multi-nœuds, TLS public, bascule automatique et sauvegardes externes nécessitent des serveurs/réseau/DNS supplémentaires et ne sont pas activés ici.

## Haute disponibilité à deux nœuds (implémentée)

```text
               IP virtuelle (keepalived) = qafila.tn / erp.qafila.tn
             ┌──────────────────────┴──────────────────────┐
      qafila-node1                                   qafila-node2
  Caddy → Odoo n1 + Odoo n2                     Caddy → Odoo n1 + Odoo n2
  PostgreSQL PRIMAIRE ──réplication continue──►  PostgreSQL RÉPLIQUE
```

- **Une seule adresse** : les clients visent l'IP virtuelle. keepalived la place sur un nœud sain ; si ce nœud tombe, elle passe sur l'autre en ~10 s.
- **Base répliquée en continu** : chaque écriture du primaire est rejouée sur la réplique. Les pièces jointes sont stockées en base, donc répliquées aussi.
- **Bascule automatique** : le nœud qui reçoit l'IP virtuelle promeut sa réplique en primaire. Odoo se connecte toujours via l'IP virtuelle, il suit donc sans reconfiguration.
- **Pas de « cerveau divisé »** : un ancien primaire qui revient après une panne ne reprend pas l'IP (`nopreempt`). Il détecte qu'un autre primaire sert l'IP, arrête sa base et se marque « clôturé ». Il n'est réintégré, comme réplique, que par `init-standby.sh`.

**Mise en place** (deux VM clonées du modèle, `.env` identique sauf `QAFILA_ROLE`) :

1. nœud 1 (`QAFILA_ROLE=primary`) : `sudo ./scripts/ha/node-setup.sh` puis `./install.sh`
2. nœud 2 (`QAFILA_ROLE=standby`) : `sudo ./scripts/ha/node-setup.sh`, `./scripts/ha/init-standby.sh`, puis `./install.sh`
3. sur chaque nœud : `./scripts/ha/status.sh`

**Démonstration de bascule** : arrêter le nœud 1 (`sudo poweroff`) → `erp.qafila.tn` répond toujours, servi par le nœud 2 dont la base est devenue primaire (`status.sh`). Au retour, le nœud 1 s'affiche « CLÔTURÉ » : `./scripts/ha/init-standby.sh` puis `./install.sh` le réintègre comme réplique.

**Sans deuxième VM** : `./scripts/ha/lab-test.sh` rejoue réplication, panne, promotion, clôture et réintégration avec deux PostgreSQL jetables sur cette machine (16 vérifications, ~1 min).

**Limites assumées (deux nœuds, sans arbitre)** : la réplication est asynchrone, donc la dernière seconde d'écritures peut être perdue lors d'une bascule. Si les deux nœuds tombent l'un après l'autre, le premier revenu peut avoir des données anciennes. Une production réelle ajoute un troisième nœud arbitre (Patroni + etcd, voir ci-dessus).

## Exploitation

- État : `podman ps`
- Logs : `podman logs -f odoo-demo-app` / `podman logs -f odoo-demo-db`
- Sauvegardes : exporter régulièrement la base avec `pg_dump` et le volume filestore `odoo-ha-data`, puis copier les exports chiffrés hors de cette machine.
- Le compte administrateur Odoo est créé lors de l'initialisation web ; définissez un mot de passe solide avant d'exposer l'instance.
