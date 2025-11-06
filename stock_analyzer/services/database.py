"""
数据库服务
"""
from sqlalchemy import create_engine, and_, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict
import pandas as pd
import logging

from ..models import Base, Stock, StockDaily
from ..config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseService:
    """数据库服务"""

    def __init__(self, database_url: str = None):
        """初始化数据库服务"""
        self.database_url = database_url or config.database.url
        self.engine = create_engine(self.database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)

        # 创建所有表
        self.init_db()

    def init_db(self):
        """初始化数据库，创建所有表"""
        logger.info("正在创建数据库表...")
        Base.metadata.create_all(bind=self.engine)
        logger.info("数据库表创建完成")

    def get_session(self) -> Session:
        """获取数据库会话"""
        return self.SessionLocal()

    def upsert_stocks(self, stocks_data: pd.DataFrame) -> int:
        """
        批量插入或更新股票基本信息

        Args:
            stocks_data: 包含股票信息的DataFrame

        Returns:
            更新的股票数量
        """
        session = self.get_session()
        count = 0

        try:
            for _, row in stocks_data.iterrows():
                stock = session.query(Stock).filter_by(code=row['code']).first()

                if stock:
                    # 更新现有记录
                    for key, value in row.items():
                        if hasattr(stock, key) and pd.notna(value):
                            setattr(stock, key, value)
                else:
                    # 创建新记录
                    stock_data = {k: v for k, v in row.items() if pd.notna(v)}
                    stock = Stock(**stock_data)
                    session.add(stock)

                count += 1

                # 每100条提交一次
                if count % 100 == 0:
                    session.commit()
                    logger.info(f"已处理 {count} 只股票")

            session.commit()
            logger.info(f"成功更新 {count} 只股票信息")
            return count

        except Exception as e:
            session.rollback()
            logger.error(f"批量更新股票信息失败: {e}")
            return 0
        finally:
            session.close()

    def upsert_stock_daily(self, daily_data: pd.DataFrame) -> int:
        """
        批量插入或更新股票每日数据

        Args:
            daily_data: 包含每日行情的DataFrame

        Returns:
            更新的记录数
        """
        session = self.get_session()
        count = 0

        try:
            for _, row in daily_data.iterrows():
                # 检查是否存在
                existing = session.query(StockDaily).filter(
                    and_(
                        StockDaily.code == row['code'],
                        StockDaily.trade_date == row['trade_date']
                    )
                ).first()

                if existing:
                    # 更新现有记录
                    for key, value in row.items():
                        if hasattr(existing, key) and key not in ['id', 'created_at'] and pd.notna(value):
                            setattr(existing, key, value)
                else:
                    # 创建新记录
                    daily_dict = {k: v for k, v in row.items() if pd.notna(v) and k != 'id'}
                    daily = StockDaily(**daily_dict)
                    session.add(daily)

                count += 1

                # 每500条提交一次
                if count % 500 == 0:
                    session.commit()
                    logger.debug(f"已处理 {count} 条每日数据")

            session.commit()
            return count

        except Exception as e:
            session.rollback()
            logger.error(f"批量更新每日数据失败: {e}")
            return 0
        finally:
            session.close()

    def get_stock_by_code(self, code: str) -> Optional[Stock]:
        """根据代码获取股票信息"""
        session = self.get_session()
        try:
            return session.query(Stock).filter_by(code=code).first()
        finally:
            session.close()

    def search_stocks(self, keyword: str, limit: int = 20) -> List[Stock]:
        """搜索股票（按代码或名称）"""
        session = self.get_session()
        try:
            return session.query(Stock).filter(
                (Stock.code.like(f"%{keyword}%")) | (Stock.name.like(f"%{keyword}%"))
            ).limit(limit).all()
        finally:
            session.close()

    def get_stock_daily_history(self, code: str, start_date: date = None,
                                 end_date: date = None, limit: int = 100) -> List[StockDaily]:
        """获取股票历史行情"""
        session = self.get_session()
        try:
            query = session.query(StockDaily).filter_by(code=code)

            if start_date:
                query = query.filter(StockDaily.trade_date >= start_date)
            if end_date:
                query = query.filter(StockDaily.trade_date <= end_date)

            return query.order_by(StockDaily.trade_date.desc()).limit(limit).all()
        finally:
            session.close()

    def get_stocks_by_criteria(self,
                                min_pe: float = None, max_pe: float = None,
                                min_pb: float = None, max_pb: float = None,
                                min_market_cap: float = None, max_market_cap: float = None,
                                min_turnover: float = None, max_turnover: float = None,
                                industry: str = None,
                                limit: int = 100) -> List[Stock]:
        """根据条件筛选股票"""
        session = self.get_session()
        try:
            query = session.query(Stock)

            if min_pe is not None:
                query = query.filter(Stock.pe_ratio >= min_pe)
            if max_pe is not None:
                query = query.filter(Stock.pe_ratio <= max_pe)
            if min_pb is not None:
                query = query.filter(Stock.pb_ratio >= min_pb)
            if max_pb is not None:
                query = query.filter(Stock.pb_ratio <= max_pb)
            if min_market_cap is not None:
                query = query.filter(Stock.total_market_cap >= min_market_cap)
            if max_market_cap is not None:
                query = query.filter(Stock.total_market_cap <= max_market_cap)
            if min_turnover is not None:
                query = query.filter(Stock.turnover_rate >= min_turnover)
            if max_turnover is not None:
                query = query.filter(Stock.turnover_rate <= max_turnover)
            if industry:
                query = query.filter(Stock.industry.like(f"%{industry}%"))

            return query.limit(limit).all()
        finally:
            session.close()

    def get_latest_trade_date(self) -> Optional[date]:
        """获取数据库中最新的交易日期"""
        session = self.get_session()
        try:
            result = session.query(func.max(StockDaily.trade_date)).scalar()
            return result
        finally:
            session.close()

    def get_stock_count(self) -> int:
        """获取股票总数"""
        session = self.get_session()
        try:
            return session.query(Stock).count()
        finally:
            session.close()

    def get_daily_data_count(self) -> int:
        """获取每日数据总数"""
        session = self.get_session()
        try:
            return session.query(StockDaily).count()
        finally:
            session.close()
