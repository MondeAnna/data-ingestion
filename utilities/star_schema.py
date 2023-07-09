import pandas as pd
import os


class FlowStarSchema:
    _date_key = "Date_Key"

    _measure_names = [
        "Total_Assets",
        "Institutional_Assets",
        "Net_Flow_R",
        "Net_Flow_I",
    ]

    def __init__(self, analysis, cis_funds_fund_data, cis_funds_sector_data):
        self.analysis = analysis
        self.cis_funds_fund_data = cis_funds_fund_data
        self.cis_funds_sector_data = cis_funds_sector_data
        self.dimensions = _FlowDimensions(
            analysis, cis_funds_fund_data, cis_funds_sector_data
        )
        self.fact = self._generate_fact()

    def to_excel(self, filename):
        log_dir = f"{os.path.pardir}{os.path.sep}assets{os.path.sep}"

        if not os.path.isdir(log_dir):
            os.mkdir(log_dir)

        path = f"{log_dir}{filename}.xlsx"

        sheets = [
            (self.fact, "Fact_Assets"),
            (self.dimensions.date, "Dim_Date"),
            (self.dimensions.cis_manager, "Dim_CIS_Manager"),
            (self.dimensions.sector_classification, "Dim_Sector_Classification"),
            (self.dimensions.fund_name, "Dim_Fund_Names"),
            (self.dimensions.retail_institutional, "Dim_Retail_Institutional"),
            (self.dimensions.fund_of_funds, "Dim_Fund_of_Funds"),
            (self.dimensions.third_party, "Dim_Third_Party"),
            (self.dimensions.management_style, "Dim_Management_Style"),
            (self.analysis, "Original_Analysis"),
            (
                pd.concat(
                    objs=[
                        self.cis_funds_fund_data,
                        self.cis_funds_sector_data,
                    ],
                    axis="columns",
                ),
                "Original_CIS_Funds",
            ),
        ]

        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            for df, sheet_name in sheets:
                df.to_excel(writer, sheet_name=sheet_name)

    def _generate_fact(self):
        mapped_keys = self._map_keys()

        foreign_keys = pd.DataFrame(
            data=(series.values for series in mapped_keys.values()),
            index=mapped_keys.keys(),
        ).T

        original_length = self.analysis.shape[0]
        foreign_keys = foreign_keys.iloc[:original_length].reset_index(drop=True)

        measures = self._get_measures()

        fact = pd.concat([foreign_keys, measures], axis="columns")
        fact[self._date_key] = fact[self._date_key].astype(int)

        return fact.set_index(self._date_key)

    def _get_measures(self):
        measures = self.analysis.loc[:, self._measure_names]
        return measures.reset_index(drop=True)

    def _map_keys(self):
        mapped_keys = {self._date_key: self.analysis.index}

        for feature in self.dimensions.feat_names:
            if feature == self._date_key:
                continue

            feature_dimension = self.dimensions.__getattribute__(
                feature.lower()
            ).reset_index()

            feature_key = f"{feature}_Key"

            feature_key_mapped = pd.merge(
                left=self.analysis,
                right=feature_dimension,
                how="left",
                left_on=feature,
                right_on=feature,
            )[feature_key]

            mapped_keys[feature_key] = feature_key_mapped

        return mapped_keys


class _FlowDimensions:
    feat_names = [
        "Date_Key",
        "CIS_Manager",
        "Sector_Classification",
        "Fund_Name",
        "Retail_Institutional",
        "Fund_of_Funds",
        "Third_Party",
        "Management_Style",
    ]

    _descriptions = {
        "Fund_of_Funds": ["FUND OF FUNDS", "NOT FUND OF FUNDS"],
        "Management_Style": [
            "ASSET MANAGER",
            "BRANDED",
            "BROKER",
            "TO BE CONFIRMED",
        ],
        "Retail_Institutional": ["INSTITUIONAL", "RETAIL"],
        "Third_Party": ["NOT THIRD PARTY", "THIRD PARTY"],
    }

    _sector_class_feat = [
        "Sector_Classification",
        "Geography",
        "Allocation",
        "Portfolio",
    ]

    def __init__(self, analysis, cis_funds_fund_data, cis_funds_sector_data):
        self.analysis = analysis
        self.cis_funds_fund_data = cis_funds_fund_data
        self.cis_funds_sector_data = cis_funds_sector_data

        self.cis_manager = self._get_dimension("CIS_Manager")
        self.fund_of_funds = self._get_dimension("Fund_of_Funds")
        self.management_style = self._get_dimension("Management_Style")
        self.retail_institutional = self._get_dimension("Retail_Institutional")
        self.third_party = self._get_dimension("Third_Party")

        self.fund_name = self._get_fund_name_dimension()
        self.date = _DateDimension(analysis.index).get_dimension()
        self.sector_classification = self._get_sector_classification_dimension()

    def _get_dimension(self, feature_name):
        feature = self.analysis[feature_name]
        data = feature.sort_values().unique()

        dimension = pd.DataFrame(
            data=data,
            columns=[feature_name],
        )

        if self._descriptions.get(feature_name, None) is not None:
            dimension[f"{feature_name}_Description"] = self._descriptions[feature_name]

        return self._standardise_dimension(dimension, feature_name)

    def _get_fund_name_dimension(self):
        fund_name = "Fund_Name"
        feature = self.analysis[fund_name]
        data = feature.sort_values().unique()

        dimension = pd.DataFrame(
            data=data,
            columns=[fund_name],
        )

        dimension = pd.merge(
            left=self.cis_funds_fund_data,
            right=dimension,
            how="outer",
        )

        return self._standardise_dimension(dimension, fund_name)

    def _get_sector_classification_dimension(self):
        analysis_sector = self.analysis[self._sector_class_feat]
        analysis_sector = analysis_sector.drop_duplicates()

        classification = pd.merge(
            left=self.cis_funds_sector_data,
            right=analysis_sector,
            how="outer",
        )

        return self._standardise_dimension(classification, "Sector_Classification")

    @staticmethod
    def _standardise_dimension(dimension, feature_name):
        dimension.sort_values(by=feature_name, inplace=True)
        dimension.index = list(range(1, dimension.shape[0] + 1))
        dimension.index.name = f"{feature_name}_Key"
        return dimension


class _DateDimension:
    def __init__(self, date_keys):
        self.date_range = self._get_date_range(date_keys)

    def get_dimension(self):
        month_name_short = [name[:3].upper() for name in self.date_range.month_name()]
        month_name_long = [name.upper() for name in self.date_range.month_name()]

        week_day_name = [name.upper() for name in self.date_range.day_name()]

        date_keys = self.date_range.astype("str").str.replace("-", "").astype(int)

        semester_number = [
            self._get_semester_number(quarter) for quarter in self.date_range.quarter
        ]

        return pd.DataFrame(
            {
                "Date_Keys": date_keys,
                "Full_Date": self.date_range.date,
                "Year_Number": self.date_range.year,
                "Month_Number": self.date_range.month,
                "Month_Name_Short": month_name_short,
                "Month_Name_Long": month_name_long,
                "Week_Number": self.date_range.isocalendar().week.values,
                "Week_Day_Number": self.date_range.isocalendar().day,
                "Week_Day_Name": week_day_name,
                "Quarter_Number": self.date_range.quarter,
                "Semester_Number": semester_number,
                "Is_Month_Start": self.date_range.is_month_start,
                "Is Month End": self.date_range.is_month_end,
                "Is_Quarter_Start": self.date_range.is_quarter_start,
                "Is Quarter End": self.date_range.is_quarter_end,
                "Is_Year_Start": self.date_range.is_year_start,
                "Is Year End": self.date_range.is_year_end,
            }
        ).set_index("Date_Keys")

    @staticmethod
    def _get_date_range(date_keys):
        as_str = date_keys.astype(str)
        unique = as_str.sort_values().unique()

        year_oldest = unique[0][:4]
        year_newest = unique[-1][:4]

        start = f"{year_oldest}-01-01"
        end = f"{year_newest}-12-31"

        return pd.date_range(start, end, freq="D")

    @staticmethod
    def _get_semester_number(quarter):
        return {1: 1, 2: 1, 3: 2, 4: 2}[quarter]
