import streamlit as st

# --- CONFIGURATION DES INGRÉDIENTS ---
# Tu peux stocker cette liste dans ta table 'menu_items' plus tard
AVAILABLE_INGREDIENTS = [
    "Cheese", "Ham", "Mushrooms", "Olives", "Onions",
    "Egg", "Chili Oil", "Fresh Basil", "Anchovies", "Pepperoni"
]

st.title("🍕 Don Cornicione")

# Initialisation du panier
if 'cart' not in st.session_state:
    st.session_state.cart = []

with st.expander("➕ Add a Pizza to Order", expanded=True):
    pizza_choice = st.selectbox("Select Pizza", ["Margherita", "Regina", "Don Special"])
    qty = st.number_input("Quantity", min_value=1, value=1)

    # Utilisation du multiselect pour une sélection multiple propre
    to_remove = st.multiselect("Remove ingredients", AVAILABLE_INGREDIENTS)
    to_add = st.multiselect("Add extra ingredients", AVAILABLE_INGREDIENTS)

    if st.button("Add to Cart"):
        st.session_state.cart.append({
            "pizza": pizza_choice,
            "quantity": qty,
            "remove": to_remove, # Liste d'ingrédients
            "add": to_add        # Liste d'ingrédients
        })
        st.rerun()

# --- RÉCAPITULATIF ---
if st.session_state.cart:
    st.subheader("🛒 Current Order")
    for idx, item in enumerate(st.session_state.cart):
        col_item, col_btn = st.columns([0.8, 0.2])
        with col_item:
            st.write(f"**{item['quantity']}x {item['pizza']}**")
            # Affichage propre des listes
            if item['remove']:
                st.caption(f"❌ NO: {', '.join(item['remove'])}")
            if item['add']:
                st.caption(f"➕ EXTRA: {', '.join(item['add'])}")

    st.divider()
    st.subheader("📋 Order Details")

    cust_name = st.text_input("Customer Name", placeholder="e.g. Jean Dupont")

    col_d, col_t = st.columns(2)
    with col_d:
        pickup_date = st.date_input("Pickup Day")
    with col_t:
        pickup_time = st.time_input("Pickup Time")

    # --- AJOUT DU CHAMP REMARQUE ---
    order_remark = st.text_area("Special Instructions / Remark",
                                placeholder="e.g. Well done crust, or call when ready...",
                                height=100)

    is_weekly = st.checkbox("🔄 Recurring Order (Weekly)")

    if st.button("🔥 FINALIZE ORDER", use_container_width=True):
        # Ici, 'order_remark' sera envoyé à Supabase dans la table 'orders'
        # et ajouté à la description de l'événement Google Calendar
        st.success("Order submitted with your remarks!")