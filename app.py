import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Don Cornicione", page_icon="🍕", layout="centered")

@st.cache_resource
def init_supabase():
    return create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])

supabase = init_supabase()

# --- 2. RÉCUPÉRATION DES DONNÉES (DATABASE) ---
def get_menu_data():
    # On garde les noms de colonnes anglais : name, price, menu_item_ingredients...
    pizzas = supabase.table("menu_items").select("*, menu_item_ingredients(ingredients(name))").execute().data
    all_ing = supabase.table("ingredients").select("*").execute().data
    return pizzas, all_ing

# --- 3. INTERFACE UTILISATEUR (FRANÇAIS) ---
st.title("🍕 Don Cornicione")
st.markdown("*L'excellence à emporter - Franceville*")

if 'cart' not in st.session_state:
    st.session_state.cart = []

menu, all_ingredients = get_menu_data()

# --- BLOC : AJOUT PIZZA ---
with st.container(border=True):
    st.subheader("➕ Ajouter une pizza")

    pizza_names = [p['name'] for p in menu]
    selected_name = st.selectbox("Sélectionnez votre pizza", pizza_names)
    current_pizza = next(p for p in menu if p['name'] == selected_name)

    # Logique de filtrage (Recette vs Extras)
    default_ingredients = [item['ingredients']['name'] for item in current_pizza['menu_item_ingredients']]
    all_ing_names = [i['name'] for i in all_ingredients]
    extra_options = [n for n in all_ing_names if n not in default_ingredients]

    col1, col2 = st.columns(2)
    with col1:
        to_remove = st.multiselect("❌ Retirer (de la recette)", default_ingredients)
    with col2:
        to_add = st.multiselect("➕ Ajouter (Supplément)", extra_options)

    qty = st.number_input("Quantité", min_value=1, value=1)

    if st.button("Ajouter au panier", use_container_width=True):
        # Calcul du prix avec colonnes : price_extra et price
        extra_fees = sum([float(i['price_extra']) for i in all_ingredients if i['name'] in to_add])
        unit_price = float(current_pizza['price']) + extra_fees

        st.session_state.cart.append({
            "menu_item_id": current_pizza['id'], # ID pour la DB
            "display_name": selected_name,       # Nom pour l'affichage
            "quantity": qty,
            "removed_ingredients": to_remove,    # Liste pour la DB
            "added_ingredients": to_add,         # Liste pour la DB
            "item_total_price": unit_price * qty # Total pour la DB
        })
        st.rerun()

# --- RÉCAPITULATIF PANIER ---
if st.session_state.cart:
    st.divider()
    st.subheader("🛒 Votre Panier")

    grand_total = 0
    for idx, item in enumerate(st.session_state.cart):
        with st.expander(f"{item['quantity']}