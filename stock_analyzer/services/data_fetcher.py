"""
数据获取服务 - 使用 akshare 获取股票数据
"""
import akshare as ak
import pandas as pd
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataFetcher:
    """股票数据获取器"""

    @staticmethod
    def get_stock_list() -> pd.DataFrame:
        """
        获取所有A股股票列表
        返回: DataFrame包含股票代码、名称等信息
        """
        try:
            # 获取沪深A股实时行情数据
            logger.info("正在获取A股股票列表...")
            df = ak.stock_zh_a_spot_em()

            # 重命名列
            column_mapping = {
                '代码': 'code',
                '名称': 'name',
                '最新价': 'close',
                '涨跌幅': 'pct_change',
                '涨跌额': 'change',
                '成交量': 'volume',
                '成交额': 'amount',
                '换手率': 'turnover_rate',
                '市盈率-动态': 'pe_ratio',
                '市净率': 'pb_ratio',
                '总市值': 'total_market_cap',
                '流通市值': 'circulating_market_cap'
            }

            # 选择需要的列并重命名
            available_columns = [col for col in column_mapping.keys() if col in df.columns]
            df_selected = df[available_columns].copy()
            df_selected.columns = [column_mapping[col] for col in available_columns]

            # 市值单位转换（从元转为亿元）
            for col in ['total_market_cap', 'circulating_market_cap', 'amount']:
                if col in df_selected.columns:
                    df_selected[col] = df_selected[col] / 100000000

            logger.info(f"成功获取 {len(df_selected)} 只股票")
            return df_selected

        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return pd.DataFrame()

    @staticmethod
    def get_stock_info(stock_code: str) -> Optional[Dict]:
        """
        获取单个股票的详细信息
        """
        try:
            # 获取个股信息
            stock_info = ak.stock_individual_info_em(symbol=stock_code)

            info_dict = {}
            if not stock_info.empty:
                for _, row in stock_info.iterrows():
                    key = row['item']
                    value = row['value']
                    info_dict[key] = value

            return info_dict

        except Exception as e:
            logger.error(f"获取股票 {stock_code} 信息失败: {e}")
            return None

    @staticmethod
    def get_stock_history(stock_code: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        获取股票历史行情数据

        Args:
            stock_code: 股票代码
            start_date: 开始日期 YYYYMMDD
            end_date: 结束日期 YYYYMMDD
        """
        try:
            logger.info(f"正在获取股票 {stock_code} 历史数据...")

            # 如果没有指定日期，获取最近一年的数据
            if not end_date:
                end_date = datetime.now().strftime("%Y%m%d")
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")

            # 获取历史行情数据
            df = ak.stock_zh_a_hist(symbol=stock_code, period="daily",
                                     start_date=start_date, end_date=end_date, adjust="qfq")

            if df.empty:
                logger.warning(f"股票 {stock_code} 没有历史数据")
                return pd.DataFrame()

            # 重命名列
            column_mapping = {
                '日期': 'trade_date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount',
                '涨跌幅': 'pct_change',
                '涨跌额': 'change',
                '换手率': 'turnover_rate'
            }

            available_columns = [col for col in column_mapping.keys() if col in df.columns]
            df_selected = df[available_columns].copy()
            df_selected.columns = [column_mapping[col] for col in available_columns]

            # 添加股票代码
            df_selected['code'] = stock_code

            # 转换日期格式
            df_selected['trade_date'] = pd.to_datetime(df_selected['trade_date'])

            logger.info(f"成功获取股票 {stock_code} {len(df_selected)} 天的历史数据")
            return df_selected

        except Exception as e:
            logger.error(f"获取股票 {stock_code} 历史数据失败: {e}")
            return pd.DataFrame()

    @staticmethod
    def get_stock_financial_indicators(stock_code: str) -> Optional[Dict]:
        """
        获取股票财务指标
        """
        try:
            # 获取主要财务指标
            df = ak.stock_financial_analysis_indicator(symbol=stock_code)

            if df.empty:
                return None

            # 获取最新一期的数据
            latest = df.iloc[0].to_dict()
            return latest

        except Exception as e:
            logger.error(f"获取股票 {stock_code} 财务指标失败: {e}")
            return None

    @staticmethod
    def get_latest_trading_date() -> date:
        """
        获取最新的交易日期
        """
        try:
            # 获取最近的交易日历
            today = datetime.now()
            start_date = (today - timedelta(days=7)).strftime("%Y%m%d")
            end_date = today.strftime("%Y%m%d")

            df = ak.tool_trade_date_hist_sina()
            df['trade_date'] = pd.to_datetime(df['trade_date'])

            # 获取小于等于今天的最新交易日
            latest = df[df['trade_date'] <= today]['trade_date'].max()

            return latest.date()

        except Exception as e:
            logger.error(f"获取最新交易日期失败: {e}")
            # 返回今天日期
            return datetime.now().date()
