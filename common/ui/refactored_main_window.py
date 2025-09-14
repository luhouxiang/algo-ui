#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重构后的主窗口 - 职责分离的UI层
只负责UI展示和用户交互，业务逻辑委托给控制器
"""
import sys
from typing import Dict, List, Any
from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Qt
from common.klinechart.chart import ChartWidget, ChartVolume, ChartCandle, ChartMacd,\
    ChartArrow, ChartLine, ChartStraight, ChartSignal, ChartShadow
from common.klinechart.chart.keyboard_genie_window import KeyboardGenieWindow
from common.controllers.main_controller import MainController, ChartController, StockSearchController
from common.services.data_service import StockInfo
from common.klinechart.chart.object import PlotIndex, PlotItemInfo


class RefactoredMainWindow(QtWidgets.QMainWindow):
    """重构后的主窗口 - 纯UI层"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.config = config
        
        # 初始化UI组件
        self._init_ui()
        
        # 初始化控制器
        self._init_controllers()
        
        # 连接信号和槽
        self._connect_signals()
        
        # 初始化数据
        self._initialize_data()
    
    def _init_ui(self):
        """初始化UI组件"""
        # 创建图表组件
        self.chart_widget = ChartWidget(self)
        self.setCentralWidget(self.chart_widget)
        
        # 添加图表项
        self._add_chart_items()
        
        # 添加光标
        self.chart_widget.add_cursor()
        
        # 创建键盘精灵窗口
        self.keyboard_genie = KeyboardGenieWindow(self)
        
        # 设置窗口属性
        self.resize(1024, 768)
    
    def _init_controllers(self):
        """初始化控制器"""
        # 主控制器
        self.main_controller = MainController(self, self.config)
        
        # 图表控制器
        self.chart_controller = ChartController(self.chart_widget, self.main_controller.chart_service)
        
        # 搜索控制器
        self.search_controller = StockSearchController(self.main_controller)
    
    def _connect_signals(self):
        """连接信号和槽"""
        # 主控制器信号
        self.main_controller.data_loaded.connect(self._on_data_loaded)
        self.main_controller.error_occurred.connect(self._on_error_occurred)
        
        # 图表控制器信号
        self.chart_controller.chart_data_changed.connect(self._on_chart_data_changed)
        self.chart_controller.view_updated.connect(self._on_view_updated)
        
        # 搜索控制器信号
        self.search_controller.search_results_updated.connect(self._on_search_results_updated)
        self.search_controller.stock_selected.connect(self._on_stock_selected)
        
        # 键盘精灵信号
        self.keyboard_genie.input_line_edit.textChanged.connect(self._on_search_text_changed)
        self.keyboard_genie.matching_list_widget.itemDoubleClicked.connect(self._on_stock_item_double_clicked)
    
    def _initialize_data(self):
        """初始化数据"""
        self.main_controller.initialize()
    
    def _add_chart_items(self):
        """添加图表项"""
        plots = self.config.get("plots", [])
        for plot_index, plot in enumerate(plots):
            # 添加绘图区域
            hide_x_axis = plot_index != len(plots) - 1
            max_height = plot.get("max_height", 200)
            self.chart_widget.add_plot(hide_x_axis=hide_x_axis, maximum_height=max_height)
            
            # 添加图表项
            for index, chart_item in enumerate(plot.get("chart_item", [])):
                chart_type = chart_item.get("type", "")
                self._add_chart_item_by_type(plot_index, chart_type)
    
    def _add_chart_item_by_type(self, plot_index: int, chart_type: str):
        """根据类型添加图表项"""
        type_mapping = {
            "Candle": ChartCandle,
            "Volume": ChartVolume,
            "Line": ChartLine,
            "Macd": ChartMacd,
            "Arrow": ChartArrow,
            "Straight": ChartStraight,
            "Signal": ChartSignal,
            "Shadow": ChartShadow,
        }
        
        chart_class = type_mapping.get(chart_type)
        if chart_class:
            self.chart_widget.add_item(plot_index, chart_class)
        else:
            raise ValueError(f"未支持的图表类型: {chart_type}")
    
    # 事件处理方法
    def keyPressEvent(self, event):
        """键盘事件处理"""
        key = event.key()
        if key == QtCore.Qt.Key.Key_Escape:
            self._hide_keyboard_genie()
        else:
            text = event.text()
            if text.isalnum() or text.isalpha() or text.isdigit():
                self._show_keyboard_genie(text)
            else:
                super().keyPressEvent(event)
    
    def moveEvent(self, event):
        """窗口移动事件"""
        super().moveEvent(event)
        self._update_keyboard_genie_position()
    
    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        self._update_keyboard_genie_position()
    
    # 键盘精灵相关方法
    def _show_keyboard_genie(self, initial_text: str = ""):
        """显示键盘精灵"""
        if not self.keyboard_genie.isVisible():
            self.keyboard_genie.show()
            self._update_keyboard_genie_position()
            self.keyboard_genie.activateWindow()
            self.keyboard_genie.raise_()
        
        self.keyboard_genie.input_line_edit.setFocus()
        self.keyboard_genie.input_line_edit.clear()
        if initial_text:
            self.keyboard_genie.input_line_edit.setText(initial_text)
    
    def _hide_keyboard_genie(self):
        """隐藏键盘精灵"""
        self.keyboard_genie.hide()
    
    def _update_keyboard_genie_position(self):
        """更新键盘精灵位置"""
        if self.keyboard_genie.isVisible():
            main_window_pos = self.mapToGlobal(QtCore.QPoint(0, 0))
            main_window_size = self.size()
            genie_size = self.keyboard_genie.sizeHint()
            
            x = main_window_pos.x() + main_window_size.width() - genie_size.width()
            y = main_window_pos.y() + main_window_size.height() - genie_size.height()
            
            self.keyboard_genie.move(x, y)
    
    # 信号处理方法
    def _on_data_loaded(self, chart_data: Dict[PlotIndex, PlotItemInfo]):
        """数据加载完成处理"""
        self.chart_controller.update_chart_data(chart_data)
    
    def _on_error_occurred(self, error_message: str):
        """错误处理"""
        QtWidgets.QMessageBox.critical(self, "错误", error_message)
    
    def _on_chart_data_changed(self, chart_data: dict):
        """图表数据变化处理"""
        # 可以在这里添加额外的UI更新逻辑
        pass
    
    def _on_view_updated(self):
        """视图更新处理"""
        # 可以在这里添加视图更新后的UI逻辑
        pass
    
    def _on_search_results_updated(self, results: List[StockInfo]):
        """搜索结果更新处理"""
        self.keyboard_genie.matching_list_widget.clear()
        
        for stock in results:
            item_text = f"{stock.code} - {stock.name}"
            item = QtWidgets.QListWidgetItem(item_text)
            item.setData(QtCore.Qt.ItemDataRole.UserRole, stock.code)
            self.keyboard_genie.matching_list_widget.addItem(item)
        
        if results:
            self.keyboard_genie.matching_list_widget.setCurrentRow(0)
    
    def _on_stock_selected(self, stock_code: str):
        """股票选中处理"""
        self._hide_keyboard_genie()
    
    def _on_search_text_changed(self, text: str):
        """搜索文本变化处理"""
        self.search_controller.search(text)
    
    def _on_stock_item_double_clicked(self, item: QtWidgets.QListWidgetItem):
        """股票项双击处理"""
        stock_code = item.data(QtCore.Qt.ItemDataRole.UserRole)
        if stock_code:
            self.search_controller.select_stock(stock_code)
    
    # 公共方法
    def refresh_data(self):
        """刷新数据"""
        self.main_controller.refresh_data()
    
    def get_current_stock_code(self) -> str:
        """获取当前股票代码"""
        title = self.windowTitle()
        if " - " in title:
            return title.split(" - ")[0]
        return ""


# 创建应用程序实例
def create_app():
    """创建应用程序实例"""
    return QtWidgets.QApplication(sys.argv)


# 使用示例
if __name__ == '__main__':
    # 这个文件主要是示例，实际使用时需要从main.py调用
    app = create_app()
    
    # 示例配置
    config = {
        "conf": {
            "base_path": "data",
            "kline_count": 1000,
        },
        "plots": [
            {
                "max_height": 400,
                "chart_item": [
                    {
                        "type": "Candle",
                        "file_name": "candle.txt",
                        "data_type": ["datetime", "float", "float", "float", "float"]
                    }
                ]
            }
        ]
    }
    
    window = RefactoredMainWindow(config)
    window.show()
    
    app.exec()