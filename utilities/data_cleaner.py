import pandas as pd


class AnalysisCleaner:
    _code = "Fund_Code"
    _fcis_funds = ["fcis asset allocation funds"]
    _name = "Fund_Name"

    def __init__(self, analysis):
        self._prepped_analysis = self._prepper(analysis)

    @property
    def analysis(self):
        return self._prepped_analysis

    def update(self, analysis, cis_funds):
        """a. analysis' fund names set to latest as per cis funds'
        b. fund and sector code mapped
        """
        analysis = analysis.copy(deep=True)

        sector_code = self._name_to_code(cis_funds["sectors"])
        sector_code_mapped = analysis.Sector_Classification.map(sector_code)
        analysis.insert(5, "Sector_Code", sector_code_mapped)

        fund_code = self._name_to_code(cis_funds["funds_operational"])
        analysis.Fund_Name = self._update_fund_name(analysis.Fund_Name, cis_funds)

        fund_code_mapped = analysis.Fund_Name.map(fund_code)
        analysis.insert(7, "Fund_Code", fund_code_mapped)

        return analysis

    def _code_to_name(self, series):
        col = series.columns[0]
        key = series.columns[1]
        return series.set_index(col).to_dict()[key]

    @staticmethod
    def _map_fund_name(fund_names, mapping):
        original_index = fund_names.index
        fund_names = fund_names.reset_index(drop=True)

        for index, name in enumerate(fund_names):
            name = name.upper() if name is str else name
            fund_names.iloc[index] = mapping.get(name, name)

        fund_names.index = original_index
        return fund_names

    def _name_to_code(self, series):
        col = series.columns[1]
        key = series.columns[0]
        return series.set_index(col).to_dict()[key]

    def _prepper(self, analysis):
        analysis_ = analysis.copy(deep=True)
        analysis_ = self._standardise_shorthand(analysis_)
        analysis_ = self._remove_fcis_funds(analysis_)
        return self._uppercase_object_types(analysis_)

    def _remove_fcis_funds(self, analysis):
        class_ = analysis.Sector_Classification
        mask = class_.str.lower().isin(self._fcis_funds)

        to_drop = mask[mask].dropna(how="all").index
        return analysis.drop(index=to_drop)

    def _standardise_shorthand(self, analysis):
        corrected_feat = {
            "Fund_of_Funds": analysis.Fund_of_Funds.replace("NAN", "Not_FoF"),
            "Third_Party": analysis.Third_Party.replace("NAN", "Not_TP"),
            "Management_Style": analysis.Management_Style.replace(
                {"tbc": "TBC", "NAN": "TBC"}
            ),
        }

        for feat in corrected_feat:
            analysis[feat] = corrected_feat.get(feat, analysis[feat])

        return analysis

    def _update_fund_name(self, fund_name, cis_funds):
        old_names_to_code = self._name_to_code(cis_funds["funds_archived"])
        fund_names_coded = fund_name.replace(old_names_to_code)

        code_to_new_names = self._code_to_name(cis_funds["funds_operational"])
        return fund_names_coded.replace(code_to_new_names)

    def _uppercase_object_types(self, analysis):
        objects = analysis.dtypes == "object"
        features = [feat for feat, bool_ in objects.items() if bool_]
        analysis[features] = analysis[features].apply(lambda series: series.str.upper())

        return analysis


class CISFundsCleaner:
    _feat = ["Fund_Code", "Fund_Name", "Sector_Code", "Sector_Classification"]

    def __init__(self, cis_funds):
        funds = cis_funds[self._feat].astype(str)
        self._prepped_funds = funds.apply(lambda series: series.str.upper())
        # is the str.upper still necessary?

    @property
    def cis_funds(self):
        return {
            "funds_operational": self._clean_fund_names_by_usage("operational"),
            "funds_archived": self._clean_fund_names_by_usage("archived"),
            "sectors": self._clean_sector_class(),
        }

    def _clean_fund_names_by_usage(self, state):
        funds = self._prepped_funds.copy(deep=True).reset_index()
        funds = funds[self._feat[:2]]

        unique = funds["Fund_Code"].drop_duplicates()

        funds = {
            "operational": funds.loc[unique.index],
            "archived": funds.drop(index=unique.index),
        }[state]

        funds = funds.drop_duplicates()
        funds = funds.sort_values(by="Fund_Name")

        funds.index = range(1, funds.shape[0] + 1)
        return funds

    def _clean_sector_class(self):
        """unique sector codes, ignores if not four chars long"""
        modal_len = 4
        funds = self._prepped_funds.copy(deep=True)
        funds = funds[self._feat[2:]].drop_duplicates()
        mask = funds["Sector_Code"].str.len() == modal_len
        return funds[mask].sort_values(by="Sector_Classification", ignore_index=True)
