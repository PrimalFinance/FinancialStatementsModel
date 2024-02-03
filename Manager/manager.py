from FinancialScrapers.DataManager.data_manager import DataManager

from Asset.asset import Asset
from dotenv import load_dotenv

load_dotenv()
import pandas as pd
import yfinance as yf

base_path = "D:\\FinancialData\\FinancialData"
chrome_driver_path = "D:\\ChromeDriver\\chrome_driver.exe"


class Manager:
    def __init__(self, ticker: str) -> None:
        self.ticker = ticker.upper()
        self.data_manager = DataManager(base_path, chrome_driver_path)

    def test(self):
        asset = Asset(self.ticker, "th")

        # # self.data_manager.expired = 90

        income_statement = self.data_manager.get_income_statement(
            self.ticker, write_data=True
        )

        # print(f"Income: {income_statement}")
        balance_sheet = self.data_manager.get_balance_sheet(self.ticker)
        cash_flow = self.data_manager.get_cash_flow(self.ticker)

        asset.set_all_statements(income_statement, balance_sheet, cash_flow)
