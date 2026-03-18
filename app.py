import streamlit as st
import pandas as pd
import google.generativeai as genai
import plotly.express as px

# --- 1. SETTINGS ---
st.set_page_config(page_title="Aetherium PhonePe Intel", layout="wide")

# Premium CSS Styling
st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    .stHeader { background-color: white; padding: 2rem; border-bottom: 1px solid #e2e8f0; }
    .reportview-container .main .block-container { padding-top: 2rem; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. AI CORE ---
def categorize_spends(merchant_list):
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Act as a Personal Finance Expert. Categorize these transaction descriptions:
        {merchant_list}
        Return ONLY categories (Food, Transport, Shopping, Bills, Investment, Rent) separated by commas.
        """
        response = model.generate_content(prompt)
        return [c.strip() for c in response.text.split(',')]
    except Exception as e:
        st.error(f"AI Connection Error: {e}")
        return ["Uncategorized"] * len(merchant_list)

# --- 3. THE INTERFACE ---
st.title("🛡️ PhonePe Strategic Intelligence")
st.write("Welcome back, **Sushma**. Upload your Excel statement to generate insights.")

uploaded_file = st.file_uploader("Upload PhonePe Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
    # Read the Excel file
    df = pd.read_excel(uploaded_file)
    
    st.subheader("Data Preview")
    st.dataframe(df.head(3), use_container_width=True)

    # COLUMN MAPPING (This prevents the 'Crap Output' error)
    st.info("Verify your columns below:")
    col1, col2 = st.columns(2)
    merchant_col = col1.selectbox("Select 'Details/Merchant' Column", df.columns)
    amount_col = col2.selectbox("Select 'Amount' Column", df.columns)

    if st.button("🚀 Run AI Audit", use_container_width=True):
        with st.spinner("Classifying transactions..."):
            # Process the top 20 rows for efficiency
            data_to_process = df.head(20).copy()
            
            # Clean Amount Column (remove ₹ and commas)
            data_to_process[amount_col] = pd.to_numeric(
                data_to_process[amount_col].astype(str).str.replace(r'[^\d.]', '', regex=True), 
                errors='coerce'
            ).fillna(0)

            # AI Classification
            merchants = data_to_process[merchant_col].astype(str).tolist()
            categories = categorize_spends(merchants)
            data_to_process['AI_Category'] = categories[:len(data_to_process)]

            # --- DASHBOARD ---
            st.divider()
            m1, m2 = st.columns(2)
            
            with m1:
                fig = px.pie(data_to_process, values=amount_col, names='AI_Category', 
                             hole=0.5, title="Spending Velocity by Category")
                st.plotly_chart(fig, use_container_width=True)
                
            with m2:
                st.subheader("🤖 Strategic Insights")
                total_spent = data_to_process[amount_col].sum()
                insight_prompt = f"Total spent is {total_spent}. Categories: {categories}. Give 2 high-performance tips for Sushma."
                
                model = genai.GenerativeModel('gemini-1.5-flash')
                res = model.generate_content(insight_prompt)
                st.info(res.text)

            st.subheader("Detailed Classified Ledger")
            st.dataframe(data_to_process, use_container_width=True)
