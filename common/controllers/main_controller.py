#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
控制器层 - 协调UI和业务逻辑
实现MVC模式中的Controller角色
"""
import logging
from typing import Dict, List, Any, Optional
from PySide6 import QtCore
from common.services.data_service import DataService, StockInfo
from common.services.algorithm_service import AlgorithmService
from common.services.chart_service import ChartService
from common.klinechart.chart.object import PlotIndex, PlotItemInfo
from common.model.kline import KLine


class MainController(QtCore.QObject):
    """主控制器 - 协调主窗口的各种操作"""
    
    # 定义信号
    data_loaded = QtCore.Signal(dict)  # 数据加载完成信号
    chart_updated = QtCore.Signal()    # 图表更新信号
    error_occurred = QtCore.Signal(str)  # 错误发生信号
    
    def __init__(self, main_window, config: Dict[str, Any]):
        super().__init__()
        self.main_window = main_window
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 初始化服务
        self.data_service = DataService()
        self.algorithm_service = AlgorithmService()
        self.chart_service = ChartService(self.data_service, self.algorithm_service)
        
        # 缓存数据
        self._stock_list: List[StockInfo] = []
        self._current_chart_data: Optional[Dict[PlotIndex, PlotItemInfo]] = None
        
        # 连接信号
        self._connect_signals()
    
    def _connect_signals(self):
        """连接信号和槽"""
        self.data_loaded.connect(self._on_data_loaded)
        self.error_occurred.connect(self._on_error_occurred)
    
    def initialize(self):
        """初始化控制器"""
        try:
            # 加载股票列表
            self._load_stock_list()
            
            # 加载初始图表数据
            self._load_initial_chart_data()
            
            self.logger.info("控制器初始化完成")
            
        except Exception as e:
            self.logger.error(f"控制器初始化失败: {str(e)}")
            self.error_occurred.emit(f"初始化失败: {str(e)}")
    
    def _load_stock_list(self):
        """加载股票列表"""
        try:
            base_path = self.config.get("conf", {}).get("base_path", "")
            if base_path:
                self._stock_list = self.data_service.load_stock_list(base_path)
                self.logger.info(f"股票列表加载完成，共 {len(self._stock_list)} 只股票")
        except Exception as e:
            self.logger.error(f"股票列表加载失败: {str(e)}")
    
    def _load_initial_chart_data(self):
        """加载初始图表数据"""
        try:
            chart_data = self.chart_service.load_chart_data(self.config)
            self._current_chart_data = chart_data
            self.data_loaded.emit(chart_data)
        except Exception as e:
            self.logger.error(f"初始图表数据加载失败: {str(e)}")
            self.error_occurred.emit(f"数据加载失败: {str(e)}")
    
    def switch_stock(self, stock_code: str):
        """
        切换股票
        
        Args:
            stock_code: 股票代码
        """
        try:
            stock_info = self.data_service.find_stock_by_code(self._stock_list, stock_code)
            if not stock_info:
                self.error_occurred.emit(f"未找到股票: {stock_code}")
                return
            
            # 更新图表数据
            chart_data = self.chart_service.update_chart_file(self.config, stock_info.file_name)
            self._current_chart_data = chart_data
            
            # 发送信号通知UI更新
            self.data_loaded.emit(chart_data)
            
            # 更新窗口标题
            self.main_window.setWindowTitle(f"{stock_code} - {stock_info.name}")
            
            self.logger.info(f"切换到股票: {stock_code} - {stock_info.name}")
            
        except Exception as e:
            self.logger.error(f"切换股票失败: {stock_code}, 错误: {str(e)}")
            self.error_occurred.emit(f"切换股票失败: {str(e)}")
    
    def search_stocks(self, keyword: str) -> List[StockInfo]:
        """
        搜索股票
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            匹配的股票列表
        """
        try:
            return self.data_service.search_stocks(self._stock_list, keyword)
        except Exception as e:
            self.logger.error(f"搜索股票失败: {keyword}, 错误: {str(e)}")
            return []
    
    def get_stock_list(self) -> List[StockInfo]:
        """获取股票列表"""
        return self._stock_list
    
    def refresh_data(self):
        """刷新数据"""
        try:
            if self._current_chart_data:
                # 重新计算算法
                klines = self._extract_klines_from_chart_data(self._current_chart_data)
                self.chart_service.apply_algorithms_to_data(klines, self._current_chart_data)
                
                # 通知UI更新
                self.chart_updated.emit()
                
        except Exception as e:
            self.logger.error(f"刷新数据失败: {str(e)}")
            self.error_occurred.emit(f"刷新数据失败: {str(e)}")
    
    def _extract_klines_from_chart_data(self, chart_data: Dict[PlotIndex, PlotItemInfo]) -> List[KLine]:
        """从图表数据中提取K线数据"""
        # 这里需要根据实际的数据结构来实现
        # 目前返回空列表作为占位符
        return []
    
    def get_current_chart_data(self) -> Optional[Dict[PlotIndex, PlotItemInfo]]:
        """获取当前图表数据"""
        return self._current_chart_data
    
    def _on_data_loaded(self, data: dict):
        """数据加载完成的处理"""
        self.logger.debug("数据加载完成，通知UI更新")
    
    def _on_error_occurred(self, error_message: str):
        """错误发生的处理"""
        self.logger.error(f"控制器错误: {error_message}")


class ChartController(QtCore.QObject):
    """图表控制器 - 专门处理图表相关操作"""
    
    # 定义信号
    chart_data_changed = QtCore.Signal(dict)
    view_updated = QtCore.Signal()
    
    def __init__(self, chart_widget, chart_service: ChartService):
        super().__init__()
        self.chart_widget = chart_widget
        self.chart_service = chart_service
        self.logger = logging.getLogger(__name__)
    
    def update_chart_data(self, chart_data: Dict[PlotIndex, PlotItemInfo]):
        """
        更新图表数据
        
        Args:
            chart_data: 图表数据
        """
        try:
            # 清空现有数据
            self.chart_widget.clear_all()
            
            # 更新数据
            self.chart_widget.update_all_history_data(
                chart_data, 
                self._algorithm_callback
            )
            
            # 更新视图
            self.update_view()
            
            self.chart_data_changed.emit(chart_data)
            
        except Exception as e:
            self.logger.error(f"更新图表数据失败: {str(e)}")
    
    def update_view(self):
        """更新图表视图"""
        try:
            self.chart_widget.update_all_view()
            self.chart_widget._update_y_range()
            self.chart_widget.scene().update()
            self.chart_widget.viewport().update()
            
            self.view_updated.emit()
            
        except Exception as e:
            self.logger.error(f"更新图表视图失败: {str(e)}")
    
    def _algorithm_callback(self, klines: List[KLine], data: Dict[PlotIndex, PlotItemInfo]):
        """算法回调函数"""
        try:
            self.chart_service.apply_algorithms_to_data(klines, data)
        except Exception as e:
            self.logger.error(f"算法回调执行失败: {str(e)}")
    
    def zoom_in(self):
        """放大图表"""
        # 实现放大逻辑
        pass
    
    def zoom_out(self):
        """缩小图表"""
        # 实现缩小逻辑
        pass
    
    def reset_view(self):
        """重置视图"""
        try:
            self.update_view()
        except Exception as e:
            self.logger.error(f"重置视图失败: {str(e)}")


class StockSearchController(QtCore.QObject):
    """股票搜索控制器 - 处理股票搜索相关功能"""
    
    # 定义信号
    search_results_updated = QtCore.Signal(list)  # 搜索结果更新
    stock_selected = QtCore.Signal(str)           # 股票选中
    
    def __init__(self, main_controller: MainController):
        super().__init__()
        self.main_controller = main_controller
        self.logger = logging.getLogger(__name__)
    
    def search(self, keyword: str):
        """
        搜索股票
        
        Args:
            keyword: 搜索关键词
        """
        try:
            results = self.main_controller.search_stocks(keyword)
            self.search_results_updated.emit(results)
        except Exception as e:
            self.logger.error(f"搜索失败: {keyword}, 错误: {str(e)}")
    
    def select_stock(self, stock_code: str):
        """
        选择股票
        
        Args:
            stock_code: 股票代码
        """
        try:
            self.stock_selected.emit(stock_code)
            self.main_controller.switch_stock(stock_code)
        except Exception as e:
            self.logger.error(f"选择股票失败: {stock_code}, 错误: {str(e)}")
    
    def get_all_stocks(self) -> List[StockInfo]:
        """获取所有股票"""
        return self.main_controller.get_stock_list()