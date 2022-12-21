import streamlit as st
import pandas as pd
import datetime
import os
os.system("clear")

# Run Streamlit Command: streamlit run Inicio.py --theme.base "light"

# Session States
st.session_state["Flag"] = 0
st.session_state["Dataset"] = pd.DataFrame()
st.session_state["Year"] = 0

# Page Config
st.set_page_config(
    page_title="IR Calculator",
    page_icon=":money_with_wings:"
)

# Function to get the Average Price and filter by Year
def processed_dataset(df, year):
    processed_df = df.copy()

    processed_df.loc[processed_df['Type'] == 'Venda', ['Qty']] *= -1
    processed_df['Total Shares'] = processed_df.groupby(['Symbol'])['Qty'].cumsum().reset_index(level=0, drop=True)
    processed_df.loc[processed_df['Type'] == 'Venda', ['Qty']] *= -1

    unique_symbols = processed_df['Symbol'].unique()

    for Symbol in unique_symbols:
        avg_price = []
        df_filtered = processed_df[processed_df['Symbol'] == Symbol].reset_index().copy()
        for index in range(len(df_filtered)):

            # First Operation
            if index == 0:
                avg_price.append(df_filtered.iloc[0]['Cost'])

            # Started a new position again
            elif (df_filtered.iloc[index]['Qty'] == df_filtered.iloc[index]['Total Shares']) & (
                    df_filtered.iloc[index]['Type'] == 'Compra'):
                avg_price.append(df_filtered.iloc[index]['Cost'])

            # A Buy after a Buy
            elif (df_filtered.iloc[index - 1]['Type'] == 'Compra') & (df_filtered.iloc[index]['Type'] == 'Compra'):
                avg_price.append(
                    ((df_filtered.iloc[index - 1]['Total Shares'] * avg_price[index - 1]) + (
                                df_filtered.iloc[index]['Qty'] * df_filtered.iloc[index]['Cost'])) /
                    df_filtered.iloc[index]['Total Shares']
                )

            # A Sale after some Buy
            elif (df_filtered.iloc[index - 1]['Type'] == 'Compra') & (df_filtered.iloc[index]['Type'] == 'Venda'):
                avg_price.append(avg_price[index - 1])

            # A Sale after a Sale
            elif (df_filtered.iloc[index - 1]['Type'] == 'Venda') & (df_filtered.iloc[index]['Type'] == 'Venda'):
                avg_price.append(avg_price[index - 1])

            # A Buy after some Sale
            elif (df_filtered.iloc[index - 1]['Type'] == 'Venda') & (df_filtered.iloc[index]['Type'] == 'Compra'):
                avg_price.append(
                    ((df_filtered.iloc[index - 1]['Total Shares'] * avg_price[index - 1]) + (
                                df_filtered.iloc[index]['Qty'] * df_filtered.iloc[index]['Cost'])) /
                    df_filtered.iloc[index]['Total Shares']
                )

            else:
                avg_price.append('null')

        processed_df.loc[processed_df['Symbol'] == Symbol, ['Average Cost']] = avg_price

    processed_df["Date"] = pd.to_datetime(processed_df["Date"], format="%m/%d/%Y").dt.date

    return processed_df[processed_df["Date"] >= datetime.datetime(year - 1, 1, 1).date()]

# Function to highlight DataFrames rows based on Purchase or Sell
def highlight_types(df):
    return ['background-color: #9ff59f']*len(df) if df.Type == "Compra" else ['background-color: #fc9292']*len(df)

# Beginning Main Page
st.title("IR Calculator by Messias")
st.markdown("---")

with st.sidebar:
    st.title("Upload your CSV")
    form = st.form("dataset_form", clear_on_submit=False)
    file_uploaded = form.file_uploader(
        "Unformatted CSV will trow an error",
        type="csv",
        key="transaction_dataset"
    )
    st.session_state["Year"] = form.selectbox("Select the Year you want to Calculate:", [2023, 2022, 2021])

    submitted = form.form_submit_button("Submit")
    if submitted:
        try:
            transaction_df = pd.read_csv(file_uploaded)
            for column in ["Date", "Type", "Symbol", "Qty", "Cost", "Total"]:
                if column not in transaction_df.columns.tolist():
                    st.session_state["Flag"] = 2
        except:
            st.session_state["Flag"] = 2
        if st.session_state["Flag"] == 0:
            st.success("Done")
            st.session_state["Flag"] = 1
            st.session_state["Dataset"] = transaction_df
        else:
            st.error("Wrong Header")
            st.session_state["Flag"] = 0

if st.session_state["Flag"] == 1:
    st.markdown("##### :rocket: Here are all operations you've performed in " + str(st.session_state["Year"] - 1) + "!")
    st.session_state["Dataset"] = processed_dataset(st.session_state["Dataset"], st.session_state["Year"])
    st.dataframe(st.session_state["Dataset"].style.apply(highlight_types, axis=1), height=200)
    st.markdown("##### Some Metrics:")
    metrics_col = st.columns(3)
    metrics_col[0].metric("Number of Purchases", len(st.session_state["Dataset"][st.session_state["Dataset"]["Type"] == "Compra"]))
    metrics_col[1].metric("Number of Sales",
                          len(st.session_state["Dataset"][st.session_state["Dataset"]["Type"] == "Venda"]))