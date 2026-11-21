# Haute disponibilité de Qafila

Ce document explique comment l'ERP Qafila (Odoo 19 + PostgreSQL 16) reste accessible quand une machine tombe en panne. Il décrit le principe, le déroulement d'une panne, les fichiers concernés, la façon de le tester et les limites.

## 1. Le problème

Sur une seule machine, une panne (coupure, crash, disque plein) rend l'ERP inaccessible. Les commandes, livraisons et factures sont bloquées jusqu'à la réparation.

La haute disponibilité (HA) consiste à doubler chaque élément pour que le service continue quand une machine s'arrête, **sans perdre de données** et **sans intervention humaine** pour la bascule.

## 2. L'architecture

Deux machines virtuelles identiques, clonées depuis le modèle durci :

```text
              IP virtuelle (keepalived) = qafila.tn / erp.qafila.tn
            ┌───────────────────────┴───────────────────────┐
      qafila-node1                                     qafila-node2
   Caddy ─► Odoo n1 + Odoo n2                      Caddy ─► Odoo n1 + Odoo n2
   PostgreSQL PRIMAIRE ───réplication continue───► PostgreSQL RÉPLIQUE
```

| Élément | Rôle | Pourquoi il est doublé |
|---|---|---|
| **IP virtuelle** (keepalived, protocole VRRP) | Adresse unique visée par les utilisateurs. Elle est portée par un seul nœud à la fois. | Si le nœud qui la porte tombe, elle passe sur l'autre : les utilisateurs ne changent rien. |
| **Caddy** | HTTPS et répartition de charge vers les deux Odoo. | Chaque nœud a le sien. |
| **Odoo** | L'application. Elle ne garde rien d'important sur le disque. | Un Odoo par nœud. Si l'un tombe, Caddy envoie tout vers l'autre. |
| **PostgreSQL** | Les données : clients, commandes, factures et pièces jointes. | Le primaire accepte les écritures, la réplique en reçoit une copie en continu. |

Trois choix rendent cela possible :

- **Les pièces jointes sont stockées en base** (`ir_attachment.location = db`). La réplication PostgreSQL copie donc aussi les PDF et les images. Il n'y a pas de dossier partagé (NFS) qui deviendrait un point unique de panne.
- **Odoo se connecte à PostgreSQL via l'IP virtuelle.** Odoo atteint donc toujours la base du nœud qui porte l'IP, c'est-à-dire le primaire.
- **La réplique suit elle aussi l'IP virtuelle.** Après une bascule, elle n'a pas besoin d'être reconfigurée.

## 3. Le fonctionnement normal

1. node1 porte l'IP virtuelle et sa base est **primaire**.
2. Chaque écriture (nouvelle commande, facture…) est envoyée en continu à la base de node2. Le retard est inférieur à une seconde.
3. La base de node2 est en **lecture seule** : personne ne peut y écrire par erreur.
4. Toutes les 5 secondes, keepalived lance sur chaque nœud un contrôle de santé (`qafila-check`). Ce contrôle vérifie que PostgreSQL et le site web répondent.

## 4. Le déroulement d'une panne de node1

| Temps | Ce qui se passe |
|---|---|
| 0 s | node1 s'arrête (coupure, crash, ou contrôle de santé en échec). |
| ~3 s | node2 ne reçoit plus les messages VRRP de node1. |
| ~3–10 s | keepalived place l'IP virtuelle sur node2, puis lance `qafila-promote`. La réplique devient **primaire** (`pg_promote()`). |
| ~10 s | Odoo se reconnecte via l'IP virtuelle et arrive sur la nouvelle base primaire. L'ERP fonctionne à nouveau. |

Pour l'utilisateur, l'ERP ne répond pas pendant une dizaine de secondes. Il peut ensuite devoir se reconnecter, car les sessions Odoo sont propres à chaque nœud.

## 5. Le retour de node1 et la protection contre le « cerveau divisé »

C'est le point le plus délicat de toute HA.

**Le danger.** Quand node1 redémarre, sa base se croit encore primaire. Pourtant, ses données sont **périmées** : tout ce qui a été saisi sur node2 pendant la panne lui manque. S'il reprenait l'IP virtuelle, on aurait **deux bases primaires** avec des données différentes. C'est le « cerveau divisé » (*split brain*), et il fait perdre des données.

**Deux protections :**

1. **`nopreempt`** : un nœud qui revient ne reprend jamais l'IP au nœud qui l'a remplacé, même s'il a une priorité plus haute.
2. **La clôture (*fencing*)** : le contrôle de santé de node1 voit trois choses à la fois.
   - Sa base locale est primaire.
   - Il ne porte pas l'IP virtuelle.
   - La base derrière l'IP virtuelle est elle aussi primaire.

   Il en conclut qu'il est un ancien primaire périmé. Il **arrête sa base** et écrit le marqueur `/var/lib/qafila/fenced`. Tant que ce marqueur existe, ce nœud ne peut plus prendre l'IP, même si on relance sa base à la main.

**La réintégration.** Sur node1, lancer :

```bash
./scripts/ha/init-standby.sh   # efface la base périmée et recopie celle du primaire actuel
./install.sh                   # redémarre les services ; node1 est maintenant la réplique
```

Dès que la base de node1 tourne en réplique, le contrôle de santé lève la clôture tout seul. Le cluster est de nouveau protégé, avec les rôles inversés : node2 primaire, node1 réplique.

## 6. Les fichiers

| Fichier | Rôle |
|---|---|
| `config/ha/compose.ha.yaml` | Conteneurs d'un nœud (PostgreSQL configuré pour la réplication, Odoo, Caddy), en réseau « host ». |
| `config/ha/keepalived.conf.tmpl` | Modèle de configuration keepalived : IP virtuelle, `nopreempt`, contrôle de santé, promotion. |
| `scripts/ha/node-setup.sh` (sudo) | Prépare un nœud : keepalived, scripts root, pare-feu, `/etc/hosts`, redémarrage auto des conteneurs. |
| `scripts/ha/check.sh` | Contrôle de santé et clôture. Installé en `/usr/libexec/keepalived/qafila-check`. |
| `scripts/ha/promote.sh` | Promotion de la réplique en primaire. Installé en `/usr/libexec/keepalived/qafila-promote`. |
| `scripts/ha/init-standby.sh` | (Re)construit la base locale comme réplique du primaire actuel. |
| `scripts/ha/status.sh` | État du cluster vu depuis un nœud : IP, rôle de la base, retard, clôture. |
| `scripts/ha/lab-test.sh` | Banc d'essai de la bascule sur une seule machine. |
| `install.sh` | En HA, lit le **vrai** rôle de la base locale, car il change après une bascule. Refuse de tourner sur un nœud clôturé. |

**Pourquoi `/usr/libexec/keepalived/` ?** keepalived exécute ses scripts en root. Pour la sécurité, il refuse un script modifiable par un utilisateur ordinaire. De son côté, SELinux n'autorise keepalived à lancer des scripts que dans ce dossier. `node-setup.sh` y copie donc les scripts, avec root comme propriétaire. Après toute modification de `check.sh` ou `promote.sh`, il faut relancer `sudo ./scripts/ha/node-setup.sh`.

**Autres protections :**
- `max_slot_wal_keep_size=2GB` : si la réplique reste éteinte longtemps, le primaire ne garde pas indéfiniment l'historique qui lui est destiné. Sans cette limite, le disque du primaire se remplirait et tout s'arrêterait.
- Les ports PostgreSQL (5432) et Odoo (8069) ne sont ouverts qu'au nœud voisin.
- Les conteneurs redémarrent automatiquement avec la machine.

## 7. La mise en place

Prérequis : deux VM clonées du modèle sur le même réseau, et le même `.env` sur les deux (`NODE1_IP`, `NODE2_IP`, `VIP`, mots de passe). Seule la variable `QAFILA_ROLE` change.

| Étape | node1 (`QAFILA_ROLE=primary`) | node2 (`QAFILA_ROLE=standby`) |
|---|---|---|
| 1 | `sudo ./scripts/ha/node-setup.sh` | |
| 2 | `./install.sh` (crée la base et les données) | |
| 3 | | `sudo ./scripts/ha/node-setup.sh` |
| 4 | | `./scripts/ha/init-standby.sh` |
| 5 | | `./install.sh` |
| 6 | `./scripts/ha/status.sh` | `./scripts/ha/status.sh` |

Sur les postes clients : `sudo ./scripts/sudo-setup.sh <VIP>`, pour que `qafila.tn` et `erp.qafila.tn` pointent vers l'IP virtuelle.

## 8. Les tests

### Sans deuxième machine

```bash
./scripts/ha/lab-test.sh
```

Ce script lance deux PostgreSQL jetables sur la machine et utilise les **vrais** scripts `check.sh` et `promote.sh`. Seuls keepalived et l'IP virtuelle sont simulés. Scénario :

1. A est primaire et B est sa réplique. Une écriture sur A apparaît sur B, et B refuse les écritures.
2. A tombe en panne : son contrôle échoue, B est promue et accepte les écritures.
3. A revient avec ses anciennes données. Elle refuse l'IP, est clôturée et sa base est arrêtée. Même relancée à la main, elle reste refusée.
4. A est réintégrée comme réplique de B. La clôture est levée et les 4 expéditions sont présentes. **Aucune donnée n'est perdue.**

Résultat obtenu : **16 vérifications réussies sur 16** (environ 1 minute).

### Avec les deux machines (démonstration)

1. Sur node1 : `sudo poweroff`.
2. Dans le navigateur, `https://erp.qafila.tn` répond de nouveau après une dizaine de secondes.
3. Sur node2, `./scripts/ha/status.sh` affiche : IP virtuelle portée par ce nœud, PostgreSQL PRIMAIRE.
4. Rallumer node1 : `status.sh` y affiche « CLÔTURÉ ». La réintégration se fait comme décrit en section 5.

## 9. Les limites

| Limite | Conséquence | Solution en production |
|---|---|---|
| Réplication **asynchrone** | Lors d'une bascule, la dernière seconde d'écritures peut être perdue. | Réplication synchrone, avec au moins 3 nœuds pour ne pas bloquer le primaire. |
| **Deux nœuds sans arbitre** | Si node1 tombe, puis node2 tombe **avant** le retour de node1, node1 revient avec des données anciennes et personne ne peut le contredire. | Un 3ᵉ nœud qui vote : Patroni + etcd. |
| Sessions Odoo propres à chaque nœud | Après une bascule, l'utilisateur doit se reconnecter. | Sessions en base ou dans un stockage partagé. |
| Une seule salle / un seul réseau | Une panne réseau ou électrique générale arrête tout. | Nœuds sur des sites différents. |
| Sauvegardes locales | Une sauvegarde sur la même machine disparaît avec elle. | Copies chiffrées hors site (`scripts/backup.sh` + transfert externe). |

La HA protège contre la **panne d'une machine**. Elle ne remplace pas les **sauvegardes**. Une suppression par erreur est répliquée immédiatement sur l'autre nœud : seule une sauvegarde permet de revenir en arrière.
