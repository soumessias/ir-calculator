from utils import end_of_year_wallet, processed_dataset
from numerize.numerize import numerize
from st_aggrid import AgGrid
import streamlit as st
import pandas as pd
import os
os.system("clear")

# Run Streamlit Command: streamlit run Inicio.py --theme.base "light"

# Session States
st.session_state["Operations_Flag"] = 0
st.session_state["Operations_Dataset"] = pd.DataFrame()
st.session_state["Dividends_Flag"] = 0
st.session_state["Dividends_Dataset"] = pd.DataFrame()
st.session_state["Year"] = 0
st.session_state["Symbols"] = []

# Page Config
st.set_page_config(
    page_title="IR Calculator",
    page_icon=":money_with_wings:"
)

# Beginning Main Page
st.title("IR Calculator by Messias (2023)")
st.markdown("---")

with st.sidebar:
    st.title("Data Input:")
    form = st.form("dataset_form", clear_on_submit=False)
    operations = form.file_uploader(
        "Upload all your Operations",
        type="csv",
        key="operations_dataset",
        help="Must be an CSV following the correctly format. Check the Docs for more information."
    )
    dividends = form.file_uploader(
        "Upload all your Dividends",
        type="csv",
        key="dividends_dataset",
        help="Must be an CSV following the correctly format. Check the Docs for more information."
    )
    st.session_state["Year"] = form.selectbox("Select the Year you want to Calculate:", [2023, 2022, 2021])

    submitted = form.form_submit_button("Submit")
    if submitted:

        # Checking Operations CSV
        try:
            operations_df = pd.read_csv(operations)
            for column in ["Date", "Type", "Symbol", "Qty", "Cost", "Total"]:
                if column not in operations_df.columns.tolist():
                    st.session_state["Operations_Flag"] = 2
        except:
            st.session_state["Operations_Flag"] = 3

        # Checking Dividends CSV
        try:
            dividends_df = pd.read_csv(dividends)
            for column in ["Date", "Symbol", "Type", "Amount"]:
                if column not in dividends_df.columns.tolist():
                    st.session_state["Dividends_Flag"] = 2
        except:
            st.session_state["Dividends_Flag"] = 3

        # Conditions that should be respected
        if st.session_state["Operations_Flag"] == 0 and st.session_state["Dividends_Flag"] == 0:
            st.success(":white_check_mark: Uploaded Successfully")
            st.session_state["Operations_Flag"] = 1
            st.session_state["Dividends_Flag"] = 1
            st.session_state["Operations_Dataset"] = operations_df
            st.session_state["Dividends_Dataset"] = dividends_df
        elif st.session_state["Operations_Flag"] == 3:
            st.error(":exclamation: Operations CSV with wrong format")
            st.session_state["Operations_Flag"] = 0
        elif st.session_state["Dividends_Flag"] == 3:
            st.error(":exclamation: Dividends CSV with wrong format")
            st.session_state["Dividends_Flag"] = 0
        elif st.session_state["Operations_Flag"] == 2:
            st.error(":exclamation: Operations CSV with wrong header")
            st.session_state["Operations_Flag"] = 0
        else:
            st.error(":exclamation: Dividends CSV with wrong header")
            st.session_state["Dividends_Flag"] = 0

if st.session_state["Operations_Flag"] == 1 and st.session_state["Dividends_Flag"] == 1:

    # Getting the Processed Wallet
    processed_df = processed_dataset(st.session_state["Operations_Dataset"])
    # Getting the End of the Year Wallet
    end_of_year_df = end_of_year_wallet(processed_df)
    # Dividends of the Year
    dividends_df = st.session_state["Dividends_Dataset"]

    # Checking if any Symbol provided isn't in the Database
    if st.session_state["Symbols"] != []:
        st.error(":exclamation: Symbols not founded in the Database: " +
                 str(st.session_state["Symbols"]).replace("[", "").replace("]", "").replace("'", ""))

    # Starting the Statistics
    st.markdown("##### :moneybag: Wallet's summary for " + str(st.session_state["Year"] - 1) + "!")
    AgGrid(end_of_year_df, height=200, update_mode="NO_UPDATE", fit_columns_on_grid_load=True)
    # Metrics of the Year
    st.markdown("##### :bar_chart: Some Metrics of the Year:")
    metrics_col = st.columns(3)
    metrics_col[0].metric("Number of Purchases",
                          len(
                              processed_df[
                                  (processed_df["Type"] == "Compra") &
                                  (pd.DatetimeIndex(processed_df["Date"]).year == st.session_state["Year"] - 1)
                              ]
                          ),
                          str(
                              round(
                                      (
                                          (
                                            len(
                                              processed_df[
                                                  (processed_df["Type"] == "Compra") &
                                                  (pd.DatetimeIndex(processed_df["Date"]).year == st.session_state[
                                                      "Year"] - 1)
                                                  ]
                                            ) /
                                            len(
                                              processed_df[
                                                  (processed_df["Type"] == "Compra") &
                                                  (pd.DatetimeIndex(processed_df["Date"]).year == st.session_state[
                                                      "Year"] - 2)
                                                  ]
                                            )
                                      ) - 1
                                  ) * 100,
                                  2
                              )
                          ) +
                          "% last year (" +
                          str(
                              len(
                                  processed_df[
                                      (processed_df["Type"] == "Compra") &
                                      (pd.DatetimeIndex(processed_df["Date"]).year == st.session_state["Year"] - 2)
                                      ]
                              )
                          ) + ")"
                        )
    metrics_col[1].metric("Number of Sales",
                          len(
                              processed_df[
                                  (processed_df["Type"] == "Venda") &
                                  (pd.DatetimeIndex(processed_df["Date"]).year == st.session_state["Year"] - 1)
                                  ]
                          ),
                          str(
                              round(
                                  (
                                      (
                                          len(
                                              processed_df[
                                                  (processed_df["Type"] == "Venda") &
                                                  (pd.DatetimeIndex(processed_df["Date"]).year == st.session_state[
                                                      "Year"] - 1)
                                                  ]
                                          ) /
                                          len(
                                              processed_df[
                                                  (processed_df["Type"] == "Venda") &
                                                  (pd.DatetimeIndex(processed_df["Date"]).year == st.session_state[
                                                      "Year"] - 2)
                                                  ]
                                          )
                                      ) - 1
                                  ) * 100,
                                  2
                              )
                          ) +
                          "% last year(" +
                          str(
                              len(
                                  processed_df[
                                      (processed_df["Type"] == "Venda") &
                                      (pd.DatetimeIndex(processed_df["Date"]).year == st.session_state["Year"] - 2)
                                      ]
                              )
                          ) + ")"
                        )
    metrics_col[2].metric("Dividends Received",
                          numerize(
                              sum(
                                  dividends_df[
                                      (pd.DatetimeIndex(dividends_df["Date"]).year == st.session_state["Year"] - 1)
                                      ]["Amount"]
                              ),
                              2
                          ),
                          str(
                              round(
                                  (
                                      (
                                          sum(
                                              dividends_df[
                                                  (pd.DatetimeIndex(dividends_df["Date"]).year == st.session_state[
                                                      "Year"] - 1)
                                              ]["Amount"]
                                          ) /
                                          sum(
                                              dividends_df[
                                                  (pd.DatetimeIndex(dividends_df["Date"]).year == st.session_state[
                                                      "Year"] - 2)
                                              ]["Amount"]
                                          )
                                      ) - 1
                                  ) * 100,
                                  2
                              )
                          ) +
                          "% last year(" +
                          str(
                              numerize(
                                  sum(
                                      dividends_df[
                                          (pd.DatetimeIndex(dividends_df["Date"]).year == st.session_state[
                                              "Year"] - 2)
                                      ]["Amount"]
                                  )
                              )
                          ) + ")"

)