from matplotlib.patches import FancyBboxPatch
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd


class FlowDataExplorer:
    def __init__(self, analyses, cis_funds):
        self._analyses = analyses.copy(deep=True)
        self._cis_funds = cis_funds.copy(deep=True)

    def cis_funds_matching_sub_code(self, fund_code):
        codes = self._cis_funds.Fund_Code.astype(str)
        mask = codes.apply(lambda str_: str_ in fund_code)
        return self._cis_funds[mask]

    def inconsistent_fund_code_dtype(self):
        codes = self._cis_funds.Fund_Code
        mask = codes.apply(lambda str_: str_.isdigit())
        return self._cis_funds[mask]

    def inconsistent_sector_code_class_mapping(self, code, class_):
        codes = self._cis_funds.Sector_Code
        mask_1 = codes.astype(str).str.contains(code)

        classes = self._cis_funds.Sector_Classification
        mask_2 = classes.astype(str).str.contains(class_)

        return self._cis_funds[mask_1 | mask_2]

    def inconsistent_fund_code_multi_mapping(self, feature):
        funds = self._cis_funds[["Fund_Code", "Fund_Name"]].astype(str)
        funds = funds.apply(lambda s: s.str.upper()).drop_duplicates()

        mask_feat_dups = funds[feature].duplicated()
        feat_dups = funds[feature][mask_feat_dups]

        mask_multi_use = funds[feature].isin(feat_dups)
        return funds[mask_multi_use].sort_values(by=feature, ignore_index=True)

    def inconsistent_sector_code_format(self):
        modal_len = 4

        codes = self._cis_funds.Sector_Code
        mask = codes.str.len() != modal_len

        return self._cis_funds[mask]

    def inconsistent_sector_code_usage(self, code_1, code_2):
        codes = self._cis_funds.Sector_Code

        mask_1 = codes.astype(str).str.contains(code_1)
        mask_2 = codes.astype(str).str.contains(code_2)

        inconsistencies = self._cis_funds[mask_1 | mask_2]

        sectors = inconsistencies[["Sector_Code", "Sector_Classification"]]

        return (
            sectors.value_counts()
            .reset_index()
            .rename(columns={0: "Occurances"})
            .drop_duplicates()
        )

    @property
    def number_of_quarters(self):
        analyses_quarters = self._analyses.index.unique()
        cis_funds_quarters = self._cis_funds.index.unique()
        return pd.DataFrame(
            data={
                "Raw Analysis Data": len(analyses_quarters),
                "Raw CIS Funds Data": len(cis_funds_quarters),
            },
            index=["No. of Quarters"],
        )

    def plot_number_of_quarters(self):
        data = self.number_of_quarters
        return self._generate_barplot(
            data=data,
            title="Quarters in Each Data Set",
            xlabel=data.index[0],
        )

    def plot_value_counts(self):
        data = self.value_counts
        return self._generate_barplot(
            data=data,
            title="Unique Entries in Each Data Set",
            xlabel=data.index[0],
        )

    def sample_of_analysis(self, date_key):
        return self._analyses.loc[date_key].iloc[:5, :8]

    def sample_of_cis_funds(self, date_key):
        return self._cis_funds.loc[date_key].iloc[:5, :8]

    @property
    def value_counts(self):
        analysis_fund_names = self._analyses.Fund_Name.unique()
        analysis_class = self._analyses.Sector_Classification.unique()

        cis_funds_fund_names = self._cis_funds.Fund_Name.unique()
        cis_funds_class = self._cis_funds.Sector_Classification.unique()

        return pd.DataFrame(
            data={
                "Funds: Analysis": analysis_fund_names.size,
                "Funds: CIS Funds": cis_funds_fund_names.size,
                "Sectors: Analysis": analysis_class.size,
                "Sectors: CIS Funds": cis_funds_class.size,
            },
            index=["No. of Unique Values"],
        )

    @staticmethod
    def _generate_barplot(data, title, xlabel):
        BOLD = "bold"
        sns.set(
            rc={
                "axes.labelpad": 25,
                "axes.titlesize": 24,
                "figure.figsize": (10, 4),
                "font.weight": BOLD,
                "ytick.major.pad": 25,
            },
            style="white",
        )

        plot = sns.barplot(
            data=data,
            orient="h",
            palette="Blues",
        )

        patches = []

        for patch in reversed(plot.patches):
            bb = patch.get_bbox()
            color = patch.get_facecolor()

            p_bbox = FancyBboxPatch(
                xy=(bb.xmin, bb.ymin),
                width=abs(bb.width),
                height=abs(bb.height),
                boxstyle=f"round, pad=-0.25, rounding_size=2",
                ec="none",
                fc=color,
                mutation_aspect=0.2,
            )

            patch.remove()
            patches.append(p_bbox)

        for patch in patches:
            plot.add_patch(patch)

        sns.despine(left=True, bottom=True)

        plot.bar_label(plot.containers[0])
        plot.set_title(title, weight=BOLD)
        plot.set_xlabel(xlabel, fontsize=16, weight=BOLD)
        plot.set_yticklabels(data.columns)

        plt.tight_layout()
        plt.show()
