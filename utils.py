import streamlit as st
import pandas as pd
import datetime

import streamlit


# Function to get the Average Price and filter by Year
def processed_dataset(df):

    # Loading the Symbols Database
    st.session_state["Symbol_Database"] = pd.read_csv("symbols_database.csv")
    not_found_symbols = []

    # Processes to get the Average Cost
    processed_df = df.copy()
    processed_df.loc[processed_df['Type'] == 'Venda', ['Qty']] *= -1
    processed_df['Total Shares'] = processed_df.groupby(['Symbol'])['Qty'].cumsum().reset_index(level=0, drop=True)
    processed_df.loc[processed_df['Type'] == 'Venda', ['Qty']] *= -1
    unique_symbols = processed_df['Symbol'].unique()
    for Symbol in unique_symbols:

        # If the symbol not in the database, store it in this list
        if Symbol not in st.session_state["Symbol_Database"]["Symbol"].unique():
            not_found_symbols.append(Symbol)

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

    # Converting the Date column to Date
    processed_df["Date"] = pd.to_datetime(processed_df["Date"], format="%m/%d/%Y").dt.date

    # Getting Dividends Data
    st.session_state["Dividends_Dataset"]["Date"] = pd.to_datetime(st.session_state["Dividends_Dataset"]["Date"], format="%m/%d/%Y").dt.date

    # Adding to a Session State all symbols not Found in the Database
    if not_found_symbols is not None:
        st.session_state["Symbols"] = not_found_symbols

    # Joining the Processed DF with the Database info
    processed_df = processed_df.merge(st.session_state["Symbol_Database"][st.session_state["Symbol_Database"].columns[:-1]], on='Symbol', how='left')

    return processed_df[processed_df["Date"] < datetime.datetime(st.session_state["Year"], 1, 1).date()]

# Get End of the Year Wallet
def end_of_year_wallet(df):
    # Getting just the last state of each Symbol
    end_of_year_df = df.groupby("Symbol")[["Total Shares", "Average Cost", "Category", "Name", "CNPJ"]].last().reset_index().copy()
    # Calculating the Position Cost
    end_of_year_df["Position Cost"] = end_of_year_df["Total Shares"] * end_of_year_df["Average Cost"]
    # Joining with all dividends received in the Selected Year per Stock
    end_of_year_df = end_of_year_df.merge(
        st.session_state["Dividends_Dataset"][
            pd.DatetimeIndex(st.session_state["Dividends_Dataset"]["Date"]).year == st.session_state["Year"] - 1
        ].groupby("Symbol")["Amount"].sum(),
        on="Symbol",
        how="left"
    ).fillna(0).rename(columns={"Amount":"Dividends"})

    return end_of_year_df[end_of_year_df["Total Shares"] > 0].round(2)

# Function to automatize the Bens e Direitos declaration message
def bens_e_direitos_declaration(df, category):
    desc_array = []
    cnpj_array = []

    for index, row in df[df["Category"] == category].iterrows():
        desc_array.append(
            str(int(row["Total Shares"])) +
            (" Cotas" if category in ["FII", "ETF"] else " Ações") +
            " de " +
            row["Name"] +
            ", Código de Negociação " +
            row["Symbol"] +
            ", ao preço médio de " + ("R$" if category not in ["Stock", "Reit", "Stock ETF"] else "$") +
            str(row["Average Cost"]) +
            ". Custo total de " + ("R$" if category not in ["Stock", "Reit", "Stock ETF"] else "$") +
            str(row["Position Cost"]) + "."
        )
        cnpj_array.append(row["CNPJ"])
    df = pd.DataFrame(zip(desc_array, cnpj_array), columns=["Declaration Description", "CNPJ"])
    return df

# Function to automatize the dividends message declaration
def dividendos_declaration(df, category, type):
    df = df.merge(st.session_state["Symbol_Database"], on="Symbol", how="left")
    df = df[
        (df["Category"] == category) &
        (df["Type"] == type) &
        (pd.DatetimeIndex(df["Date"]).year == st.session_state["Year"] - 1)
    ]
    if category != "Stock":
        df = df.groupby(["CNPJ", "Name"])["Amount"].sum().reset_index()
    else:
        df["Month"] = pd.DatetimeIndex(df["Date"]).month
        df = df.groupby("Month")["Amount"].sum().reset_index()
    return df