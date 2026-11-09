"""Le Vide-Grenier — tableau de bord de l'équipe (garant, admins, vérificateurs, livreurs).

Chaque vente suit le circuit garanti :
proposé -> vérifié -> publié -> réservé -> vendu (livré, sous garantie) -> vendeur payé
"""
from datetime import date, datetime, timezone

import pandas as pd
import streamlit as st
from supabase import create_client

from pathlib import Path

ICONE = Path(__file__).with_name("logo_icone.png")
st.set_page_config(page_title="Le Vide-Grenier — Équipe",
                   page_icon=str(ICONE) if ICONE.exists() else "🏷️", layout="wide")

BLEU, ORANGE = "#14365A", "#F08A24"
MARQUE_SVG = (
    '<svg width="{t}" height="{t}" viewBox="0 0 140 126" role="img" aria-label="Logo Le Vide-Grenier">'
    f'<path d="M8 58 L70 10 L132 58" fill="none" stroke="{ORANGE}" stroke-width="12" '
    'stroke-linecap="round" stroke-linejoin="round"/>'
    f'<rect x="24" y="52" width="92" height="66" rx="10" fill="{BLEU}"/>'
    '<text x="70" y="102" text-anchor="middle" font-family="\'Baloo 2\', sans-serif" font-weight="800" '
    'font-size="46" fill="#FFFFFF">VG</text></svg>'
)


def logo(grand=True):
    """Logo piste B : le toit du grenier au-dessus de VG."""
    t, nom, sous = (84, 46, 12) if grand else (48, 26, 9)
    st.markdown(
        "<style>@import url('https://fonts.googleapis.com/css2?family=Baloo+2:wght@600;800&display=swap');</style>"
        f'<div style="display:flex;align-items:center;gap:{t // 5}px;margin-bottom:8px">'
        + MARQUE_SVG.format(t=t) +
        '<div style="display:flex;flex-direction:column;line-height:1">'
        f'<span style="font-family:\'Baloo 2\',sans-serif;font-weight:800;font-size:{nom}px;color:{BLEU}">Le Vide-Grenier</span>'
        f'<span style="font-weight:600;font-size:{sous}px;letter-spacing:2px;text-transform:uppercase;color:#9A4A06;margin-top:4px">'
        'Les bonnes affaires de la maison</span></div></div>',
        unsafe_allow_html=True,
    )


# ---------- Outils ----------

def sb():
    """Un client Supabase par session : chaque membre de l'équipe a sa propre connexion."""
    if "sb" not in st.session_state:
        st.session_state.sb = create_client(URL, KEY)
    return st.session_state.sb


def fcfa(n):
    return f"{int(n or 0):,} FCFA".replace(",", " ")


def parse_dt(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def jolie_date(s):
    d = parse_dt(s)
    return d.strftime("%d/%m/%Y %H:%M") if d else "—"


def maintenant():
    return datetime.now(timezone.utc).isoformat()


def commission(formule, prix):
    taux, minimum = (0.20, 1000) if formule == "domicile" else (0.15, 500)
    return max(round(prix * taux), minimum)


def garantie_txt(est_appareil):
    return "7 jours" if est_appareil else "48 h"


def membre():
    return st.session_state.get("membre")


def est_garant():
    return membre() and membre()["role"] in ("garant", "admin")


def ok(message):
    st.session_state.flash = message
    st.rerun()


def choisir_ou_creer_personne(prefixe, titre):
    """Sélectionne une personne existante ou en crée une nouvelle. Renvoie son id (ou None)."""
    personnes = sb().table("personnes").select("id, nom, telephone, quartier").order("nom").execute().data
    options = ["➕ Nouvelle personne"] + [f"{p['nom']} — {p['telephone']}" for p in personnes]
    choix = st.selectbox(titre, options, key=f"{prefixe}_choix")
    if choix != options[0]:
        return personnes[options.index(choix) - 1]["id"], None
    c1, c2, c3 = st.columns(3)
    nouvelle = {
        "nom": c1.text_input("Nom complet", key=f"{prefixe}_nom"),
        "telephone": c2.text_input("Téléphone (WhatsApp)", key=f"{prefixe}_tel"),
        "quartier": c3.text_input("Quartier", key=f"{prefixe}_quartier"),
        "piece_identite_vue": st.checkbox("Pièce d'identité vue", key=f"{prefixe}_piece"),
    }
    return None, nouvelle


def enregistrer_personne(pid, nouvelle):
    if pid:
        return pid
    if not nouvelle["nom"].strip() or not nouvelle["telephone"].strip():
        st.error("Le nom et le téléphone sont obligatoires.")
        st.stop()
    return sb().table("personnes").insert(nouvelle).execute().data[0]["id"]


def texte_annonce(o):
    lignes = [
        f"🏷️ {o['code_vg']} – {o['titre']}",
        f"💰 {fcfa(o['prix_vente'])}",
        f"✅ État : {ETATS[o['etat']]}" + (f" – {o['defauts']}" if o.get("defauts") else ""),
    ]
    if o.get("description"):
        lignes.append(f"ℹ️ {o['description']}")
    lignes += [
        f"🛡️ Vérifié par Le Vide-Grenier et garanti {garantie_txt(o['est_appareil'])}",
        f"📲 Pour commander : écris « {o['code_vg']} » au numéro du Vide-Grenier",
    ]
    return "\n".join(lignes)


# ---------- Connexion ----------

def ecran_connexion():
    logo(grand=True)
    st.subheader("Espace équipe")
    st.caption("Réservé à l'équipe du Vide-Grenier.")
    t1, t2 = st.tabs(["Se connecter", "Première connexion : créer mon mot de passe"])
    with t1:
        with st.form("connexion"):
            email = st.text_input("E-mail")
            mdp = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("Se connecter", type="primary"):
                try:
                    res = sb().auth.sign_in_with_password({"email": email.strip(), "password": mdp})
                    st.session_state.user = res.user
                    st.rerun()
                except Exception:
                    st.error("E-mail ou mot de passe incorrect, ou e-mail pas encore confirmé.")
    with t2:
        st.write("Utilise l'e-mail que le garant a inscrit dans l'équipe.")
        with st.form("inscription"):
            email = st.text_input("E-mail", key="ins_email")
            mdp = st.text_input("Choisis un mot de passe (8 caractères minimum)", type="password", key="ins_mdp")
            if st.form_submit_button("Créer mon mot de passe"):
                try:
                    sb().auth.sign_up({"email": email.strip(), "password": mdp})
                    st.success("C'est fait. Ouvre ta boîte mail, clique sur le lien de confirmation, puis connecte-toi.")
                except Exception as e:
                    st.error(f"Impossible de créer le compte : {e}")


def charger_membre():
    user = st.session_state.user
    rows = sb().table("equipe").select("*").eq("user_id", user.id).execute().data
    if not rows or not rows[0]["actif"]:
        st.error("Ton compte n'est pas (ou plus) dans l'équipe du Vide-Grenier. Demande au garant de t'ajouter.")
        if st.button("Se déconnecter"):
            deconnexion()
        st.stop()
    st.session_state.membre = rows[0]


def deconnexion():
    try:
        sb().auth.sign_out()
    except Exception:
        pass
    for k in ("user", "membre", "sb"):
        st.session_state.pop(k, None)
    st.rerun()


# ---------- Pages ----------

def page_tableau_de_bord():
    st.header("Tableau de bord")
    objets = sb().table("objets").select("statut, date_fin_depot, code_vg, titre").execute().data
    commandes = sb().table("commandes").select("statut, fin_garantie").execute().data
    a_payer = sb().table("vendeurs_a_payer").select("*").execute().data
    compte = lambda s: sum(1 for o in objets if o["statut"] == s)

    c = st.columns(5)
    c[0].metric("À vérifier", compte("propose"))
    c[1].metric("À publier", compte("verifie"))
    c[2].metric("En vente", compte("publie"))
    c[3].metric("Sous garantie", sum(1 for x in commandes if x["statut"] == "livree"))
    c[4].metric("Vendeurs à payer", len(a_payer), fcfa(sum(x["montant_a_verser"] for x in a_payer)))

    if a_payer:
        st.subheader("Vendeurs à payer (garantie terminée)")
        st.dataframe(pd.DataFrame(a_payer)[["code_vg", "titre", "vendeur", "telephone", "montant_vente", "commission", "montant_a_verser"]],
                     hide_index=True, width="stretch")

    bientot = [o for o in objets if o["statut"] == "publie" and o["date_fin_depot"]
               and (date.fromisoformat(o["date_fin_depot"]) - date.today()).days <= 3]
    if bientot:
        st.subheader("Dépôts qui arrivent à 30 jours")
        st.write("Propose une baisse de prix au vendeur, ou qu'il récupère l'objet sous 7 jours.")
        st.dataframe(pd.DataFrame(bientot)[["code_vg", "titre", "date_fin_depot"]], hide_index=True)


def page_nouveau_depot():
    st.header("Nouveau dépôt")
    st.caption("Étape 1 du circuit : le vendeur propose son objet.")
    pid, nouvelle = choisir_ou_creer_personne("vendeur", "Vendeur")
    st.divider()
    c1, c2 = st.columns(2)
    titre = c1.text_input("Objet (ex. : Téléphone Tecno Spark 10)")
    categorie = c2.selectbox("Catégorie", list(CATEGORIES), format_func=CATEGORIES.get)
    description = st.text_area("Description (marque, taille, couleur…)")
    c3, c4, c5 = st.columns(3)
    etat = c3.selectbox("État annoncé", list(ETATS), format_func=ETATS.get, index=1)
    formule = c4.selectbox("Formule", list(FORMULES), format_func=FORMULES.get)
    prix = c5.number_input("Prix demandé par le vendeur (FCFA)", min_value=0, step=500)
    est_appareil = st.checkbox("Appareil électrique ou téléphone (garantie 7 jours, test obligatoire)",
                               value=categorie == "electronique")
    if prix:
        st.info(f"Si l'objet est vendu {fcfa(prix)} : commission {fcfa(commission(formule, prix))}, "
                f"le vendeur reçoit {fcfa(prix - commission(formule, prix))}.")
    if st.button("Enregistrer le dépôt", type="primary"):
        if not titre.strip():
            st.error("Indique le nom de l'objet.")
            st.stop()
        vendeur_id = enregistrer_personne(pid, nouvelle)
        o = sb().table("objets").insert({
            "vendeur_id": vendeur_id, "titre": titre.strip(), "description": description.strip() or None,
            "categorie": categorie, "etat": etat, "formule": formule, "est_appareil": est_appareil,
            "prix_demande": int(prix) or None,
            "date_depot": date.today().isoformat() if formule == "depot" else None,
        }).execute().data[0]
        ok(f"Dépôt enregistré : écris **{o['code_vg']}** sur l'étiquette de l'objet.")


def page_verification():
    st.header("Vérification")
    st.caption("Étape 2 : tester l'objet, noter les défauts, puis le déclarer conforme ou le refuser.")
    objets = sb().table("objets").select("*, vendeur:personnes(nom, telephone, piece_identite_vue)") \
        .eq("statut", "propose").order("created_at").execute().data
    if not objets:
        st.success("Aucun objet en attente de vérification.")
    for o in objets:
        with st.expander(f"{o['code_vg']} — {o['titre']} ({o['vendeur']['nom']})"):
            st.write(f"Catégorie : {CATEGORIES[o['categorie']]} · État annoncé : {ETATS[o['etat']]} · "
                     f"Prix demandé : {fcfa(o['prix_demande'])}")
            if o.get("description"):
                st.write(o["description"])
            k = o["id"]
            controles = [st.checkbox("Pièce d'identité du vendeur vue", value=o["vendeur"]["piece_identite_vue"], key=f"pi{k}")]
            imei, preuve = None, False
            if o["est_appareil"]:
                imei = st.text_input("IMEI ou numéro de série", value=o.get("imei") or "", key=f"imei{k}")
                preuve = st.checkbox("Facture ou boîte présentée, même IMEI que l'appareil", key=f"pr{k}")
                controles += [preuve, st.checkbox("Testé : s'allume, charge, appels, caméra, écran, boutons", key=f"t{k}")]
            else:
                controles.append(st.checkbox("Objet complet, propre, conforme à la description", key=f"c{k}"))
            defauts = st.text_input("Défauts constatés (seront écrits dans l'annonce)", key=f"d{k}")
            etat = st.selectbox("État constaté", list(ETATS), format_func=ETATS.get,
                                index=list(ETATS).index(o["etat"]), key=f"e{k}")
            prix = st.number_input("Prix de vente retenu (FCFA)", min_value=0, step=500,
                                   value=int(o["prix_demande"] or 0), key=f"p{k}")
            c1, c2 = st.columns(2)
            if c1.button("✅ Conforme", key=f"ok{k}", type="primary"):
                if not all(controles):
                    st.error("Tous les contrôles doivent être cochés pour déclarer l'objet conforme.")
                elif prix <= 0:
                    st.error("Indique le prix de vente.")
                else:
                    sb().table("objets").update({
                        "statut": "verifie", "etat": etat, "defauts": defauts or None, "imei": imei or None,
                        "preuve_achat": preuve, "prix_vente": int(prix), "verifie_par": membre()["id"],
                    }).eq("id", k).execute()
                    if controles[0] and not o["vendeur"]["piece_identite_vue"]:
                        sb().table("personnes").update({"piece_identite_vue": True}).eq("id", o["vendeur_id"]).execute()
                    ok(f"{o['code_vg']} vérifié : il attend la validation du garant.")
            motif = c2.text_input("Motif du refus", key=f"m{k}")
            if c2.button("❌ Refuser et rendre au vendeur", key=f"no{k}"):
                if not motif.strip():
                    st.error("Indique le motif du refus.")
                else:
                    sb().table("objets").update({"statut": "refuse", "motif_refus": motif.strip(),
                                                 "verifie_par": membre()["id"]}).eq("id", k).execute()
                    ok(f"{o['code_vg']} refusé. Préviens le vendeur et rends-lui l'objet.")


def page_publication():
    st.header("Publication")
    st.caption("Étape 3 : seul le garant (ou un admin) publie, après avoir relu la fiche.")
    if not est_garant():
        st.warning("Cette étape est réservée au garant et aux admins.")
        return
    objets = sb().table("objets").select("*, vendeur:personnes(nom)").eq("statut", "verifie").order("created_at").execute().data
    if not objets:
        st.success("Aucun objet en attente de publication.")
    for o in objets:
        with st.expander(f"{o['code_vg']} — {o['titre']} · {fcfa(o['prix_vente'])}", expanded=True):
            st.code(texte_annonce(o), language=None)
            st.caption(f"Vendeur : {o['vendeur']['nom']} · Formule : {FORMULES[o['formule']]} · "
                       f"Commission prévue : {fcfa(commission(o['formule'], o['prix_vente']))}")
            if st.button("Valider et publier", key=f"pub{o['id']}", type="primary"):
                sb().table("objets").update({"statut": "publie", "valide_par": membre()["id"]}).eq("id", o["id"]).execute()
                ok(f"{o['code_vg']} publié. Copie l'annonce dans le bon groupe WhatsApp.")

    st.subheader("En vente actuellement")
    en_vente = sb().table("objets").select("*").eq("statut", "publie").order("created_at", desc=True).execute().data
    for o in en_vente:
        with st.expander(f"{o['code_vg']} — {o['titre']} · {fcfa(o['prix_vente'])}"):
            st.code(texte_annonce(o), language=None)


def page_commandes():
    st.header("Commandes")
    st.caption("Étapes 4 à 6 : l'acheteur commande, paie Le Vide-Grenier, puis tu livres.")
    en_vente = sb().table("objets").select("id, code_vg, titre, prix_vente").eq("statut", "publie").order("code_vg").execute().data
    with st.expander("➕ Nouvelle commande", expanded=bool(en_vente)):
        if not en_vente:
            st.info("Aucun objet publié pour le moment.")
        else:
            choix = st.selectbox("Objet commandé", en_vente, format_func=lambda o: f"{o['code_vg']} — {o['titre']} ({fcfa(o['prix_vente'])})")
            pid, nouvelle = choisir_ou_creer_personne("acheteur", "Acheteur")
            c1, c2, c3 = st.columns(3)
            prix = c1.number_input("Prix (FCFA)", min_value=0, step=500, value=int(choix["prix_vente"]))
            frais = c2.number_input("Frais de livraison (FCFA)", min_value=0, step=100, value=500)
            mode = c3.selectbox("Paiement", ["mobile_money", "especes"],
                                format_func={"mobile_money": "Mobile Money", "especes": "Espèces à la livraison"}.get)
            if st.button("Enregistrer la commande", type="primary"):
                acheteur_id = enregistrer_personne(pid, nouvelle)
                sb().table("commandes").insert({"objet_id": choix["id"], "acheteur_id": acheteur_id, "prix": int(prix),
                                                "frais_livraison": int(frais), "mode_paiement": mode}).execute()
                sb().table("objets").update({"statut": "reserve"}).eq("id", choix["id"]).execute()
                ok(f"Commande enregistrée : écris « RÉSERVÉ » sous l'annonce {choix['code_vg']}.")

    commandes = sb().table("commandes").select("*, objet:objets(id, code_vg, titre), acheteur:personnes(nom, telephone)") \
        .in_("statut", ["reservee", "payee"]).order("created_at").execute().data
    st.subheader("À encaisser et à livrer")
    if not commandes:
        st.success("Aucune commande en cours.")
    for c in commandes:
        o = c["objet"]
        total = c["prix"] + c["frais_livraison"]
        etat = "💰 payée" if c["statut"] == "payee" else "⏳ pas encore payée"
        with st.expander(f"{o['code_vg']} — {o['titre']} → {c['acheteur']['nom']} ({c['acheteur']['telephone']}) · {fcfa(total)} · {etat}"):
            k = c["id"]
            if c["statut"] == "reservee":
                ref = st.text_input("Référence Mobile Money (ou « espèces »)", key=f"ref{k}")
                b1, b2 = st.columns(2)
                if b1.button("Paiement reçu sur le compte du Vide-Grenier", key=f"pay{k}", type="primary"):
                    sb().table("commandes").update({"statut": "payee", "date_paiement": maintenant(),
                                                    "reference_paiement": ref or None}).eq("id", k).execute()
                    ok("Paiement enregistré.")
                if b2.button("Annuler la commande", key=f"ann{k}"):
                    sb().table("commandes").update({"statut": "annulee"}).eq("id", k).execute()
                    sb().table("objets").update({"statut": "publie"}).eq("id", o["id"]).execute()
                    ok(f"Commande annulée : {o['code_vg']} est de nouveau en vente.")
            else:
                if st.button("📦 Livré à l'acheteur (la garantie commence)", key=f"liv{k}", type="primary"):
                    sb().table("commandes").update({"statut": "livree", "date_livraison": maintenant(),
                                                    "livre_par": membre()["id"]}).eq("id", k).execute()
                    sb().table("objets").update({"statut": "vendu"}).eq("id", o["id"]).execute()
                    ok(f"{o['code_vg']} livré. Écris « VENDU » sous l'annonce.")


def page_garanties():
    st.header("Garanties et réclamations")
    st.caption("Étape 7 : pendant la garantie, l'acheteur peut signaler un problème.")
    maintenant_dt = datetime.now(timezone.utc)
    livrees = sb().table("commandes").select("*, objet:objets(id, code_vg, titre, est_appareil), acheteur:personnes(nom, telephone)") \
        .eq("statut", "livree").order("fin_garantie").execute().data
    sous_garantie = [c for c in livrees if parse_dt(c["fin_garantie"]) > maintenant_dt]
    st.subheader("Sous garantie")
    if not sous_garantie:
        st.info("Aucune vente sous garantie.")
    for c in sous_garantie:
        with st.expander(f"{c['objet']['code_vg']} — {c['objet']['titre']} → {c['acheteur']['nom']} · fin le {jolie_date(c['fin_garantie'])}"):
            motif = st.text_input("Problème signalé par l'acheteur", key=f"rec{c['id']}")
            st.caption("Rappel : un changement d'avis, l'usure indiquée ou une casse après livraison ne sont pas couverts.")
            if st.button("Enregistrer la réclamation", key=f"brec{c['id']}"):
                if not motif.strip():
                    st.error("Décris le problème.")
                else:
                    sb().table("reclamations").insert({"commande_id": c["id"], "motif": motif.strip()}).execute()
                    sb().table("commandes").update({"statut": "reclamation"}).eq("id", c["id"]).execute()
                    ok("Réclamation enregistrée. Le paiement du vendeur est bloqué.")

    st.subheader("Réclamations à trancher")
    if not est_garant():
        st.caption("Seul le garant ou un admin peut trancher.")
    recs = sb().table("reclamations").select("*, commande:commandes(id, prix, frais_livraison, objet:objets(id, code_vg, titre), acheteur:personnes(nom, telephone))") \
        .eq("decision", "en_attente").execute().data
    if not recs:
        st.success("Aucune réclamation en attente.")
    for r in recs:
        c = r["commande"]
        with st.expander(f"{c['objet']['code_vg']} — {c['acheteur']['nom']} : {r['motif']}", expanded=True):
            if est_garant():
                b1, b2 = st.columns(2)
                if b1.button(f"Accepter : rembourser {fcfa(c['prix'])} et reprendre l'objet", key=f"acc{r['id']}", type="primary"):
                    sb().table("reclamations").update({"decision": "acceptee", "traite_par": membre()["id"], "traitee_le": maintenant()}).eq("id", r["id"]).execute()
                    sb().table("commandes").update({"statut": "remboursee"}).eq("id", c["id"]).execute()
                    sb().table("objets").update({"statut": "rendu"}).eq("id", c["objet"]["id"]).execute()
                    ok("Réclamation acceptée : rembourse l'acheteur depuis le compte du Vide-Grenier et rends l'objet au vendeur.")
                if b2.button("Refuser (non couvert par la garantie)", key=f"ref{r['id']}"):
                    sb().table("reclamations").update({"decision": "refusee", "traite_par": membre()["id"], "traitee_le": maintenant()}).eq("id", r["id"]).execute()
                    sb().table("commandes").update({"statut": "livree"}).eq("id", c["id"]).execute()
                    ok("Réclamation refusée. Explique la raison à l'acheteur.")


def page_vendeurs_a_payer():
    st.header("Vendeurs à payer")
    st.caption("Étape 8 : garantie terminée sans réclamation → tu paies le vendeur, moins ta commission.")
    if not est_garant():
        st.warning("Cette étape est réservée au garant et aux admins.")
        return
    lignes = sb().table("vendeurs_a_payer").select("*").order("fin_garantie").execute().data
    if not lignes:
        st.success("Aucun vendeur à payer pour le moment.")
    for v in lignes:
        with st.expander(f"{v['vendeur']} ({v['telephone']}) — {v['code_vg']} {v['titre']} : {fcfa(v['montant_a_verser'])}", expanded=True):
            st.write(f"Prix de vente {fcfa(v['montant_vente'])} − commission {fcfa(v['commission'])} = **{fcfa(v['montant_a_verser'])}**")
            ref = st.text_input("Référence du transfert Mobile Money", key=f"pv{v['commande_id']}")
            if st.button(f"J'ai payé {fcfa(v['montant_a_verser'])}", key=f"bpv{v['commande_id']}", type="primary"):
                sb().table("paiements_vendeurs").insert({
                    "commande_id": v["commande_id"], "vendeur_id": v["vendeur_id"], "montant_vente": v["montant_vente"],
                    "commission": v["commission"], "montant_verse": v["montant_a_verser"],
                    "reference_paiement": ref or None, "paye_par": membre()["id"],
                }).execute()
                sb().table("commandes").update({"statut": "terminee"}).eq("id", v["commande_id"]).execute()
                sb().table("objets").update({"statut": "vendeur_paye"}).eq("id", v["objet_id"]).execute()
                ok(f"Paiement de {v['vendeur']} enregistré. Vente {v['code_vg']} terminée.")

    st.subheader("Paiements déjà faits")
    faits = sb().table("paiements_vendeurs").select("created_at, montant_vente, commission, montant_verse, reference_paiement, vendeur:personnes(nom)") \
        .order("created_at", desc=True).limit(50).execute().data
    if faits:
        df = pd.DataFrame([{"Date": jolie_date(p["created_at"]), "Vendeur": p["vendeur"]["nom"], "Vente": p["montant_vente"],
                            "Commission": p["commission"], "Versé": p["montant_verse"], "Référence": p["reference_paiement"]} for p in faits])
        st.dataframe(df, hide_index=True, width="stretch")
        st.metric("Commissions encaissées (50 derniers paiements)", fcfa(df["Commission"].sum()))


def page_registre():
    st.header("Registre")
    st.caption("Chaque changement d'étape est noté automatiquement, avec la date et la personne.")
    objets = sb().table("objets").select("id, code_vg, titre, statut, prix_vente, vendeur:personnes(nom)").order("id", desc=True).execute().data
    if objets:
        st.dataframe(pd.DataFrame([{"Code": o["code_vg"], "Objet": o["titre"], "Vendeur": o["vendeur"]["nom"],
                                    "Prix": o["prix_vente"], "Étape": STATUTS_OBJET[o["statut"]]} for o in objets]),
                     hide_index=True, width="stretch")
        code = st.selectbox("Historique d'un objet", [o["code_vg"] for o in objets])
        oid = next(o["id"] for o in objets if o["code_vg"] == code)
        equipe = {e["user_id"]: e["nom"] for e in sb().table("equipe").select("user_id, nom").execute().data}
        mvts = sb().table("mouvements").select("*").eq("objet_id", oid).order("created_at").execute().data
        st.dataframe(pd.DataFrame([{"Date": jolie_date(m["created_at"]),
                                    "De": STATUTS_OBJET.get(m["statut_avant"], "—"),
                                    "Vers": STATUTS_OBJET[m["statut_apres"]],
                                    "Par": equipe.get(m["par_user"], "—")} for m in mvts]),
                     hide_index=True, width="stretch")
    else:
        st.info("Le registre est vide pour l'instant.")


def page_equipe():
    st.header("Équipe")
    equipe = sb().table("equipe").select("*").order("id").execute().data
    st.dataframe(pd.DataFrame([{"Nom": e["nom"], "E-mail": e["email"], "Rôle": ROLES[e["role"]],
                                "Compte relié": "oui" if e["user_id"] else "pas encore", "Actif": e["actif"]} for e in equipe]),
                 hide_index=True, width="stretch")
    if membre()["role"] != "garant" and membre()["role"] != "admin":
        return
    st.subheader("Ajouter un membre")
    with st.form("ajout_membre"):
        c1, c2, c3, c4 = st.columns(4)
        nom = c1.text_input("Nom")
        email = c2.text_input("E-mail")
        tel = c3.text_input("Téléphone")
        role = c4.selectbox("Rôle", ["verificateur", "livreur", "admin"], format_func=ROLES.get)
        if st.form_submit_button("Ajouter"):
            if not nom.strip() or not email.strip():
                st.error("Nom et e-mail obligatoires.")
            else:
                sb().table("equipe").insert({"nom": nom.strip(), "email": email.strip().lower(),
                                             "telephone": tel or None, "role": role}).execute()
                ok(f"{nom} ajouté. Il crée son mot de passe avec « Première connexion ».")
    st.subheader("Activer ou désactiver")
    autres = [e for e in equipe if e["role"] != "garant"]
    if autres:
        e = st.selectbox("Membre", autres, format_func=lambda e: f"{e['nom']} ({'actif' if e['actif'] else 'inactif'})")
        if st.button("Désactiver" if e["actif"] else "Réactiver"):
            sb().table("equipe").update({"actif": not e["actif"]}).eq("id", e["id"]).execute()
            ok("Modification enregistrée.")


# ---------- Application ----------

if "user" not in st.session_state:
    ecran_connexion()
    st.stop()

if "membre" not in st.session_state:
    charger_membre()

m = membre()
PAGES = {
    "📊 Tableau de bord": page_tableau_de_bord,
    "📥 Nouveau dépôt": page_nouveau_depot,
    "🔍 Vérification": page_verification,
    "📢 Publication": page_publication,
    "🛒 Commandes": page_commandes,
    "🛡️ Garanties": page_garanties,
    "💸 Vendeurs à payer": page_vendeurs_a_payer,
    "📒 Registre": page_registre,
    "👥 Équipe": page_equipe,
}
with st.sidebar:
    logo(grand=False)
    st.write(f"{m['nom']} · {ROLES[m['role']]}")
    page = st.radio("Menu", list(PAGES), label_visibility="collapsed")
    if st.button("Se déconnecter"):
        deconnexion()

if msg := st.session_state.pop("flash", None):
    st.success(msg)

PAGES[page]()
