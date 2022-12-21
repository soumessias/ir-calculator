import streamlit as st
import pandas as pd
import datetime

import streamlit


# Function to get the Average Price and filter by Year
def processed_dataset(df):

    # Loading the Symbols Database
    symbols_database = pd.read_csv("symbols_database.csv")
    not_found_symbols = []

    # Processes to get the Average Cost
    processed_df = df.copy()
    processed_df.loc[processed_df['Type'] == 'Venda', ['Qty']] *= -1
    processed_df['Total Shares'] = processed_df.groupby(['Symbol'])['Qty'].cumsum().reset_index(level=0, drop=True)
    processed_df.loc[processed_df['Type'] == 'Venda', ['Qty']] *= -1
    unique_symbols = processed_df['Symbol'].unique()
    for Symbol in unique_symbols:

        # If the symbol not in the database, store it in this list
        if Symbol not in symbols_database["Symbol"].unique():
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
    processed_df = processed_df.merge(symbols_database[symbols_database.columns[:-1]], on='Symbol', how='left')

    return processed_df[processed_df["Date"] < datetime.datetime(st.session_state["Year"], 1, 1).date()]

# Function to highlight DataFrames rows based on Purchase or Sell
def highlight_types(df):
    return ['background-color: #9ff59f']*len(df) if df.Type == "Compra" else ['background-color: #fc9292']*len(df)

# Get End of the Year Wallet
def end_of_year_wallet(df):
    # Getting just the last state of each Symbol
    end_of_year_df = df.groupby("Symbol")[["Total Shares", "Average Cost", "Category"]].last().reset_index().copy()
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