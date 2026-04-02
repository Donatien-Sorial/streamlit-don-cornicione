import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta

# --- 1. CONFIGURATION & CONNEXION ---
st.set_page_config(page_title="Don Cornicione Admin", page_icon="🍕", layout="centered")

# Personnalisation du style pour mobile
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #ff4b4b; color: white; }
    .stExpander { border: 1px solid #ddd; border-radius: 10px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def init_supabase():
    return create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])

supabase = init_supabase()

# --- 2. FONCTIONS DE DONNÉES ---
def get_menu_and_ingredients():
    # Récupère pizzas + ingrédients par défaut
    pizzas = supabase.table("menu_items").select("*, menu_item_ingredients(ingredients(name))").execute().data
    # Récupère tous les ingrédients disponibles
    all_ing = supabase.table("ingredients").select("*").execute().data
    return pizzas, all_ing

# --- 3. LOGIQUE DE L'INTERFACE ---
st.title("🍕 Don Cornicione")
st.markdown("*L'excellence à emporter - Franceville*")

# Initialisation du panier dans la session
if 'cart' not in st.session_state:
    st.session_state.cart = []

menu, tous_ingredients = get_menu_and_ingredients()

# --- SECTION : AJOUT D'UNE PIZZA ---
with st.container():
    st.subheader("➕ Ajouter une pizza")

    # A. Sélection de la Pizza
    noms_pizzas = [p['name'] for p in menu]
    nom_selectionne = st.selectbox("Choisir une pizza", noms_pizzas)
    pizza_actuelle = next(p for p in menu if p['name'] == nom_selectionne)

    # B. Filtrage des ingrédients
    # 1. Ingrédients de la recette (à enlever)
    ing_par_defaut = [item['ingredients']['name'] for item in pizza_actuelle['menu_item_ingredients']]

    # 2. Autres ingrédients (à ajouter)
    tous_noms_ing = [i['name'] for i in tous_ingredients]
    options_ajout = [nom for nom in tous_noms_ing if nom not in ing_par_defaut]

    col1, col2 = st.columns(2)
    with col1:
        a_enlever = st.multiselect("❌ Enlever", ing_par_defaut)
    with col2:
        a_ajouter = st.multiselect("➕ Ajouter (Supplément)", options_ajout)

    quantite = st.number_input("Quantité", min_value=1, value=1)

    if st.button("Ajouter au panier", use_container_width=True):
        # Calcul du prix (Base + Suppléments)
        prix_supplements = sum([float(i['price_extra']) for i in tous_ingredients if i['name'] in a_ajouter])
        prix_unitaire = float(pizza_actuelle['price']) + prix_supplements

        st.session_state.cart.append({
            "pizza_id": pizza_actuelle['id'],
            "nom": nom_selectionne,
            "quantite": quantite,
            "enlever": a_enlever,
            "ajouter": a_ajouter,
            "prix_total": prix_unitaire * quantite
        })
        st.rerun()

# --- SECTION : RÉCAPITULATIF DU PANIER ---
if st.session_state.cart:
    st.divider()
    st.subheader("🛒 Votre Commande")

    total_commande = 0
    for idx, item in enumerate(st.session_state.cart):
        with st.expander(f"{item['quantite']}x {item['nom']} - {item['prix_total']:.2f}€", expanded=True):
            if item['enlever']: st.write(f"❌ Sans : {', '.join(item['enlever'])}")
            if item['ajouter']: st.write(f"➕ Supplément : {', '.join(item['ajouter'])}")
            if st.button(f"Supprimer la ligne {idx+1}", key=f"del_{idx}"):
                st.session_state.cart.pop(idx)
                st.rerun()
        total_commande += item['prix_total']

    st.write(f"### Total à payer : {total_commande:.2f}€")

    # --- SECTION : INFORMATIONS CLIENT ---
    st.divider()
    st.subheader("👤 Vos informations")

    nom_client = st.text_input("Nom complet", placeholder="Ex: Jean Dupont")
    tel_client = st.text_input("Numéro de téléphone", placeholder="Ex: 06 12 34 56 78")

    # Bloc d'information sur la confirmation
    st.info("""
    **Note sur la confirmation :**
    - Pour les commandes dans plus de 3 jours : confirmation immédiate.
    - Pour les autres : une confirmation vous sera demandée 48h à l'avance ou rapidement selon le délai.
    """)

    c1, c2 = st.columns(2)
    with c1:
        date_p = st.date_input("Jour du retrait", datetime.now())
    with c2:
        heure_p = st.time_input("Heure du retrait", datetime.now().replace(hour=19, minute=0))

    remarque = st.text_area("Remarques éventuelles", placeholder="Ex: Cuisson bien cuite, code porte...")
    est_recurrent = st.checkbox("🔄 Commande hebdomadaire")

    if st.button("🔥 VALIDER LA COMMANDE", use_container_width=True):
        if not nom_client or not tel_client:
            st.error("Veuillez remplir votre nom et votre numéro de téléphone !")
        else:
            # Ici viendront les appels API Google et Supabase
            st.balloons()
            st.success(f"Merci {nom_client} ! Votre commande a été transmise.")
            # st.session_state.cart = []