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

## Exploitation

- État : `podman ps`
- Logs : `podman logs -f odoo-demo-app` / `podman logs -f odoo-demo-db`
- Sauvegardes : exporter régulièrement la base avec `pg_dump` et le volume filestore `odoo-ha-data`, puis copier les exports chiffrés hors de cette machine.
- Le compte administrateur Odoo est créé lors de l'initialisation web ; définissez un mot de passe solide avant d'exposer l'instance.
