#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据服务层 - 负责所有数据相关操作
将数据加载逻辑从UI层分离出来
"""
import os
import re
import logging
from typing import List, Dict, Optional
from datetime import datetime
from common.utils import file_txt
from common.utils.pinyin_util import get_pinyin_first_letters
from common.model.kline import KLine
from common.klinechart.chart.object import DataItem


class StockInfo:
    """股票信息模型"""
    def __init__(self, code: str, name: str, pinyin: str, file_name: str):
        self.code = code
        self.name = name
        self.pinyin = pinyin
        self.file_name = file_name


class DataService:
    """数据服务 - 负责数据加载和管理"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def load_kline_data(self, file_path: str, count: int = 1000, 
                       start_dt: str = "", end_dt: str = "") -> List[str]:
        """
        加载K线数据
        
        Args:
            file_path: 文件路径
            count: 加载数量
            start_dt: 开始时间
            end_dt: 结束时间
            
        Returns:
            K线数据列表
        """
        try:
            data_list = file_txt.tail_kline(file_path, count, start_dt, end_dt)
            self.logger.info(f"成功加载K线数据: {file_path}, 数量: {len(data_list)}")
            return data_list
        except Exception as e:
            self.logger.error(f"加载K线数据失败: {file_path}, 错误: {str(e)}")
            return []
    
    def convert_to_bars(self, data_list: List[str], data_type: List[str]) -> Dict[datetime, DataItem]:
        """
        将原始数据转换为Bar字典
        
        Args:
            data_list: 原始数据列表
            data_type: 数据类型定义
            
        Returns:
            Bar字典
        """
        bar_dict: Dict[datetime, DataItem] = {}
        for data_index, txt in enumerate(data_list):
            bar = DataItem(txt, data_type)
            if bar:
                bar_dict[bar[0]] = bar
        return bar_dict
    
    def load_stock_list(self, base_path: str) -> List[StockInfo]:
        """
        加载股票列表
        
        Args:
            base_path: 数据目录路径
            
        Returns:
            股票信息列表
        """
        stock_list = []
        pattern = re.compile(r'^\d+#[^#]*L9\.txt$')
        
        try:
            for file_name in os.listdir(base_path):
                if pattern.match(file_name):
                    file_path = os.path.join(base_path, file_name)
                    stock_info = self._parse_stock_file(file_path, file_name)
                    if stock_info:
                        stock_list.append(stock_info)
            
            self.logger.info(f"加载股票列表完成，共 {len(stock_list)} 只股票")
            return stock_list
            
        except Exception as e:
            self.logger.error(f"加载股票列表失败: {str(e)}")
            return []
    
    def _parse_stock_file(self, file_path: str, file_name: str) -> Optional[StockInfo]:
        """
        解析股票文件获取股票信息
        
        Args:
            file_path: 文件完整路径
            file_name: 文件名
            
        Returns:
            股票信息对象
        """
        try:
            with open(file_path, 'r', encoding='gb2312') as f:
                first_line = f.readline().strip()
                fields = first_line.split()
                if len(fields) >= 2:
                    code = fields[0].strip()
                    name = fields[1].strip()
                    pinyin = get_pinyin_first_letters(name)
                    return StockInfo(code, name, pinyin, file_name)
        except Exception as e:
            self.logger.warning(f"解析股票文件失败: {file_path}, 错误: {str(e)}")
        return None
    
    def find_stock_by_code(self, stock_list: List[StockInfo], code: str) -> Optional[StockInfo]:
        """
        根据代码查找股票
        
        Args:
            stock_list: 股票列表
            code: 股票代码
            
        Returns:
            股票信息对象
        """
        for stock in stock_list:
            if stock.code == code:
                return stock
        return None
    
    def search_stocks(self, stock_list: List[StockInfo], keyword: str) -> List[StockInfo]:
        """
        搜索股票
        
        Args:
            stock_list: 股票列表
            keyword: 搜索关键词
            
        Returns:
            匹配的股票列表
        """
        keyword_upper = keyword.strip().upper()
        if not keyword_upper:
            return []
        
        matching_stocks = []
        for stock in stock_list:
            if (keyword_upper in stock.code or 
                keyword_upper in stock.pinyin.upper() or
                keyword_upper in stock.name):
                matching_stocks.append(stock)
        
        return matching_stocks