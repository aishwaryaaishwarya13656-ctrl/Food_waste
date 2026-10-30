import streamlit as st
import sqlite3
from datetime import date

st.set_page_config(
    page_title="Fresh Life Food Tracker",
    page_icon="🥗",
    layout="wide"
)

# Database connection
conn = sqlite3.connect("food.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS food (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT,
    quantity REAL,
    unit TEXT,
    purchase_date TEXT,
    expiry_date TEXT,
    status TEXT DEFAULT 'Stored'
)
""")
conn.commit()

# Page design
st.markdown("""
<style>
.stApp {
    background-color: #f5faf3;
}
h1, h2, h3 {
    color: #286747;
}
</style>
""", unsafe_allow_html=True)

st.title("🥗 Fresh Life Food Tracker")
st.write("Track food expiry. Reduce waste. Save money.")

# Navigation
page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Add Food", "Food Inventory",
     "Expiry Alerts", "Waste Reduction"]
)

# Read food items
def get_food():
    cur.execute("SELECT * FROM food ORDER BY expiry_date")
    return cur.fetchall()

items = get_food()
today = date.today()

def days_left(expiry):
    return (date.fromisoformat(expiry) - today).days

# DASHBOARD
if page == "Dashboard":
    st.header("📊 Dashboard")

    fresh = sum(
        1 for x in items
        if days_left(x[6]) > 3 and x[7] != "Used"
    )
    soon = sum(
        1 for x in items
        if 0 <= days_left(x[6]) <= 3 and x[7] != "Used"
    )
    expired = sum(
        1 for x in items
        if days_left(x[6]) < 0 and x[7] != "Used"
    )
    used = sum(1 for x in items if x[7] == "Used")

    a, b, c, d = st.columns(4)
    a.metric("Total Items", len(items))
    b.metric("Fresh", fresh)
    c.metric("Expiring Soon", soon)
    d.metric("Expired", expired)

    st.subheader("Food needing attention")
    for x in items:
        if x[7] == "Used":
            continue
        remaining = days_left(x[6])
        if remaining < 0:
            st.error(f"{x[1]}: expired {-remaining} day(s) ago")
        elif remaining <= 3:
            st.warning(
                f"{x[1]}: expires in {remaining} day(s)"
            )

    st.info(f"Items marked as used: {used}")

# ADD FOOD
elif page == "Add Food":
    st.header("➕ Add Food Item")

    with st.form("food_form"):
        name = st.text_input("Food Name")
        category = st.selectbox(
            "Category",
            ["Vegetables", "Fruits", "Dairy",
             "Cooked Food", "Grains", "Other"]
        )
        quantity = st.number_input(
            "Quantity", min_value=0.1, value=1.0
        )
        unit = st.selectbox(
            "Unit", ["kg", "g", "litre", "ml", "pieces", "pack"]
        )
        purchased = st.date_input(
            "Purchase Date", value=today
        )
        expiry = st.date_input(
            "Expiry Date", value=today
        )
        submit = st.form_submit_button("Save Food")

        if submit:
            if not name.strip():
                st.error("Please enter a food name.")
            elif expiry < purchased:
                st.error(
                    "Expiry date cannot be before purchase date."
                )
            else:
                cur.execute("""
                INSERT INTO food
                (name, category, quantity, unit,
                 purchase_date, expiry_date, status)
                VALUES (?, ?, ?, ?, ?, ?, 'Stored')
                """, (
                    name.strip(), category, quantity, unit,
                    purchased.isoformat(), expiry.isoformat()
                ))
                conn.commit()
                st.success("Food item added successfully!")
                st.rerun()

# FOOD INVENTORY
elif page == "Food Inventory":
    st.header("🧺 Food Inventory")

    if not items:
        st.info("No food items added yet.")
    else:
        for x in items:
            remaining = days_left(x[6])
            with st.expander(f"{x[1]} — {x[2]}"):
                st.write(f"Quantity: {x[3]} {x[4]}")
                st.write(f"Purchase date: {x[5]}")
                st.write(f"Expiry date: {x[6]}")
                st.write(f"Status: {x[7]}")

                if x[7] == "Used":
                    st.success("Food marked as used")
                elif remaining < 0:
                    st.error("Expired")
                elif remaining <= 3:
                    st.warning("Use soon")
                else:
                    st.success("Fresh")

                if x[7] != "Used":
                    if st.button(
                        "Mark as Used", key=f"use_{x[0]}"
                    ):
                        cur.execute(
                            "UPDATE food SET status='Used' WHERE id=?",
                            (x[0],)
                        )
                        conn.commit()
                        st.rerun()

                if st.button(
                    "Delete Item", key=f"delete_{x[0]}"
                ):
                    cur.execute(
                        "DELETE FROM food WHERE id=?",
                        (x[0],)
                    )
                    conn.commit()
                    st.rerun()

# EXPIRY ALERTS
elif page == "Expiry Alerts":
    st.header("⏰ Expiry Alerts")

    alerts = [
        x for x in items
        if x[7] != "Used" and days_left(x[6]) <= 3
    ]

    if not alerts:
        st.success("No items need an expiry alert.")
    else:
        for x in alerts:
            remaining = days_left(x[6])
            if remaining < 0:
                st.error(
                    f"{x[1]} expired {-remaining} day(s) ago."
                )
            else:
                st.warning(
                    f"{x[1]} expires in {remaining} day(s)."
                )

# WASTE REDUCTION
elif page == "Waste Reduction":
    st.header("🌱 Food Waste Reduction")

    used = [x for x in items if x[7] == "Used"]
    expired = [
        x for x in items
        if x[7] != "Used" and days_left(x[6]) < 0
    ]

    total_quantity_used = sum(x[3] for x in used)

    st.metric("Items Marked as Used", len(used))
    st.metric("Expired Items", len(expired))
    st.metric("Total Quantity Used", round(total_quantity_used, 2))

    st.write("Tips to reduce food waste:")
    st.write("- Use older food before newer food.")
    st.write("- Store food according to its label.")
    st.write("- Plan meals before buying groceries.")
    st.write("- Freeze suitable food when appropriate.")

conn.close()