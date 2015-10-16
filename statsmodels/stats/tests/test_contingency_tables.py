"""
Tests for contingency table analyses.
"""

import numpy as np
import statsmodels.stats.contingency_tables as ctab
import pandas as pd
from numpy.testing import assert_allclose, assert_equal
import os
import statsmodels.api as sm

cur_dir = os.path.dirname(os.path.abspath(__file__))
fname = "contingency_table_r_results.csv"
fpath = os.path.join(cur_dir, 'results', fname)
r_results = pd.read_csv(fpath)


tables = [None, None, None]

tables[0] = np.asarray([[23, 15], [19, 31]])

tables[1] = np.asarray([[144, 33, 84, 126],
                        [2, 4, 14, 29],
                        [0, 2, 6, 25],
                        [0, 0, 1, 5]])

tables[2] = np.asarray([[20, 10, 5],
                        [3, 30, 15],
                        [0, 5, 40]])


def test_homogeneity():

    for k,table in enumerate(tables):
        st = sm.stats.SquareTable(table, shift_zeros=False)
        hm = st.homogeneity()
        assert_allclose(hm.statistic, r_results.loc[k, "homog_stat"])
        assert_allclose(hm.df, r_results.loc[k, "homog_df"])

        # Test Bhapkar via its relationship to Stuart_Maxwell.
        hmb = st.homogeneity(method="bhapkar")
        assert_allclose(hmb.statistic, hm.statistic / (1 - hm.statistic / table.sum()))


def test_SquareTable_from_data():

    np.random.seed(434)
    df = pd.DataFrame(index=range(100), columns=["v1", "v2"])
    df["v1"] = np.random.randint(0, 5, 100)
    df["v2"] = np.random.randint(0, 5, 100)
    table = pd.crosstab(df["v1"], df["v2"])

    rslt1 = ctab.SquareTable(table)
    rslt2 = ctab.SquareTable.from_data(df)
    rslt3 = ctab.SquareTable(np.asarray(table))

    assert_equal(rslt1.summary().as_text(),
                 rslt2.summary().as_text())

    assert_equal(rslt2.summary().as_text(),
                 rslt3.summary().as_text())



def test_cumulative_odds():

    table = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    table = np.asarray(table)
    tbl_obj = ctab.Table(table)

    cum_odds = tbl_obj.cumulative_oddsratios
    assert_allclose(cum_odds[0, 0], 28 / float(5 * 11))
    assert_allclose(cum_odds[0, 1], (3 * 15) / float(3 * 24), atol=1e-5,
                    rtol=1e-5)
    assert_allclose(np.log(cum_odds), tbl_obj.cumulative_log_oddsratios,
                    atol=1e-5, rtol=1e-5)


def test_local_odds():

    table = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    table = np.asarray(table)
    tbl_obj = ctab.Table(table)

    loc_odds = tbl_obj.local_oddsratios
    assert_allclose(loc_odds[0, 0], 5 / 8.)
    assert_allclose(loc_odds[0, 1], 12 / float(15), atol=1e-5,
                    rtol=1e-5)
    assert_allclose(np.log(loc_odds), tbl_obj.local_log_oddsratios,
                    atol=1e-5, rtol=1e-5)


def test_ordinal_association():

    for k,table in enumerate(tables):

        row_scores = 1 + np.arange(table.shape[0])
        col_scores = 1 + np.arange(table.shape[1])

        # First set of scores
        rslt = ctab.Table(table, shift_zeros=False).ordinal_association(row_scores, col_scores)
        assert_allclose(rslt.statistic, r_results.loc[k, "lbl_stat"])
        assert_allclose(rslt.null_mean, r_results.loc[k, "lbl_expval"])
        assert_allclose(rslt.null_sd**2, r_results.loc[k, "lbl_var"])
        assert_allclose(rslt.zscore**2, r_results.loc[k, "lbl_chi2"], rtol=1e-5, atol=1e-5)
        assert_allclose(rslt.pvalue, r_results.loc[k, "lbl_pvalue"], rtol=1e-5, atol=1e-5)

        # Second set of scores
        rslt = ctab.Table(table, shift_zeros=False).ordinal_association(row_scores, col_scores**2)
        assert_allclose(rslt.statistic, r_results.loc[k, "lbl2_stat"])
        assert_allclose(rslt.null_mean, r_results.loc[k, "lbl2_expval"])
        assert_allclose(rslt.null_sd**2, r_results.loc[k, "lbl2_var"])
        assert_allclose(rslt.zscore**2, r_results.loc[k, "lbl2_chi2"])
        assert_allclose(rslt.pvalue, r_results.loc[k, "lbl2_pvalue"], rtol=1e-5, atol=1e-5)


def test_chi2_association():

    np.random.seed(8743)

    table = np.random.randint(10, 30, size=(4, 4))

    from scipy.stats import chi2_contingency
    rslt_scipy = chi2_contingency(table)

    b = ctab.Table(table).nominal_association

    assert_allclose(b.statistic, rslt_scipy[0])
    assert_allclose(b.pvalue, rslt_scipy[1])


def test_symmetry():

    for k,table in enumerate(tables):
        st = sm.stats.SquareTable(table, shift_zeros=False)
        b = st.symmetry()
        assert_allclose(b.statistic, r_results.loc[k, "bowker_stat"])
        assert_equal(b.df, r_results.loc[k, "bowker_df"])
        assert_allclose(b.pvalue, r_results.loc[k, "bowker_pvalue"])


def test_mcnemar():

    # Use chi^2 without continuity correction
    b1 = ctab.mcnemar(tables[0], exact=False, correction=False)

    st = sm.stats.SquareTable(tables[0])
    b2 = st.homogeneity()
    assert_allclose(b1.statistic, b2.statistic)
    assert_equal(b2.df, 1)

    # Use chi^2 with continuity correction
    b3 = ctab.mcnemar(tables[0], exact=False, correction=True)
    assert_allclose(b3.pvalue, r_results.loc[0, "homog_cont_p"])

    # Use binomial reference distribution
    b4 = ctab.mcnemar(tables[0], exact=True)
    assert_allclose(b4.pvalue, r_results.loc[0, "homog_binom_p"])


def test_cochranq():
    """
    library(CVST)
    table1 = matrix(c(1, 0, 1, 1,
                      0, 1, 1, 1,
                      1, 1, 1, 0,
                      0, 1, 0, 0,
                      0, 1, 0, 0,
                      1, 0, 1, 0,
                      0, 1, 0, 0,
                      1, 1, 1, 1,
                      0, 1, 0, 0), ncol=4, byrow=TRUE)
    rslt1 = cochranq.test(table1)
    table2 = matrix(c(0, 0, 1, 1, 0,
                      0, 1, 0, 1, 0,
                      0, 1, 1, 0, 1,
                      1, 0, 0, 0, 1,
                      1, 1, 0, 0, 0,
                      1, 0, 1, 0, 0,
                      0, 1, 0, 0, 0,
                      0, 0, 1, 1, 0,
                      0, 0, 0, 0, 0), ncol=5, byrow=TRUE)
    rslt2 = cochranq.test(table2)
    """

    table = [[1, 0, 1, 1],
             [0, 1, 1, 1],
             [1, 1, 1, 0],
             [0, 1, 0, 0],
             [0, 1, 0, 0],
             [1, 0, 1, 0],
             [0, 1, 0, 0],
             [1, 1, 1, 1],
             [0, 1, 0, 0]]
    table = np.asarray(table)

    stat, pvalue, df = ctab.cochrans_q(table, return_object=False)
    assert_allclose(stat, 4.2)
    assert_allclose(df, 3)

    table = [[0, 0, 1, 1, 0],
             [0, 1, 0, 1, 0],
             [0, 1, 1, 0, 1],
             [1, 0, 0, 0, 1],
             [1, 1, 0, 0, 0],
             [1, 0, 1, 0, 0],
             [0, 1, 0, 0, 0],
             [0, 0, 1, 1, 0],
             [0, 0, 0, 0, 0]]
    table = np.asarray(table)

    stat, pvalue, df = ctab.cochrans_q(table, return_object=False)
    assert_allclose(stat, 1.2174, rtol=1e-4)
    assert_allclose(df, 4)

    # Cochran's q and Mcnemar are equivalent for 2x2 tables
    data = table[:, 0:2]
    xtab = np.asarray(pd.crosstab(data[:, 0], data[:, 1]))
    b1 = ctab.cochrans_q(data, return_object=True)
    b2 = ctab.mcnemar(xtab, exact=False, correction=False)
    assert_allclose(b1.statistic, b2.statistic)
    assert_allclose(b1.pvalue, b2.pvalue)



class CheckStratifiedMixin(object):

    def initialize(self, tables):
        self.rslt = ctab.StratifiedTables(tables)
        self.rslt_0 = ctab.StratifiedTables(tables, shift_zeros=True)
        tables_pandas = [pd.DataFrame(x) for x in tables]
        self.rslt_pandas = ctab.StratifiedTables(tables_pandas)


    def test_oddsratio_pooled(self):
        assert_allclose(self.rslt.oddsratio_pooled, self.oddsratio_pooled,
                        rtol=1e-4, atol=1e-4)


    def test_logodds_pooled(self):
        assert_allclose(self.rslt.logodds_pooled, self.logodds_pooled,
                        rtol=1e-4, atol=1e-4)


    def test_null_odds(self):
        stat, pvalue = self.rslt.test_null_odds(correction=True)
        assert_allclose(stat, self.mh_stat, rtol=1e-4, atol=1e-5)
        assert_allclose(pvalue, self.mh_pvalue, rtol=1e-4, atol=1e-4)


    def test_oddsratio_pooled_confint(self):
        lcb, ucb = self.rslt.oddsratio_pooled_confint()
        assert_allclose(lcb, self.or_lcb, rtol=1e-4, atol=1e-4)
        assert_allclose(ucb, self.or_ucb, rtol=1e-4, atol=1e-4)


    def test_logodds_pooled_confint(self):
        lcb, ucb = self.rslt.logodds_pooled_confint()
        assert_allclose(lcb, np.log(self.or_lcb), rtol=1e-4,
                        atol=1e-4)
        assert_allclose(ucb, np.log(self.or_ucb), rtol=1e-4,
                        atol=1e-4)


    def test_equal_odds(self):

        if not hasattr(self, "or_homog"):
            return

        stat, pvalue = self.rslt_0.test_equal_odds()
        assert_allclose(stat, self.or_homog, rtol=1e-4, atol=1e-4)
        assert_allclose(pvalue, self.or_homog_p, rtol=1e-4, atol=1e-4)


    def test_pandas(self):

        assert_equal(self.rslt.summary().as_text(),
                     self.rslt_pandas.summary().as_text())


    def test_from_data(self):

        np.random.seed(241)
        df = pd.DataFrame(index=range(100), columns=("v1", "v2", "strat"))
        df["v1"] = np.random.randint(0, 2, 100)
        df["v2"] = np.random.randint(0, 2, 100)
        df["strat"] = np.kron(np.arange(10), np.ones(10))

        tables = []
        for k in range(10):
            ii = np.arange(10*k, 10*(k+1))
            tables.append(pd.crosstab(df.loc[ii, "v1"], df.loc[ii, "v2"]))

        rslt1 = ctab.StratifiedTables(tables)
        rslt2 = ctab.StratifiedTables.from_data("v1", "v2", "strat", df)

        assert_equal(rslt1.summary().as_text(), rslt2.summary().as_text())


class TestStratified1(CheckStratifiedMixin):
    """
    data = array(c(0, 0, 6, 5,
                   3, 0, 3, 6,
                   6, 2, 0, 4,
                   5, 6, 1, 0,
                   2, 5, 0, 0),
                   dim=c(2, 2, 5))
    rslt = mantelhaen.test(data)
    """

    def __init__(self):

        tables = [None] * 5
        tables[0] = np.array([[0, 0], [6, 5]])
        tables[1] = np.array([[3, 0], [3, 6]])
        tables[2] = np.array([[6, 2], [0, 4]])
        tables[3] = np.array([[5, 6], [1, 0]])
        tables[4] = np.array([[2, 5], [0, 0]])

        self.initialize(tables)

        self.oddsratio_pooled = 7
        self.logodds_pooled = np.log(7)
        self.mh_stat = 3.9286
        self.mh_pvalue = 0.04747
        self.or_lcb = 1.026713
        self.or_ucb = 47.725133


class TestStratified2(CheckStratifiedMixin):
    """
    data = array(c(20, 14, 10, 24,
                   15, 12, 3, 15,
                   3, 2, 3, 2,
                   12, 3, 7, 5,
                   1, 0, 3, 2),
                   dim=c(2, 2, 5))
    rslt = mantelhaen.test(data)
    """

    def __init__(self):
        tables = [None] * 5
        tables[0] = np.array([[20, 14], [10, 24]])
        tables[1] = np.array([[15, 12], [3, 15]])
        tables[2] = np.array([[3, 2], [3, 2]])
        tables[3] = np.array([[12, 3], [7, 5]])
        tables[4] = np.array([[1, 0], [3, 2]])

        self.initialize(tables)

        self.oddsratio_pooled = 3.5912
        self.logodds_pooled = np.log(3.5912)

        self.mh_stat = 11.8852
        self.mh_pvalue = 0.0005658

        self.or_lcb = 1.781135
        self.or_ucb = 7.240633


class TestStratified3(CheckStratifiedMixin):
    """
    data = array(c(313, 512, 19, 89,
                   207, 353, 8, 17,
                   205, 120, 391, 202,
                   278, 139, 244, 131,
                   138, 53, 299, 94,
                   351, 22, 317, 24),
                   dim=c(2, 2, 6))
    rslt = mantelhaen.test(data)
    """

    def __init__(self):

        tables = [None] * 6
        tables[0] = np.array([[313, 512], [19, 89]])
        tables[1] = np.array([[207, 353], [8, 17]])
        tables[2] = np.array([[205, 120], [391, 202]])
        tables[3] = np.array([[278, 139], [244, 131]])
        tables[4] = np.array([[138, 53], [299, 94]])
        tables[5] = np.array([[351, 22], [317, 24]])

        self.initialize(tables)

        self.oddsratio_pooled = 1.101879
        self.logodds_pooled = np.log(1.101879)

        self.mh_stat = 1.3368
        self.mh_pvalue = 0.2476

        self.or_lcb = 0.9402012
        self.or_ucb = 1.2913602

        self.or_homog = 18.83297
        self.or_homog_p = 0.002064786


class Check2x2Mixin(object):

    def initialize(self):
        self.tbl_obj = ctab.Table2x2(self.table)
        self.tbl_data_obj = ctab.Table2x2.from_data(self.data)

    def test_oddsratio(self):
        assert_allclose(self.tbl_obj.oddsratio, self.oddsratio)


    def test_log_oddsratio(self):
        assert_allclose(self.tbl_obj.log_oddsratio, self.log_oddsratio)


    def test_log_oddsratio_se(self):
        assert_allclose(self.tbl_obj.log_oddsratio_se, self.log_oddsratio_se)


    def test_oddsratio_pvalue(self):
        assert_allclose(self.tbl_obj.oddsratio_pvalue(), self.oddsratio_pvalue)


    def test_oddsratio_confint(self):
        lcb1, ucb1 = self.tbl_obj.oddsratio_confint(0.05)
        lcb2, ucb2 = self.oddsratio_confint
        assert_allclose(lcb1, lcb2)
        assert_allclose(ucb1, ucb2)


    def test_riskratio(self):
        assert_allclose(self.tbl_obj.riskratio, self.riskratio)


    def test_log_riskratio(self):
        assert_allclose(self.tbl_obj.log_riskratio, self.log_riskratio)


    def test_log_riskratio_se(self):
        assert_allclose(self.tbl_obj.log_riskratio_se, self.log_riskratio_se)


    def test_riskratio_pvalue(self):
        assert_allclose(self.tbl_obj.riskratio_pvalue(), self.riskratio_pvalue)


    def test_riskratio_confint(self):
        lcb1, ucb1 = self.tbl_obj.riskratio_confint(0.05)
        lcb2, ucb2 = self.riskratio_confint
        assert_allclose(lcb1, lcb2)
        assert_allclose(ucb1, ucb2)


    def test_log_riskratio_confint(self):
        lcb1, ucb1 = self.tbl_obj.log_riskratio_confint(0.05)
        lcb2, ucb2 = self.log_riskratio_confint
        assert_allclose(lcb1, lcb2)
        assert_allclose(ucb1, ucb2)


    def test_from_data(self):
        assert_equal(self.tbl_obj.summary().as_text(),
                     self.tbl_data_obj.summary().as_text())



class Test2x2_1(Check2x2Mixin):

    def __init__(self):

        data = np.zeros((8, 2))
        data[:, 0] = [0, 0, 1, 1, 0, 0, 1, 1]
        data[:, 1] = [0, 1, 0, 1, 0, 1, 0, 1]
        self.data = np.asarray(data)
        self.table = np.asarray([[2, 2], [2, 2]])

        self.initialize()

        self.oddsratio = 1.
        self.log_oddsratio = 0.
        self.log_oddsratio_se = np.sqrt(2)
        self.oddsratio_confint = [0.062548836166112329, 15.987507702689751]
        self.oddsratio_pvalue = 1.
        self.riskratio = 1.
        self.log_riskratio = 0.
        self.log_riskratio_se = 1 / np.sqrt(2)
        self.riskratio_pvalue = 1.
        self.riskratio_confint = [0.25009765325990629,
                                  3.9984381579173824]
        self.log_riskratio_confint = [-1.3859038243496782,
                                      1.3859038243496782]
