import streamlit as st
import pandas as pd
from datetime import datetime
from database import init_db, get_connection
from user_auth import login_user, create_user
import matplotlib.pyplot as plt
from io import BytesIO
from fpdf import FPDF

init_db()
conn = get_connection()

def df_to_pdf(df, title="Report"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, title, ln=True, align="C")
    pdf.ln(10)

    col_width = pdf.w / (len(df.columns) + 1)
    row_height = pdf.font_size * 1.5

    for col_name in df.columns:
        pdf.cell(col_width, row_height, str(col_name), border=1)
    pdf.ln(row_height)

    for _, row in df.iterrows():
        for item in row:
            pdf.cell(col_width, row_height, str(item), border=1)
        pdf.ln(row_height)

    pdf_output = BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)
    return pdf_output

if "logged_in" not in st.session_state:
    st.title("🎨 Paint Inventory Login")
    with st.form("login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            user = login_user(username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.username = user[1]
                st.session_state.role = user[3]
                st.experimental_rerun()
            else:
                st.error("Invalid credentials")
else:
    role = st.session_state.role
    st.sidebar.title("Paint Inventory System")
    st.sidebar.success(f"{st.session_state.username} ({role})")

    if st.sidebar.button("🔓 Logout"):
        st.session_state.clear()
        st.experimental_rerun()

    pages = {
        'admin': ["Purchase", "Sale", "Inventory", "Accounting", "User Management", "Manage Data"],
        'staff': ["Purchase", "Sale", "Inventory", "Manage Data"],
        'accountant': ["Inventory", "Accounting"]
    }

    choice = st.sidebar.selectbox("📁 Navigate", pages.get(role, []))

    def purchase_page():
        st.header("🛒 Add Purchase")
        with st.form("purchase_form"):
            date = st.date_input("Date", datetime.today())
            supplier = st.text_input("Supplier")
            ptype = st.text_input("Paint Type")
            color = st.text_input("Color")
            qty = st.number_input("Quantity (L)", 0.0)
            cost = st.number_input("Unit Cost (₹)", 0.0)
            if st.form_submit_button("Submit"):
                total = qty * cost
                conn.execute("INSERT INTO purchases VALUES (NULL,?,?,?,?,?,?,?)",
                             (date.isoformat(), supplier, ptype, color, qty, cost, total))
                conn.commit()
                st.success(f"Recorded purchase: ₹{total:.2f}")

    def sales_page():
        st.header("💸 Record a Sale")
        with st.form("sale_form"):
            date = st.date_input("Date", datetime.today())
            customer = st.text_input("Customer")
            ptype = st.text_input("Paint Type")
            color = st.text_input("Color")
            qty = st.number_input("Quantity Sold (L)", 0.0)
            price = st.number_input("Unit Price (₹)", 0.0)
            if st.form_submit_button("Submit"):
                total = qty * price
                conn.execute("INSERT INTO sales VALUES (NULL,?,?,?,?,?,?,?)",
                             (date.isoformat(), customer, ptype, color, qty, price, total))
                conn.commit()
                st.success(f"Recorded sale: ₹{total:.2f}")

    def inventory_page():
        st.header("📦 Inventory")
        df_p = pd.read_sql("SELECT type, color, SUM(qty) AS purchased FROM purchases GROUP BY type, color", conn)
        df_s = pd.read_sql("SELECT type, color, SUM(qty) AS sold FROM sales GROUP BY type, color", conn)
        df = pd.merge(df_p, df_s, on=["type", "color"], how="left").fillna(0)
        df["stock"] = df["purchased"] - df["sold"]
        df = df[df["stock"] > 0]

        st.dataframe(df)

        inv_chart = df.groupby("type")["stock"].sum().reset_index()
        st.bar_chart(inv_chart.set_index("type"))

        csv = df.to_csv(index=False).encode()
        st.download_button("⬇️ Download Inventory CSV", csv, "inventory.csv")

        pdf_bytes = df_to_pdf(df, title="Paint Inventory Report")
        st.download_button("📄 Download Inventory PDF", pdf_bytes, "inventory.pdf")

    def accounting_page():
        st.header("📊 Accounting")

        p_df = pd.read_sql("SELECT date, total_cost FROM purchases", conn)
        s_df = pd.read_sql("SELECT date, total_sale FROM sales", conn)

        p_df['date'] = pd.to_datetime(p_df['date'])
        s_df['date'] = pd.to_datetime(s_df['date'])

        p_total = p_df['total_cost'].sum()
        s_total = s_df['total_sale'].sum()

        st.metric("Total Purchases (₹)", f"₹{p_total:.2f}")
        st.metric("Total Sales (₹)", f"₹{s_total:.2f}")
        st.metric("Profit (₹)", f"₹{s_total - p_total:.2f}")

        st.write("### Weekly Sales")
        st.line_chart(s_df.set_index("date").resample('W').sum())

        st.write("### Weekly Purchases")
        st.line_chart(p_df.set_index("date").resample('W').sum())

    def user_mgmt_page():
        st.header("👥 User Management")
        with st.form("user_form"):
            new_user = st.text_input("New Username")
            new_pw = st.text_input("New Password", type="password")
            new_role = st.selectbox("Role", ["staff", "accountant", "admin"])
            if st.form_submit_button("Add User"):
                if create_user(new_user, new_pw, new_role):
                    st.success("User created")
                else:
                    st.error("Username exists or error occurred")

    def manage_data():
        st.header("🧾 Manage Records")

        tab1, tab2 = st.tabs(["🛒 Purchases", "💸 Sales"])

        with tab1:
            df = pd.read_sql("SELECT * FROM purchases", conn)
            st.dataframe(df)
            pid = st.number_input("Purchase ID to Delete", min_value=0)
            if st.button("Delete Purchase"):
                conn.execute("DELETE FROM purchases WHERE id=?", (pid,))
                conn.commit()
                st.success(f"Deleted purchase ID {pid}")

        with tab2:
            df = pd.read_sql("SELECT * FROM sales", conn)
            st.dataframe(df)
            sid = st.number_input("Sale ID to Delete", min_value=0)
            if st.button("Delete Sale"):
                conn.execute("DELETE FROM sales WHERE id=?", (sid,))
                conn.commit()
                st.success(f"Deleted sale ID {sid}")

    if choice == "Purchase":
        purchase_page()
    elif choice == "Sale":
        sales_page()
    elif choice == "Inventory":
        inventory_page()
    elif choice == "Accounting":
        accounting_page()
    elif choice == "User Management" and role == "admin":
        user_mgmt_page()
    elif choice == "Manage Data":
        manage_data()
