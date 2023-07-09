from datetime import datetime
from utilities import logger
from copy import deepcopy
import pandas as pd
import re
import os


class FlowExtractor:
    _log_name = "quarters_with_no_cis_funds"

    def __init__(self):
        logger.reset_logger(self._log_name)
        self.logger = logger.create_logger(self._log_name)

    def extract_sheets(self, excel_files, sheet_name, header):
        dates = [self._get_date(file) for file in excel_files]
        sheets = {}

        for date, excel in zip(dates, excel_files):
            try:
                sheets[date] = pd.read_excel(
                    io=excel,
                    sheet_name=sheet_name,
                    header=header,
                ).dropna(
                    how="all",
                    axis="index",
                )
            except ValueError:
                event = "EVENT:\t Unable to ingest CIS Funds data"
                reason = "REASON:\t No Data"
                quarter = f"QUARTER: {date}"
                error = f"\n\t{event}\n\t{reason}\n\t{quarter}\n"
                self.logger.error(error)

        return sheets

    def _get_date(self, excel):
        """AA sheet present in all publications
        expected format:
        <day: int>/<month[full word]: str>/<year: int>
        """
        index_zero = 0

        aa_sheet = pd.read_excel(excel, header=None, sheet_name="AA")

        end_of_quarter_entries = [
            entry
            for entry in aa_sheet.iloc[index_zero].unique()
            if type(entry) is str and "quarter ended" in entry.lower()
        ][index_zero]

        quarter = re.findall(
            pattern=r"\d\d.+\d\d\d\d$",
            string=end_of_quarter_entries,
        )[index_zero]

        return self._format_publication_date(quarter)

    @staticmethod
    def _format_publication_date(date_str):
        new = datetime.strptime(date_str, "%d %B %Y").strftime("%Y%m%d")
        return int(new)


class FlowStandardiser:
    _corrective_char_regex = [
        ("[(|)|/]", ""),
        ("\s+", "_"),
    ]

    _corrective_headers = [
        ("Category1", "Geography"),
        ("Category2", "Allocation"),
        ("Category3", "Portfolio"),
        ("FoF", "Fund_of_Funds"),
        ("Fundname", "Fund_Name"),
        ("Sector_Name", "Sector_Classification"),
    ]

    _date_key = "Date_Key"

    def standardise(self, sheets):
        sheets = deepcopy(sheets)

        sheets_std_header = {
            date: self._standardise_header(sheet) for date, sheet in sheets.items()
        }

        sheets_no_lead_trail_whitespace = {
            date: self._strip_lead_trail_whitespace_from_values(sheet)
            for date, sheet in sheets_std_header.items()
        }

        return self._flatten(sheets_no_lead_trail_whitespace)

    def _flatten(self, sheets):
        for date, sheet in sheets.items():
            sheet[self._date_key] = date
            sheet.set_index(self._date_key)
            sheet.index.name = self._date_key
            sheets[date] = sheet

        sheets_flat = pd.concat(sheet for sheet in sheets.values())

        return sheets_flat.set_index(self._date_key)

    def _standardise_header(self, sheet):
        corrective_pairings = [
            self._corrective_char_regex,
            self._corrective_headers,
        ]

        for pairings in corrective_pairings:
            for pattern, replace in pairings:
                sheet.columns = sheet.columns.str.replace(pattern, replace, regex=True)

        return sheet

    @staticmethod
    def _strip_lead_trail_whitespace_from_values(sheet):
        objs = sheet.dtypes == "object"

        is_str = objs[objs].index
        str_ = sheet[is_str].astype(str).applymap(str.upper).applymap(str.strip)

        is_not_str = objs[~objs].index
        str_not = sheet[is_not_str]

        return pd.concat([str_, str_not], axis="columns")


def run_preprocessing(excel_files, **sheet_to_header_map):
    extractor = FlowExtractor()
    standardiser = FlowStandardiser()
    processed = []

    for sheet, header in sheet_to_header_map.items():
        extracted = extractor.extract_sheets(excel_files, sheet, header)
        standardised = standardiser.standardise(extracted)
        processed.append(standardised)

    return processed
