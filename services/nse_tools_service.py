from jugaad_data.nse import NSELive, stock_df
from datetime import date
import json

class NseToolsService:
    def __init__(self):
        self.nse_live = NSELive()

    def extract_company_data(self, company_id):
        try:
            # Fetch real-time stock data
            real_time_data = self.nse_live.stock_quote(company_id)

            if not real_time_data:
                return json.dumps({"error": "No real-time data found for the given company ID."})

            return json.dumps(real_time_data, indent=4, default=str)
        except Exception as e:
            return json.dumps({"error": str(e)})

    def get_historical_data(self, company_id, start_date, end_date):
        try:
            # Fetch historical stock data using jugaad_data
            df = stock_df(symbol=company_id, from_date=start_date, to_date=end_date, series="EQ")

            if df.empty:
                return json.dumps({"error": "No historical data found for the given company ID and date range."})

            # Convert DataFrame to JSON
            historical_data = df.to_dict(orient="records")
            return json.dumps(historical_data, indent=4, default=str)
        except Exception as e:
            return json.dumps({"error": str(e)})

    def get_10_year_historical_data(self, company_id):
        try:
            # Set the date range for the last 10 years
            start_date = date.today().replace(year=date.today().year - 10)
            end_date = date.today()

            return self.get_historical_data(company_id, start_date, end_date)
        except Exception as e:
            return json.dumps({"error": str(e)})

    def store_data_in_file(self, data, file_name):
        try:
            # Check if data is a valid JSON string
            if isinstance(data, str):
                data = json.loads(data)

            # Write data to a JSON file
            with open(file_name, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=4, default=str)

            return json.dumps({"success": f"Data successfully stored in {file_name}."})
        except Exception as e:
            return json.dumps({"error": str(e)})


