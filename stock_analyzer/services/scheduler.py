"""
定时任务调度服务
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging

from .data_fetcher import DataFetcher
from .database import DatabaseService
from ..config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SchedulerService:
    """定时任务调度器"""

    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        # 从配置中获取tushare token
        self.data_fetcher = DataFetcher(token=config.tushare.token)
        self.scheduler = BackgroundScheduler()

    def update_all_stocks(self):
        """更新所有股票的基本信息"""
        try:
            logger.info("开始更新所有股票基本信息...")
            start_time = datetime.now()

            # 获取股票列表
            stocks_df = self.data_fetcher.get_stock_list()

            if not stocks_df.empty:
                # 添加市场信息
                stocks_df['market'] = stocks_df['code'].apply(
                    lambda x: 'SH' if x.startswith('6') else 'SZ'
                )

                # 更新到数据库
                count = self.db_service.upsert_stocks(stocks_df)

                elapsed = (datetime.now() - start_time).total_seconds()
                logger.info(f"股票基本信息更新完成，共 {count} 只股票，耗时 {elapsed:.2f} 秒")
            else:
                logger.warning("未获取到股票数据")

        except Exception as e:
            logger.error(f"更新股票基本信息失败: {e}")

    def update_daily_data(self, stock_codes: list = None):
        """
        更新每日行情数据

        Args:
            stock_codes: 要更新的股票代码列表，如果为None则更新所有股票
        """
        try:
            logger.info("开始更新每日行情数据...")
            start_time = datetime.now()

            # 如果没有指定股票代码，从数据库获取所有股票
            if stock_codes is None:
                session = self.db_service.get_session()
                stocks = session.query(self.db_service.SessionLocal().query(
                    self.db_service.engine.table_names()
                ))
                from ..models import Stock
                stocks = session.query(Stock.code).all()
                stock_codes = [s.code for s in stocks]
                session.close()

            if not stock_codes:
                logger.warning("没有需要更新的股票")
                return

            logger.info(f"准备更新 {len(stock_codes)} 只股票的每日数据")

            # 获取最新交易日
            latest_date = self.data_fetcher.get_latest_trading_date()
            date_str = latest_date.strftime("%Y%m%d")

            success_count = 0
            failed_count = 0

            # 逐个获取股票数据（可以优化为批量）
            for i, code in enumerate(stock_codes):
                try:
                    # 获取最近30天的数据（确保包含最新数据）
                    daily_df = self.data_fetcher.get_stock_history(
                        code, start_date=None, end_date=date_str
                    )

                    if not daily_df.empty:
                        self.db_service.upsert_stock_daily(daily_df)
                        success_count += 1
                    else:
                        failed_count += 1

                    # 每更新10只股票输出一次进度
                    if (i + 1) % 10 == 0:
                        logger.info(f"进度: {i + 1}/{len(stock_codes)}")

                except Exception as e:
                    logger.error(f"更新股票 {code} 每日数据失败: {e}")
                    failed_count += 1

            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(f"每日数据更新完成，成功 {success_count} 只，失败 {failed_count} 只，耗时 {elapsed:.2f} 秒")

        except Exception as e:
            logger.error(f"更新每日数据失败: {e}")

    def daily_update_job(self):
        """每日更新任务 - 更新所有用户的自选股票历史数据"""
        logger.info("执行每日定时更新任务（更新自选股票历史数据）...")

        try:
            from ..models import Favorite
            from sqlalchemy import distinct

            session = self.db_service.get_session()

            try:
                # 获取所有用户的自选股票代码（去重）
                favorites = session.query(distinct(Favorite.stock_code)).all()
                stock_codes = [f[0] for f in favorites]

                if not stock_codes:
                    logger.info("没有自选股票需要更新")
                    return

                logger.info(f"准备更新 {len(stock_codes)} 只自选股票的历史数据")

                # 更新自选股票的历史数据
                self.update_daily_data(stock_codes)

            finally:
                session.close()

        except Exception as e:
            logger.error(f"每日更新任务失败: {e}")

        logger.info("每日更新任务完成")

    def start(self, run_immediately: bool = False):
        """
        启动调度器

        Args:
            run_immediately: 是否立即执行一次更新
        """
        if config.update_schedule.auto_update:
            # 解析更新时间
            update_time = config.update_schedule.daily_update_time
            hour, minute = map(int, update_time.split(':'))

            # 添加每日定时任务
            self.scheduler.add_job(
                self.daily_update_job,
                CronTrigger(hour=hour, minute=minute),
                id='daily_update',
                name='每日股票数据更新',
                replace_existing=True
            )

            logger.info(f"已添加每日更新任务，执行时间: {update_time}")

        # 启动调度器
        self.scheduler.start()
        logger.info("调度器已启动")

        # 如果配置了启动时更新或者指定立即运行
        if run_immediately or config.update_schedule.update_on_start:
            logger.info("执行首次数据更新...")
            self.daily_update_job()

    def stop(self):
        """停止调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("调度器已停止")

    def get_jobs(self):
        """获取所有任务"""
        return self.scheduler.get_jobs()
