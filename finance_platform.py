import streamlit as st
import pandas as pd
import plotly.express as px
import os
import hashlib
import io
from openai import OpenAI

# -------------------------
# CONFIG
# -------------------------

st.set_page_config(
    page_title="Finance Intelligence Platform",
    layout="wide"
)

USER_FILE = "users.csv"
DATA_FILE = "finance_data.csv"

# -------------------------
# OPENAI CLIENT
# -------------------------

client = OpenAI(api_key="YOUR_OPENAI_API_KEY")

# -------------------------
# PASSWORD HASH
# -------------------------

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# -------------------------
# USER SYSTEM
# -------------------------

def load_users():

    if os.path.exists(USER_FILE):
        return pd.read_csv(USER_FILE)

    return pd.DataFrame(columns=["username","password"])


def save_user(username,password):

    users = load_users()

    new = pd.DataFrame({
        "username":[username],
        "password":[hash_password(password)]
    })

    users = pd.concat([users,new],ignore_index=True)
    users.to_csv(USER_FILE,index=False)


def login(username,password):

    users = load_users()

    if username in users.username.values:

        stored = users.loc[users.username==username,"password"].values[0]

        if stored == hash_password(password):
            return True

    return False


# -------------------------
# SESSION STATE
# -------------------------

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""


# -------------------------
# LOGIN PAGE
# -------------------------

if not st.session_state.logged_in:

    st.title("💰 Finance Intelligence Platform")
    st.subheader("AI Powered Personal Finance Dashboard")

    menu = st.radio("Select Option",["Login","Create Account"])

    if menu == "Login":

        username = st.text_input("Username")
        password = st.text_input("Password",type="password")

        if st.button("Login"):

            if login(username,password):

                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()

            else:
                st.error("Invalid Login")

    else:

        new_user = st.text_input("Create Username")
        new_pass = st.text_input("Create Password",type="password")

        if st.button("Create Account"):

            users = load_users()

            if new_user in users.username.values:
                st.error("User already exists")

            else:
                save_user(new_user,new_pass)
                st.success("Account created. Please login.")

# -------------------------
# MAIN DASHBOARD
# -------------------------

else:

    st.sidebar.title(f"👋 Welcome {st.session_state.username}")

    if st.sidebar.button("Logout"):

        st.session_state.logged_in = False
        st.rerun()

    # -------------------------
    # LOAD DATA
    # -------------------------

    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
    else:
        df = pd.DataFrame(columns=["Date","Type","Category","Amount","Notes"])


    # -------------------------
    # ADD TRANSACTION
    # -------------------------

    st.sidebar.header("Add Transaction")

    date = st.sidebar.date_input("Date")

    type_trans = st.sidebar.selectbox("Type",["Income","Expense"])

    category = st.sidebar.selectbox(
        "Category",
        [
        "Salary","Food","Rent","Shopping",
        "Transport","Gym","Entertainment",
        "Travel","Bills","Investment",
        "Insurance","Healthcare","Education",
        "Other"
        ]
    )

    amount = st.sidebar.number_input("Amount",min_value=0)

    notes = st.sidebar.text_input("Notes")

    if st.sidebar.button("Add Transaction"):

        new = pd.DataFrame({
            "Date":[date],
            "Type":[type_trans],
            "Category":[category],
            "Amount":[amount],
            "Notes":[notes]
        })

        df = pd.concat([df,new],ignore_index=True)
        df.to_csv(DATA_FILE,index=False)

        st.rerun()


    # -------------------------
    # DASHBOARD
    # -------------------------

    st.title("📊 Financial Dashboard")

    income = df[df.Type=="Income"]["Amount"].sum()
    expense = df[df.Type=="Expense"]["Amount"].sum()
    balance = income - expense

    c1,c2,c3,c4 = st.columns(4)

    c1.metric("💰 Total Income","₹{:,.0f}".format(income))
    c2.metric("💸 Total Expense","₹{:,.0f}".format(expense))
    c3.metric("🏦 Balance","₹{:,.0f}".format(balance))
    c4.metric("🧾 Transactions",len(df))


    # -------------------------
    # PROCESS DATE
    # -------------------------

    if not df.empty:

        df["Date"] = pd.to_datetime(df["Date"])
        df["Month"] = df["Date"].dt.to_period("M").astype(str)


    # -------------------------
    # SMART MONTHLY BUDGET
    # -------------------------

    st.subheader("🧠 Smart Monthly Budget")

    budget = st.number_input("Set Monthly Budget ₹",min_value=0,step=1000)

    monthly_expense = 0

    if not df.empty:

        current_month = pd.Timestamp.today().strftime("%Y-%m")

        monthly_expense = df[
            (df["Type"]=="Expense") &
            (df["Month"]==current_month)
        ]["Amount"].sum()

    if budget > 0:

        percent = (monthly_expense / budget) * 100

        st.progress(min(percent/100,1.0))

        st.write(f"Spent this month: ₹{monthly_expense}")
        st.write(f"Budget used: {percent:.1f}%")

        if percent > 100:
            st.error("⚠️ Budget Exceeded!")

        elif percent > 80:
            st.warning("⚠️ Close to your budget limit!")

        else:
            st.success("✅ Budget under control")


    # -------------------------
    # SAVINGS RATE
    # -------------------------

    if income > 0:

        savings_rate = ((income-expense)/income)*100

        st.subheader("💡 Savings Insight")
        st.write(f"Savings Rate: **{savings_rate:.1f}%**")

        if savings_rate < 20:
            st.warning("Try to save at least 20% of your income.")

        else:
            st.success("Great saving habit!")


    # -------------------------
    # EXPENSE PIE
    # -------------------------

    if not df.empty:

        fig = px.pie(
            df[df.Type=="Expense"],
            values="Amount",
            names="Category",
            title="Expense Distribution"
        )

        st.plotly_chart(fig,use_container_width=True)


    # -------------------------
    # CATEGORY BAR
    # -------------------------

    if not df.empty:

        cat = df[df.Type=="Expense"].groupby("Category")["Amount"].sum().reset_index()

        fig2 = px.bar(
            cat,
            x="Category",
            y="Amount",
            title="Category Spending"
        )

        st.plotly_chart(fig2,use_container_width=True)


    # -------------------------
    # MONTHLY TREND
    # -------------------------

    if not df.empty:

        monthly = df.groupby(["Month","Type"])["Amount"].sum().reset_index()

        fig3 = px.bar(
            monthly,
            x="Month",
            y="Amount",
            color="Type",
            barmode="group",
            title="Monthly Income vs Expense"
        )

        st.plotly_chart(fig3,use_container_width=True)


    # -------------------------
    # TOP SPENDING CATEGORY
    # -------------------------

    st.subheader("🏆 Top Spending Category")

    if not df.empty:

        top = df[df.Type=="Expense"].groupby("Category")["Amount"].sum()

        if not top.empty:

            highest = top.idxmax()
            value = top.max()

            st.info(f"You spend the most on **{highest} (₹{value})**")


    # -------------------------
    # AI FINANCE ASSISTANT
    # -------------------------

    st.subheader("🤖 AI Finance Assistant")

    user_question = st.text_input("Ask something about your finances")

    if st.button("Ask AI"):

        prompt = f"""
        Here is my financial data:

        {df.to_string()}

        Answer this question:

        {user_question}
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"user","content":prompt}]
        )

        answer = response.choices[0].message.content

        st.success(answer)


    # -------------------------
    # TABLE
    # -------------------------

    st.subheader("Transaction History")
    st.dataframe(df,use_container_width=True)


    # -------------------------
    # EXCEL EXPORT
    # -------------------------

    st.subheader("Download Excel Report")

    excel_buffer = io.BytesIO()

    with pd.ExcelWriter(excel_buffer,engine="openpyxl") as writer:

        df.to_excel(writer,index=False,sheet_name="Transactions")

        summary = pd.DataFrame({
            "Metric":["Income","Expense","Balance"],
            "Value":[income,expense,balance]
        })

        summary.to_excel(writer,index=False,sheet_name="Summary")

    excel_data = excel_buffer.getvalue()

    st.download_button(
        label="Download Excel Report",
        data=excel_data,
        file_name="finance_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )