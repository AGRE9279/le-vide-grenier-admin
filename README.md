# Le Vide-Grenier — Espace équipe

Tableau de bord du garant et de son équipe : dépôts, vérification, publication, commandes, garanties, paiement des vendeurs, registre.

## Lancer sur ton ordinateur

```bash
pip install -r requirements.txt
streamlit run app.py
```

Le fichier `.streamlit/secrets.toml` contient l'adresse du projet Supabase « le-vide-grenier » et sa clé publique.

## Mettre en ligne (Streamlit Community Cloud, gratuit)

1. Crée un dépôt GitHub (par exemple `le-vide-grenier-admin`) et envoie `app.py`, `requirements.txt`, `README.md` et `.gitignore`. N'envoie pas `.streamlit/secrets.toml`.
2. Sur share.streamlit.io : « New app », choisis le dépôt et `app.py`.
3. Dans « Advanced settings → Secrets », colle le contenu de `.streamlit/secrets.toml`.

## Première connexion du garant

1. Onglet « Première connexion : créer mon mot de passe » avec l'e-mail agreappolin@gmail.com.
2. Clique sur le lien de confirmation reçu par e-mail.
3. Connecte-toi : ton compte est relié automatiquement au rôle « Garant ».

Les autres membres sont ajoutés dans la page « Équipe », puis font la même chose avec leur e-mail.

## Qui peut faire quoi

| Action | Vérificateur / livreur | Garant / admin |
|---|---|---|
| Enregistrer un dépôt, vérifier, refuser | oui | oui |
| Publier un objet | non | oui |
| Commandes, paiements reçus, livraisons, réclamations | oui | oui |
| Trancher une réclamation | non | oui |
| Payer un vendeur | non | oui |
| Ajouter des membres | non | oui |

Ces règles sont aussi appliquées dans la base Supabase elle-même : même en contournant l'appli, un vérificateur ne peut ni publier ni marquer un vendeur payé.
