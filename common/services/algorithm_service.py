#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
算法服务层 - 负责所有算法计算
将算法逻辑从UI层分离出来
"""
import logging
from typing import Dict, List, Any, Optional, Callable, Union
from abc import ABC, abstractmethod
from common.model.kline import KLine


class AlgorithmInterface(ABC):
    """算法接口"""
    
    @abstractmethod
    def calculate(self, data: List[KLine], params: Optional[Dict[str, Any]] = None) -> Any:
        """计算算法结果"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """获取算法名称"""
        pass


class ZigZagAlgorithm(AlgorithmInterface):
    """锯齿算法实现"""
    
    def calculate(self, data: List[KLine], params: Optional[Dict[str, Any]] = None) -> Any:
        """计算锯齿线"""
        from common.algo.zigzag import OnCalculate
        return OnCalculate(data)
    
    def get_name(self) -> str:
        return "zigzag"


class WeiBiAlgorithm(AlgorithmInterface):
    """微笔算法实现"""
    
    def calculate(self, data: List[KLine], params: Optional[Dict[str, Any]] = None) -> Any:
        """计算微笔"""
        from common.algo.weibi import get_weibi_list
        return get_weibi_list(data)
    
    def get_name(self) -> str:
        return "weibi"


class AlgorithmRegistry:
    """算法注册表"""
    
    def __init__(self):
        self._algorithms: Dict[str, AlgorithmInterface] = {}
        self._register_default_algorithms()
    
    def _register_default_algorithms(self):
        """注册默认算法"""
        self.register(ZigZagAlgorithm())
        self.register(WeiBiAlgorithm())
    
    def register(self, algorithm: AlgorithmInterface):
        """注册算法"""
        self._algorithms[algorithm.get_name()] = algorithm
    
    def get_algorithm(self, name: str) -> Optional[AlgorithmInterface]:
        """获取算法"""
        return self._algorithms.get(name)
    
    def list_algorithms(self) -> List[str]:
        """列出所有算法名称"""
        return list(self._algorithms.keys())


class AlgorithmService:
    """算法服务 - 负责算法计算和管理"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.registry = AlgorithmRegistry()
        self._function_cache: Dict[str, Callable] = {}
    
    def register_algorithm(self, algorithm: AlgorithmInterface):
        """注册新算法"""
        self.registry.register(algorithm)
        self.logger.info(f"注册算法: {algorithm.get_name()}")
    
    def calculate(self, algorithm_name: str, data: List[KLine], 
                 params: Optional[Dict[str, Any]] = None) -> Any:
        """
        计算算法结果
        
        Args:
            algorithm_name: 算法名称
            data: 输入数据
            params: 参数
            
        Returns:
            算法计算结果
        """
        algorithm = self.registry.get_algorithm(algorithm_name)
        if not algorithm:
            raise ValueError(f"未找到算法: {algorithm_name}")
        
        try:
            result = algorithm.calculate(data, params)
            self.logger.debug(f"算法 {algorithm_name} 计算完成")
            return result
        except Exception as e:
            self.logger.error(f"算法 {algorithm_name} 计算失败: {str(e)}")
            raise
    
    def calculate_by_function_name(self, func_name: str, data: List[KLine]) -> Any:
        """
        通过函数名计算算法（兼容旧代码）
        
        Args:
            func_name: 函数名称
            data: 输入数据
            
        Returns:
            算法计算结果
        """
        if func_name in self._function_cache:
            func = self._function_cache[func_name]
        else:
            # 动态导入函数
            func = self._import_function(func_name)
            if func:
                self._function_cache[func_name] = func
            else:
                raise ValueError(f"未找到函数: {func_name}")
        
        try:
            result = func(data)
            self.logger.debug(f"函数 {func_name} 计算完成")
            return result
        except Exception as e:
            self.logger.error(f"函数 {func_name} 计算失败: {str(e)}")
            raise
    
    def _import_function(self, func_name: str) -> Optional[Callable]:
        """
        动态导入函数
        
        Args:
            func_name: 函数名称
            
        Returns:
            函数对象
        """
        try:
            # 这里可以根据实际情况调整导入逻辑
            import importlib
            
            # 尝试从全局命名空间获取
            import builtins
            if hasattr(builtins, func_name):
                return getattr(builtins, func_name)
            
            # 尝试从common.algo模块导入
            try:
                module = importlib.import_module('common.algo')
                if hasattr(module, func_name):
                    return getattr(module, func_name)
            except ImportError:
                pass
            
            # 可以添加更多的导入路径
            return None
            
        except Exception as e:
            self.logger.warning(f"导入函数 {func_name} 失败: {str(e)}")
            return None
    
    def batch_calculate(self, calculations: List[Dict[str, Any]], 
                       data: List[KLine]) -> Dict[str, Any]:
        """
        批量计算算法
        
        Args:
            calculations: 计算配置列表，每个包含 algorithm_name 和 params
            data: 输入数据
            
        Returns:
            计算结果字典
        """
        results = {}
        for calc in calculations:
            try:
                algorithm_name = calc.get('algorithm_name')
                if not algorithm_name:
                    continue
                    
                params = calc.get('params', {})
                key = calc.get('key', algorithm_name)
                
                result = self.calculate(algorithm_name, data, params)
                results[key] = result
                
            except Exception as e:
                self.logger.error(f"批量计算失败: {calc}, 错误: {str(e)}")
                results[calc.get('key', 'unknown')] = None
        
        return results
    
    def list_available_algorithms(self) -> List[str]:
        """列出可用的算法"""
        return self.registry.list_algorithms()