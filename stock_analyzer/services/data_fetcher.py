"""
数据获取服务 - 使用 tushare 获取股票数据
"""
import tushare as ts
import pandas as pd
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataFetcher:
    """股票数据获取器"""

    def __init__(self, token: str = None):
        """
        初始化数据获取器
        Args:
            token: tushare API token (如果为空，从环境变量TUSHARE_TOKEN读取)
        """
        if token:
            ts.set_token(token)
        self.pro = ts.pro_api()

    @staticmethod
    def get_stock_list() -> pd.DataFrame:
        """
        获取所有A股股票列表及基础指标
        返回: DataFrame包含股票代码、名称、市盈率、市净率、换手率等信息
        """
        try:
            logger.info("正在获取A股股票列表...")
            pro = ts.pro_api()

            # 获取股票基础信息
            stock_basic = pro.stock_basic(
                exchange='',
                list_status='L',
                fields='ts_code,symbol,name,area,industry,market,list_date'
            )

            if stock_basic.empty:
                logger.warning("未获取到股票基础信息")
                return pd.DataFrame()

            # 获取最新交易日
            trade_cal = pro.trade_cal(exchange='SSE', is_open='1')
            if not trade_cal.empty:
                latest_date = trade_cal[trade_cal['cal_date'] <= datetime.now().strftime('%Y%m%d')]['cal_date'].max()
            else:
                latest_date = datetime.now().strftime('%Y%m%d')

            # 获取每日指标（包含PE、PB、换手率等）
            logger.info(f"正在获取 {latest_date} 的市场指标...")
            daily_basic = pro.daily_basic(
                trade_date=latest_date,
                fields='ts_code,close,turnover_rate,pe,pb,total_mv,circ_mv'
            )

            # 合并数据
            if not daily_basic.empty:
                df = pd.merge(stock_basic, daily_basic, on='ts_code', how='left')
            else:
                df = stock_basic
                df['close'] = None
                df['turnover_rate'] = None
                df['pe'] = None
                df['pb'] = None
                df['total_mv'] = None
                df['circ_mv'] = None

            # 重命名列
            column_mapping = {
                'ts_code': 'ts_code',
                'symbol': 'code',
                'name': 'name',
                'market': 'market',
                'industry': 'industry',
                'list_date': 'list_date',
                'close': 'close',
                'turnover_rate': 'turnover_rate',
                'pe': 'pe_ratio',
                'pb': 'pb_ratio',
                'total_mv': 'total_market_cap',
                'circ_mv': 'circulating_market_cap'
            }

            df = df.rename(columns=column_mapping)

            # 市值单位已经是万元，转换为亿元
            for col in ['total_market_cap', 'circulating_market_cap']:
                if col in df.columns:
                    df[col] = df[col] / 10000

            logger.info(f"成功获取 {len(df)} 只股票")
            return df

        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return pd.DataFrame()

    @staticmethod
    def get_stock_info(stock_code: str) -> Optional[Dict]:
        """
        获取单个股票的详细信息
        Args:
            stock_code: 股票代码（不带后缀，如 '000001'）
        """
        try:
            pro = ts.pro_api()

            # 转换代码格式（添加交易所后缀）
            ts_code = DataFetcher._convert_to_ts_code(stock_code)

            # 获取基础信息
            stock_basic = pro.stock_basic(ts_code=ts_code, fields='ts_code,name,area,industry,market,list_date')

            if stock_basic.empty:
                return None

            info_dict = stock_basic.iloc[0].to_dict()
            return info_dict

        except Exception as e:
            logger.error(f"获取股票 {stock_code} 信息失败: {e}")
            return None

    @staticmethod
    def get_stock_history(stock_code: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        获取股票历史行情数据（包含日线和每日指标）

        Args:
            stock_code: 股票代码（不带后缀，如 '000001'）
            start_date: 开始日期 YYYYMMDD
            end_date: 结束日期 YYYYMMDD
        """
        try:
            logger.info(f"正在获取股票 {stock_code} 历史数据...")
            pro = ts.pro_api()

            # 转换代码格式
            ts_code = DataFetcher._convert_to_ts_code(stock_code)

            # 如果没有指定日期，获取最近一年的数据
            if not end_date:
                end_date = datetime.now().strftime("%Y%m%d")
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")

            # 获取日线行情数据（前复权）
            daily = pro.daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )

            if daily.empty:
                logger.warning(f"股票 {stock_code} 没有历史数据")
                return pd.DataFrame()

            # 获取每日指标（PE、PB、换手率等）
            daily_basic = pro.daily_basic(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
                fields='ts_code,trade_date,turnover_rate,pe,pb,total_mv,circ_mv'
            )

            # 合并数据
            if not daily_basic.empty:
                df = pd.merge(daily, daily_basic, on=['ts_code', 'trade_date'], how='left')
            else:
                df = daily
                df['turnover_rate'] = None
                df['pe'] = None
                df['pb'] = None
                df['total_mv'] = None
                df['circ_mv'] = None

            # 重命名列
            column_mapping = {
                'ts_code': 'ts_code',
                'trade_date': 'trade_date',
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'vol': 'volume',
                'amount': 'amount',
                'pct_chg': 'pct_change',
                'change': 'change',
                'turnover_rate': 'turnover_rate',
                'total_mv': 'total_market_cap',
                'circ_mv': 'circulating_market_cap'
            }

            df = df.rename(columns=column_mapping)

            # 添加股票代码（不带后缀）
            df['code'] = stock_code

            # 转换日期格式
            df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')

            # 成交量单位转换（手转为股）
            if 'volume' in df.columns:
                df['volume'] = df['volume'] * 100

            # 成交额单位已经是千元，转换为元
            if 'amount' in df.columns:
                df['amount'] = df['amount'] * 1000

            # 市值单位转换（万元转为亿元）
            for col in ['total_market_cap', 'circulating_market_cap']:
                if col in df.columns:
                    df[col] = df[col] / 10000

            logger.info(f"成功获取股票 {stock_code} {len(df)} 天的历史数据")
            return df

        except Exception as e:
            logger.error(f"获取股票 {stock_code} 历史数据失败: {e}")
            return pd.DataFrame()

    @staticmethod
    def get_stock_financial_indicators(stock_code: str) -> Optional[Dict]:
        """
        获取股票财务指标
        Args:
            stock_code: 股票代码（不带后缀）
        """
        try:
            pro = ts.pro_api()
            ts_code = DataFetcher._convert_to_ts_code(stock_code)

            # 获取最新财务指标
            df = pro.fina_indicator(
                ts_code=ts_code,
                fields='ts_code,end_date,roe,roa,debt_to_assets,current_ratio'
            )

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
            pro = ts.pro_api()

            # 获取最近的交易日历
            today = datetime.now()
            start_date = (today - timedelta(days=7)).strftime("%Y%m%d")
            end_date = today.strftime("%Y%m%d")

            df = pro.trade_cal(exchange='SSE', start_date=start_date, end_date=end_date, is_open='1')

            if df.empty:
                return today.date()

            # 获取小于等于今天的最新交易日
            df['cal_date'] = pd.to_datetime(df['cal_date'], format='%Y%m%d')
            latest = df[df['cal_date'] <= today]['cal_date'].max()

            return latest.date()

        except Exception as e:
            logger.error(f"获取最新交易日期失败: {e}")
            # 返回今天日期
            return datetime.now().date()

    @staticmethod
    def _convert_to_ts_code(stock_code: str) -> str:
        """
        将股票代码转换为tushare格式（添加交易所后缀）
        Args:
            stock_code: 股票代码，如 '000001' 或 '000001.SZ'
        Returns:
            tushare格式的代码，如 '000001.SZ'
        """
        if '.' in stock_code:
            return stock_code

        # 根据代码判断交易所
        if stock_code.startswith('6'):
            return f"{stock_code}.SH"
        elif stock_code.startswith(('0', '3')):
            return f"{stock_code}.SZ"
        elif stock_code.startswith('4') or stock_code.startswith('8'):
            return f"{stock_code}.BJ"  # 北交所
        else:
            return f"{stock_code}.SH"  # 默认上交所
