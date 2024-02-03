import pandas as pd

pd.options.display.float_format = "{:,.2f}".format

from FinancialScrapers.DataManager.data_manager import DataManager


class Asset:
    def __init__(self, ticker: str, in_x: str = "thousands") -> None:
        self.ticker = ticker.upper()
        self.in_x = in_x
        self.income_statement = pd.DataFrame()
        self.balance_sheet = pd.DataFrame()
        self.cash_flow = pd.DataFrame()

        self.data_manager = DataManager(
            "D:\\FinancialData\\FinancialData", "D:\\ChromeDriver\\chrome_driver.exe"
        )

        # Metrics
        self.per_share = pd.DataFrame()
        self.margins = pd.DataFrame()
        self.operating_expenses_breakdown = pd.DataFrame()
        self.yeilds = pd.DataFrame()

        self.thousand_params = [
            "Thousands",
            "thousands",
            "Thousand",
            "thousand",
            "T",
            "t",
            "Th",
            "th",
            "1000",
            "1,000",
            1000,
        ]
        self.million_params = [
            "Millions",
            "millions",
            "Million",
            "million",
            "M",
            "m",
            "Mi",
            "mi",
            "1000000",
            "1,000,000",
            1000000,
        ]
        self.billion_params = [
            "Billions",
            "billions",
            "Billion",
            "billion",
            "B",
            "b",
            "1000000000",
            "1,000,000,000",
            1000000000,
        ]
        self.no_scaling = ["None", None, "no", 1, "1", 0, "0"]

    def set_income_statement(self, df: pd.DataFrame) -> None:
        self.income_statement = df.fillna(0)
        if self.income_statement.columns[0] == "Unnamed: 0":
            self.income_statement.set_index("Unnamed: 0", inplace=True)
            self.income_statement.index.rename("index", inplace=True)
        self.income_statement.drop("reportedCurrency", inplace=True)
        for c in self.income_statement.columns:
            self.income_statement[c] = pd.to_numeric(
                self.income_statement[c], errors="coerce"
            )

        # If the stock has not had any splits, then
        # Set price & marketcap data
        price_data = self.get_matching_stock_prices(self.income_statement.columns)
        scaler = self.get_scaler()
        self.income_statement.loc["marketcap_high"] = price_data["marketcap"]["high"]
        self.income_statement.loc["marketcap_low"] = price_data["marketcap"]["low"]
        self.income_statement.loc["marketcap_average"] = price_data["marketcap"][
            "average"
        ]
        self.income_statement.div(scaler)
        for i in self.income_statement.index:
            self.income_statement.loc[i] = self.income_statement.loc[i].div(scaler)
        # Put stocks into dataframe *after* the dataframe is scaled. We *do not* want to scale the price.
        self.income_statement.loc["stock_high"] = price_data["price"]["high"]
        self.income_statement.loc["stock_low"] = price_data["price"]["low"]
        self.income_statement.loc["stock_average"] = price_data["price"]["average"]

        # *WARNING&* Must adjust prices for stock splits. Otherwise marketcap values will be incorrect.
        try:
            stock_split = self.data_manager.get_stock_split(self.ticker)
            print(f"Stock Split: {stock_split}")
            self.apply_stock_splits(self.income_statement, stock_split)
        except KeyError:
            pass

        print(f"DF: {self.balance_sheet.loc['commonStockSharesOutstanding']}")

    def get_income_statement(self) -> pd.DataFrame:
        return self.income_statement

    def set_balance_sheet(self, df: pd.DataFrame) -> None:
        self.balance_sheet = df.fillna(0)
        if self.balance_sheet.columns[0] == "Unnamed: 0":
            self.balance_sheet.set_index("Unnamed: 0", inplace=True)
            self.balance_sheet.index.rename("index", inplace=True)
        self.balance_sheet.drop("reportedCurrency", inplace=True)
        # Convert every column into a float.
        for c in self.balance_sheet.columns:
            self.balance_sheet[c] = pd.to_numeric(
                self.balance_sheet[c], errors="coerce"
            )
        # Current/Non-current Assets & Liabilities
        total_assets_row = self.balance_sheet.loc["totalAssets"]
        current_assets_row = self.balance_sheet.loc["totalCurrentAssets"]
        total_liabilities_row = self.balance_sheet.loc["totalLiabilities"]
        current_liabilities_row = self.balance_sheet.loc["totalCurrentLiabilities"]

        # Calculate net asset figures.
        self.balance_sheet.loc["net_total_assets"] = (
            total_assets_row - total_liabilities_row
        ) * 100
        self.balance_sheet.loc["net_current_assets"] = (
            current_assets_row - current_liabilities_row
        ) * 100
        self.balance_sheet.loc["current_ratio"] = (
            current_assets_row / current_liabilities_row
        ).fillna(0)
        # Set price & marketcap data
        price_data = self.get_matching_stock_prices(self.balance_sheet.columns)
        scaler = self.get_scaler()
        self.balance_sheet.loc["marketcap_high"] = price_data["marketcap"]["high"]
        self.balance_sheet.loc["marketcap_low"] = price_data["marketcap"]["low"]
        self.balance_sheet.loc["marketcap_average"] = price_data["marketcap"]["average"]
        self.balance_sheet.div(scaler)
        # Divide every row in dataframe by the scaler.
        for i in self.income_statement.index:
            self.income_statement.loc[i] = self.income_statement.loc[i].div(scaler)
        # Put stocks into dataframe *after* the dataframe is scaled. We *do not* want to scale the price.
        self.balance_sheet.loc["stock_high"] = price_data["price"]["high"]
        self.balance_sheet.loc["stock_low"] = price_data["price"]["low"]
        self.balance_sheet.loc["stock_average"] = price_data["price"]["average"]

    def get_balance_sheet(self) -> pd.DataFrame:
        return self.balance_sheet

    def set_cash_flow(self, df: pd.DataFrame) -> None:
        self.cash_flow = df.fillna(0)
        if self.cash_flow.columns[0] == "Unnamed: 0":
            self.cash_flow.set_index("Unnamed: 0", inplace=True)
            self.cash_flow.index.rename("index", inplace=True)
        self.cash_flow.drop("reportedCurrency", inplace=True)
        # Convert every column into a float.
        for c in self.cash_flow.columns:
            self.cash_flow[c] = pd.to_numeric(self.cash_flow[c], errors="coerce")
        # Set price & marketcap data
        price_data = self.get_matching_stock_prices(self.cash_flow.columns)
        scaler = self.get_scaler()
        self.cash_flow.loc["marketcap_high"] = price_data["marketcap"]["high"]
        self.cash_flow.loc["marketcap_low"] = price_data["marketcap"]["low"]
        self.cash_flow.loc["marketcap_average"] = price_data["marketcap"]["average"]
        self.cash_flow.div(scaler)
        # Divide every row in dataframe by the scaler.
        for i in self.cash_flow.index:
            self.cash_flow.loc[i] = self.cash_flow.loc[i].div(scaler)
        # Put stocks into dataframe *after* the dataframe is scaled. We *do not* want to scale the price.
        self.cash_flow.loc["stock_high"] = price_data["price"]["high"]
        self.cash_flow.loc["stock_low"] = price_data["price"]["low"]
        self.cash_flow.loc["stock_average"] = price_data["price"]["average"]

    def get_cash_flow(self) -> pd.DataFrame:
        return self.cash_flow

    def set_all_statements(
        self,
        income_statement: pd.DataFrame,
        balance_sheet: pd.DataFrame,
        cash_flow: pd.DataFrame,
    ) -> None:
        self.set_balance_sheet(
            balance_sheet
        )  # Balance sheet *must* be set first since it contains outstanding shares data.
        self.set_income_statement(income_statement)
        self.set_cash_flow(cash_flow)
        # All statements must be set before functions below are called.
        self.set_per_share_data()
        self.set_operating_expense_breakdown()
        self.set_margins()
        self.set_yields()

    def set_per_share_data(self):

        common_shares_outstanding_row = self.balance_sheet.loc[
            "commonStockSharesOutstanding"
        ].astype(float)

        # Cash per share
        self.per_share["cash"] = (
            self.balance_sheet.loc["cashAndShortTermInvestments"].astype(float)
            / common_shares_outstanding_row
        ).fillna(0)
        # Debt per share
        self.per_share["short_term_debt"] = (
            self.balance_sheet.loc["shortTermDebt"].astype(float)
            / common_shares_outstanding_row
        ).fillna(0)
        self.per_share["long_term_debt"] = (
            self.balance_sheet.loc["longTermDebt"].astype(float)
            / common_shares_outstanding_row
        ).fillna(0)
        # Book value per share
        self.per_share["book"] = (
            self.balance_sheet.loc["totalShareholderEquity"].astype(float)
            / common_shares_outstanding_row
        ).fillna(0)
        # Dividends
        self.per_share["dividends"] = (
            self.cash_flow.loc["dividendPayout"].astype(float)
            / common_shares_outstanding_row
        ).fillna(0)
        self.per_share["common_stock_dividend"] = (
            self.cash_flow.loc["dividendPayoutCommonStock"].astype(float)
            / common_shares_outstanding_row
        ).fillna(0)
        self.per_share["preferred_stock_dividends"] = (
            self.cash_flow.loc["dividendPayoutPreferredStock"].astype(float)
            / common_shares_outstanding_row
        ).fillna(0)
        # Share buybacks
        self.per_share["share_buy_backs"] = (
            self.cash_flow.loc["paymentsForRepurchaseOfCommonStock"].astype(float)
            / common_shares_outstanding_row
        ).fillna(0)
        self.per_share["preferred_share_buy_backs"] = (
            self.cash_flow.loc["paymentsForRepurchaseOfPreferredStock"].astype(float)
            / common_shares_outstanding_row
        ).fillna(0)

        self.per_share = (
            self.per_share.T
        )  # Transpose dataframe so dates are the in the column headers.

    def set_margins(self):

        total_revenue_row = self.income_statement.loc["totalRevenue"].astype(float)
        gross_profit_row = self.income_statement.loc["grossProfit"].astype(float)
        operating_income_row = self.income_statement.loc["operatingIncome"].astype(
            float
        )
        net_income_row = self.income_statement.loc["netIncome"].astype(float)
        self.margins["gross_margin"] = (gross_profit_row / total_revenue_row) * 100
        self.margins["operating_margin"] = (
            operating_income_row / total_revenue_row
        ) * 100
        self.margins["net_profit_margin"] = (net_income_row / total_revenue_row) * 100

        self.margins = self.margins.T

    def set_operating_expense_breakdown(self):
        # Operating Expense portions.
        rd_row = self.income_statement.loc["researchAndDevelopment"].astype(float)
        sga_row = self.income_statement.loc["sellingGeneralAndAdministrative"].astype(
            float
        )
        operating_expenses_row = (
            self.income_statement.loc["operatingExpenses"].astype(float).fillna(0)
        )
        self.operating_expenses_breakdown["r&d"] = (
            rd_row / operating_expenses_row
        ) * 100
        self.operating_expenses_breakdown["sg&a"] = (
            sga_row / operating_expenses_row
        ) * 100

        self.operating_expenses_breakdown = self.operating_expenses_breakdown.T

    def set_yields(self):
        # Cash & Debt
        cash = self.balance_sheet.loc["cashAndShortTermInvestments"]
        short_term_debt = self.balance_sheet.loc["shortTermDebt"]
        long_term_debt = self.balance_sheet.loc["longTermDebt"]
        # Common & Preferred Shares
        common_share_buy_backs = self.cash_flow.loc[
            "paymentsForRepurchaseOfCommonStock"
        ]
        preferred_share_buy_backs = self.cash_flow.loc[
            "paymentsForRepurchaseOfPreferredStock"
        ]
        dividends = self.cash_flow.loc["dividendPayoutCommonStock"]
        preferred_dividends = self.cash_flow.loc["dividendPayoutPreferredStock"]
        # Marketcap
        marketcap_average = self.balance_sheet.loc["marketcap_average"]
        self.yeilds["cash"] = (cash / marketcap_average) * 100
        self.yeilds["short_term_debt"] = (short_term_debt / marketcap_average) * 100
        self.yeilds["long_term_debt"] = (long_term_debt / marketcap_average) * 100
        self.yeilds["share_buy_backs"] = (
            common_share_buy_backs / marketcap_average
        ) * 100
        self.yeilds["preferred_share_buy_backs"] = (
            preferred_share_buy_backs / marketcap_average
        ) * 100
        self.yeilds["dividends"] = (dividends / marketcap_average) * 100
        self.yeilds["preferred_dividends"] = (
            preferred_dividends / marketcap_average
        ) * 100

        self.yeilds = self.yeilds.T

    ############################################## Stock Prices ##############################################
    def get_matching_stock_prices(self, columns: list):

        price_data = self.data_manager.get_data(self.ticker)
        index = 0
        common_shares_col = "commonStockSharesOutstanding"
        stock_high = {}
        stock_low = {}
        stock_average = {}
        market_cap_high = {}
        market_cap_low = {}
        market_cap_average = {}
        prev_index = 0
        for i in columns:
            if index == 0:
                stock_high[i] = 0
                stock_low[i] = 0
                stock_average[i] = 0
                prev_index = i
            else:
                price_slices = price_data.loc[prev_index:i]
                slice_high = price_slices["High"].max()
                slice_low = price_slices["Low"].min()
                slice_average = price_slices["Close"].mean()

                stock_high[i] = slice_high
                stock_low[i] = slice_low
                stock_average[i] = slice_average

                try:
                    slice_mc_high = (
                        float(self.balance_sheet.loc[common_shares_col, i]) * slice_high
                    )
                except KeyError:
                    slice_mc_high = 0
                try:
                    slice_mc_low = (
                        float(self.balance_sheet.loc[common_shares_col, i]) * slice_low
                    )
                except KeyError:
                    slice_mc_low = 0
                try:
                    slice_mc_average = (
                        float(self.balance_sheet.loc[common_shares_col, i])
                        * slice_average
                    )
                except KeyError:
                    slice_mc_average = 0

                market_cap_high[i] = slice_mc_high
                market_cap_low[i] = slice_mc_low
                market_cap_average[i] = slice_mc_average
                prev_index = i

            index += 1

        return {
            "marketcap": {
                "high": market_cap_high,
                "low": market_cap_low,
                "average": market_cap_average,
            },
            "price": {"high": stock_high, "low": stock_low, "average": stock_average},
        }

    def apply_stock_splits(self, statement: pd.DataFrame, split_history: pd.DataFrame):
        pass

    def get_scaler(self) -> int:
        if self.in_x in self.thousand_params:
            return 1000
        elif self.in_x in self.million_params:
            return 1000000
        elif self.in_x in self.billion_params:
            return 1000000000
        elif self.in_x in self.no_scaling:
            return 1
