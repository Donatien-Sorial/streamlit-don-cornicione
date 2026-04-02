import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from datetime import time

def generate_time_slots():
    slots = []
    for hour in range(20, 23): # De 20h à 22h inclus
        for minute in [0, 15, 30, 45]:
            slots.append(f"{hour:02d}:{minute:02d}")
    slots.append("23:00") # On ajoute la dernière limite
    return slots

# --- 1. CONFIGURATION & CONNEXION ---
st.set_page_config(page_title="Don Cornicione", page_icon="🍕", layout="centered")

@st.cache_resource
def init_supabase():
    return create_client(st.secrets["supabase"]["url"], st.secrets["supabase"]["key"])

supabase = init_supabase()

# --- 2. FONCTIONS BACKEND ---

def send_to_google(order_payload, cart):
    """Envoie la commande vers Google Calendar."""
    creds = service_account.Credentials.from_service_account_info(st.secrets["google_calendar"])
    service = build('calendar', 'v3', credentials=creds)

    # Construction de la description pour l'agenda
    desc = f"📞 Tel: {order_payload['customer_phone']}\n"
    desc += f"📝 Note: {order_payload['remark']}\n\n"
    desc += "🍕 DETAILS:\n"
    for item in cart:
        desc += f"- {item['quantity']}x {item['display_name']}\n"
        if item['removed_ingredients']: desc += f"   ❌ SANS: {', '.join(item['removed_ingredients'])}\n"
        if item['added_ingredients']:   desc += f"   ➕ EXTRA: {', '.join(item['added_ingredients'])}\n"

    start_time = order_payload['pickup_datetime']
    end_time = (datetime.fromisoformat(start_time) + timedelta(minutes=20)).isoformat()

    event = {
        'summary': f"🍕 {order_payload['customer_name']}",
        'description': desc,
        'start': {'dateTime': start_time, 'timeZone': 'Europe/Paris'},
        'end': {'dateTime': end_time, 'timeZone': 'Europe/Paris'},
    }

    if order_payload['is_recurring']:
        event['recurrence'] = ['RRULE:FREQ=WEEKLY']

    res = service.events().insert(calendarId='primary', body=event).execute()
    return res.get('id')

def save_to_supabase(order_payload, cart, g_id):
    """Enregistre la commande et ses lignes dans Supabase."""
    order_payload['google_event_id'] = g_id
    # 1. Table 'orders'
    res = supabase.table("orders").insert(order_payload).execute()
    order_id = res.data[0]['id']

    # 2. Table 'order_items'
    items_data = []
    for item in cart:
        items_data.append({
            "order_id": order_id,
            "menu_item_id": item['menu_item_id'],
            "quantity": item['quantity'],
            "removed_ingredients": item['removed_ingredients'],
            "added_ingredients": item['added_ingredients'],
            "item_total_price": item['item_total_price']
        })
    supabase.table("order_items").insert(items_data).execute()

# --- 3. RÉCUPÉRATION DES DONNÉES ---
def get_menu_data():
    pizzas = supabase.table("menu_items").select("*, menu_item_ingredients(ingredients(name))").execute().data
    all_ing = supabase.table("ingredients").select("*").execute().data
    return pizzas, all_ing

# --- 4. INTERFACE ---
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

    default_ingredients = [item['ingredients']['name'] for item in current_pizza['menu_item_ingredients']]
    all_ing_names = [i['name'] for i in all_ingredients]
    extra_options = [n for n in all_ing_names if n not in default_ingredients]

    col1, col2 = st.columns(2)
    with col1:
        to_remove = st.multiselect("❌ Retirer", default_ingredients)
    with col2:
        to_add = st.multiselect("➕ Ajouter", extra_options)

    qty = st.number_input("Quantité", min_value=1, value=1)

    if st.button("Ajouter au panier", use_container_width=True):
        extra_fees = sum([float(i['price_extra']) for i in all_ingredients if i['name'] in to_add])
        unit_price = float(current_pizza['price']) + extra_fees
        st.session_state.cart.append({
            "menu_item_id": current_pizza['id'],
            "display_name": selected_name,
            "quantity": qty,
            "removed_ingredients": to_remove,
            "added_ingredients": to_add,
            "item_total_price": unit_price * qty
        })
        st.rerun()

# --- RÉCAPITULATIF ET VALIDATION ---
if st.session_state.cart:
    st.divider()
    st.subheader("🛒 Votre Panier")

    total = 0
    for idx, item in enumerate(st.session_state.cart):
        with st.expander(f"{item['quantity']}x {item['display_name']} - {item['item_total_price']:.2f}€"):
            if item['removed_ingredients']: st.write(f"❌ Sans : {', '.join(item['removed_ingredients'])}")
            if item['added_ingredients']: st.write(f"➕ Extra : {', '.join(item['added_ingredients'])}")
            if st.button(f"Supprimer ligne {idx}", key=f"del_{idx}"):
                st.session_state.cart.pop(idx)
                st.rerun()
        total += item['item_total_price']

    st.write(f"### Total : {total:.2f}€")
    st.divider()

    cust_name = st.text_input("Nom complet")
    cust_phone = st.text_input("Numéro de téléphone")

    st.info("Votre numéro sera utilisé pour une demande de confirmation : immédiate si > 3j, sinon 48h. avant le retrait")

    time_options = generate_time_slots()

    c1, c2 = st.columns(2)
    with c1:
        p_date = st.date_input("Date de retrait", datetime.now())
    with c2:
        p_time = st.selectbox("Heure de retrait", time_options, index=0)

    remark = st.text_area("Remarques")
    is_rec = st.checkbox("🔄 Commande hebdomadaire")

    if st.button("🔥 VALIDER LA COMMANDE", use_container_width=True):
        if not cust_name or not cust_phone:
            st.error("Nom et téléphone requis.")
        else:
            with st.spinner("Envoi en cours..."):
                payload = {
                    "customer_name": cust_name,
                    "customer_phone": cust_phone,
                    "pickup_datetime": datetime.combine(p_date, p_time).isoformat(),
                    "remark": remark,
                    "is_recurring": is_rec
                }
                # g_id = send_to_google(payload, st.session_state.cart)
                save_to_supabase(payload, st.session_state.cart, g_id)
                st.balloons()
                st.success("Commande enregistrée !")
                st.session_state.cart = []