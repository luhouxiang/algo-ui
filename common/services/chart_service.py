#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图表服务层 - 负责图表数据处理和管理
将图表逻辑从UI层分离出来
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from common.services.data_service import DataService
from common.services.algorithm_service import AlgorithmService
from common.klinechart.chart.object import ChartItemInfo, PlotIndex, ItemIndex, PlotItemInfo
from common.model.kline import KLine


class ChartDataProcessor:
    """图表数据处理器"""
    
    def __init__(self, data_service: DataService, algorithm_service: AlgorithmService):
        self.data_service = data_service
        self.algorithm_service = algorithm_service
        self.logger = logging.getLogger(__name__)
    
    def process_chart_config(self, config: Dict[str, Any]) -> Dict[PlotIndex, PlotItemInfo]:
        """
        处理图表配置，生成图表数据
        
        Args:
            config: 图表配置
            
        Returns:
            图表数据字典
        """
        local_data: Dict[PlotIndex, PlotItemInfo] = {}
        plots = config.get("plots", [])
        
        for plot_index, plot in enumerate(plots):
            plot_info: PlotItemInfo = {}
            
            for item_index, item in enumerate(plot.get("chart_item", [])):
                item_info = self._process_chart_item(item, config.get("conf", {}))
                plot_info[ItemIndex(item_index)] = item_info
                
                self.logger.info(
                    f"plot_index:{plot_index}, item_index:{item_index}, "
                    f"数据量={len(item_info.bars) if item_info.bars else 0}"
                )
            
            local_data[PlotIndex(plot_index)] = plot_info
        
        return local_data
    
    def _process_chart_item(self, item: Dict[str, Any], conf: Dict[str, Any]) -> ChartItemInfo:
        """
        处理单个图表项
        
        Args:
            item: 图表项配置
            conf: 全局配置
            
        Returns:
            图表项信息
        """
        item_info = ChartItemInfo()
        item_info.type = item.get("type", "")
        item_info.params = item.get("params", [])
        item_info.func_name = item.get("func_name", "")
        item_info.data_type = item.get("data_type", [])
        
        file_name = item.get("file_name")
        if file_name:
            # 加载文件数据
            base_path = conf.get("base_path", "")
            kline_count = conf.get("kline_count", 1000)
            start_dt = conf.get("start_dt", "")
            end_dt = conf.get("end_dt", "")
            
            # 使用数据服务加载数据
            file_path = f'{base_path}/{file_name}'
            data_list = self.data_service.load_kline_data(file_path, kline_count, start_dt, end_dt)
            
            # 转换为Bar字典
            item_info.bars = self.data_service.convert_to_bars(data_list, item_info.data_type)
        else:
            item_info.bars = {}
        
        return item_info
    
    def apply_algorithms(self, klines: List[KLine], data: Dict[PlotIndex, PlotItemInfo]):
        """
        应用算法到图表数据
        
        Args:
            klines: K线数据
            data: 图表数据
        """
        # 首先计算基础算法（如zigzag）
        self._calculate_base_algorithms(klines)
        
        # 然后处理各个图表项的算法
        for plot_index in data.keys():
            plot_item_info: PlotItemInfo = data[plot_index]
            for item_index in plot_item_info:
                info: ChartItemInfo = plot_item_info[item_index]
                if not info.bars and info.func_name:
                    self._apply_item_algorithm(info, klines)
    
    def _calculate_base_algorithms(self, klines: List[KLine]):
        """计算基础算法"""
        try:
            # 计算zigzag算法
            self.algorithm_service.calculate("zigzag", klines)
        except Exception as e:
            self.logger.warning(f"基础算法计算失败: {str(e)}")
    
    def _apply_item_algorithm(self, info: ChartItemInfo, klines: List[KLine]):
        """
        为单个图表项应用算法
        
        Args:
            info: 图表项信息
            klines: K线数据
        """
        try:
            if info.type == "Straight":
                # 直线类型使用discrete_list
                result = self.algorithm_service.calculate_by_function_name(info.func_name, klines)
                info.discrete_list = result
            else:
                # 其他类型使用bars
                result = self.algorithm_service.calculate_by_function_name(info.func_name, klines)
                info.bars = result
                
        except Exception as e:
            self.logger.error(f"图表项算法应用失败: {info.func_name}, 错误: {str(e)}")


class ChartService:
    """图表服务 - 图表功能的统一入口"""
    
    def __init__(self, data_service: DataService, algorithm_service: AlgorithmService):
        self.data_service = data_service
        self.algorithm_service = algorithm_service
        self.processor = ChartDataProcessor(data_service, algorithm_service)
        self.logger = logging.getLogger(__name__)
    
    def load_chart_data(self, config: Dict[str, Any]) -> Dict[PlotIndex, PlotItemInfo]:
        """
        加载图表数据
        
        Args:
            config: 图表配置
            
        Returns:
            图表数据
        """
        try:
            return self.processor.process_chart_config(config)
        except Exception as e:
            self.logger.error(f"加载图表数据失败: {str(e)}")
            return {}
    
    def apply_algorithms_to_data(self, klines: List[KLine], 
                                data: Dict[PlotIndex, PlotItemInfo]):
        """
        对图表数据应用算法
        
        Args:
            klines: K线数据
            data: 图表数据
        """
        try:
            self.processor.apply_algorithms(klines, data)
        except Exception as e:
            self.logger.error(f"应用算法失败: {str(e)}")
    
    def update_chart_file(self, config: Dict[str, Any], file_name: str) -> Dict[PlotIndex, PlotItemInfo]:
        """
        更新图表文件数据
        
        Args:
            config: 图表配置
            file_name: 新的文件名
            
        Returns:
            更新后的图表数据
        """
        try:
            # 更新配置中的文件名
            if "plots" in config and len(config["plots"]) > 0:
                if "chart_item" in config["plots"][0] and len(config["plots"][0]["chart_item"]) > 0:
                    config["plots"][0]["chart_item"][0]["file_name"] = file_name
            
            # 重新加载数据
            return self.load_chart_data(config)
            
        except Exception as e:
            self.logger.error(f"更新图表文件失败: {file_name}, 错误: {str(e)}")
            return {}
    
    def get_chart_types(self) -> List[str]:
        """获取支持的图表类型"""
        return [
            "Candle",   # K线图
            "Volume",   # 成交量
            "Line",     # 曲线
            "Macd",     # MACD
            "Arrow",    # 箭头
            "Straight", # 直线
            "Signal",   # 信号
            "Shadow",   # 阴影
        ]
    
    def validate_chart_config(self, config: Dict[str, Any]) -> bool:
        """
        验证图表配置
        
        Args:
            config: 图表配置
            
        Returns:
            是否有效
        """
        try:
            if "plots" not in config:
                return False
            
            for plot in config["plots"]:
                if "chart_item" not in plot:
                    return False
                
                for item in plot["chart_item"]:
                    if "type" not in item:
                        return False
                    
                    if item["type"] not in self.get_chart_types():
                        return False
            
            return True
            
        except Exception:
            return False