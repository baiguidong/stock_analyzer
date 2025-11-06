"""
股票数据模型
"""
from datetime import date, datetime
from typing import Optional
from sqlalchemy import Column, String, Float, Integer, Date, DateTime, Index, BigInteger
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Stock(Base):
    """股票基本信息表"""
    __tablename__ = "stocks"

    # 股票代码（主键）
    code = Column(String(10), primary_key=True, comment="股票代码")
    # 股票名称
    name = Column(String(50), nullable=False, comment="股票名称")
    # 市场（SH/SZ）
    market = Column(String(10), comment="市场")
    # 行业
    industry = Column(String(50), comment="行业")
    # 上市日期
    list_date = Column(Date, comment="上市日期")

    # 财务指标
    total_assets = Column(Float, comment="总资产(亿元)")
    net_assets = Column(Float, comment="净资产(亿元)")
    pe_ratio = Column(Float, comment="市盈率(动态)")
    pb_ratio = Column(Float, comment="市净率")
    roe = Column(Float, comment="净资产收益率(%)")

    # 市场指标
    total_market_cap = Column(Float, comment="总市值(亿元)")
    circulating_market_cap = Column(Float, comment="流通市值(亿元)")
    turnover_rate = Column(Float, comment="换手率(%)")

    # 更新时间
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    def __repr__(self):
        return f"<Stock(code={self.code}, name={self.name})>"


class StockDaily(Base):
    """股票每日行情数据表"""
    __tablename__ = "stock_daily"

    # 联合主键
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), nullable=False, index=True, comment="股票代码")
    trade_date = Column(Date, nullable=False, index=True, comment="交易日期")

    # 价格数据
    open = Column(Float, comment="开盘价")
    close = Column(Float, comment="收盘价")
    high = Column(Float, comment="最高价")
    low = Column(Float, comment="最低价")

    # 成交数据
    volume = Column(BigInteger, comment="成交量(股)")
    amount = Column(Float, comment="成交额(元)")

    # 涨跌数据
    change = Column(Float, comment="涨跌额")
    pct_change = Column(Float, comment="涨跌幅(%)")

    # 市值数据
    total_market_cap = Column(Float, comment="总市值(亿元)")
    circulating_market_cap = Column(Float, comment="流通市值(亿元)")

    # 换手率
    turnover_rate = Column(Float, comment="换手率(%)")

    # 创建时间
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")

    # 创建联合索引
    __table_args__ = (
        Index('idx_code_date', 'code', 'trade_date', unique=True),
    )

    def __repr__(self):
        return f"<StockDaily(code={self.code}, date={self.trade_date}, close={self.close})>"
