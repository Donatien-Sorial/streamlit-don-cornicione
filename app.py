import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta

# --- 1. CONFIGURATION & CONNEXION ---
st.set_page_config(page_title="Don Cornicione", page_icon="🍕", layout="centered")

@st.cache_resource
def init_supabase():
    return create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])

supabase = init_supabase()

# --- 2. FONCTIONS DE DONNÉES ---
def get_menu_and_ingredients():
    pizzas = supabase.table("menu_items").select("*, menu_item_ingredients(ingredients(name))").execute().data
    all_ing = supabase.table("ingredients").select("*").execute().data
    return pizzas, all_ing

# --- 3. LOGIQUE DE L'INTERFACE ---
st.title("🍕 Don Cornicione")
st.markdown("*L'excellence à emporter - Franceville*")

# Initialisation du panier
if 'cart' not in st.session_state:
    st.session_state.cart = []

menu, all_ingredients = get_menu_and_ingredients()

# --- SECTION : AJOUT D'UNE PIZZA ---
with st.container(border=True):
    st.subheader("➕ New Pizza Line")

    pizza_names = [p['name'] for p in menu]
    selected_name = st.selectbox("Select Pizza", pizza_names)
    current_pizza = next(p for p in menu if p['name'] == selected_name)

    default_ingredients = [item['ingredients']['name'] for item in current_pizza['menu_item_ingredients']]

    all_ing_names = [i['name'] for i in all_ingredients]
    add_options = [name for name in all_ing_names if name not in default_ingredients]

    col1, col2 = st.columns(2)
    with col1:
        to_remove = st.multiselect("❌ Remove (from recipe)", default_ingredients)
    with col2:
        to_add = st.multiselect("➕ Add Extras", add_options)

    qty = st.number_input("Quantity", min_value=1, value=1)

    if st.button("Add to Order", use_container_width=True):
        extra_price = sum([float(i['price_extra']) for i in all_ingredients if i['name'] in to_add])
        unit_price = float(current_pizza['price']) + extra_price

        st.session_state.cart.append({
            "pizza_id": current_pizza['id'],
            "name": selected_name,
            "quantity": qty,
            "remove": to_remove,
            "add": to_add,
            "price": unit_price * qty
        })
        st.rerun()

# --- SECTION : RÉCAPITULATIF DU PANIER ---
if st.session_state.cart:
    st.divider()
    st.subheader("🛒 Current Order")

    total_order = 0
    for idx, item in enumerate(st.session_state.cart):
        with st.expander(f"{item['quantity']}x {item['name']} - {item['price']:.2f}€", expanded=True):
            if item['remove']: st.write(f"❌ No: {', '.join(item['remove'])}")
            if item['add']: st.write(f"➕ Extra: {', '.join(item['add'])}")
            if st.button(f"Remove item {idx+1}", key=f"del_{idx}"):
                st.session_state.cart.pop(idx)
                st.rerun()
        total_order += item['price']

    st.write(f"### Total: {total_order:.2f}€")

    # --- SECTION : VALIDATION FINALE ---
    st.divider()
    st.subheader("👤 Customer & Pickup")

    cust_name = st.text_input("Customer Name", placeholder="e.g. Marc")

    c1, c2 = st.columns(2)
    with c1:
        p_date = st.date_input("Day", datetime.now())
    with c2:
        p_time = st.time_input("Time", datetime.now().replace(hour=19, minute=0))

    remark = st.text_area("Remark (Instructions)", placeholder="Well cooked, door code 1234...")
    is_weekly = st.checkbox("🔄 Recurring weekly order")

    if st.button("🔥 SEND ORDER TO CALENDAR", use_container_width=True):
        if not cust_name:
            st.error("Please enter a name!")
        else:
            # ICI : Appel de tes fonctions Google & Supabase
            # (Je les garde en commentaire pour que tu puisses tester l'UI d'abord)
            st.balloons()
            st.success("Order sent! (Check your database and calendar)")
            # st.session_state.cart = [] # Optionnel : vider le panier