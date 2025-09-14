#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重构后的主程序 - 模块化架构
展示如何使用分离后的各个模块
"""
import os
import sys
import logging

# 设置工作目录和路径
work_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(work_dir)
sys.path.append(work_dir)

# 导入服务模块
from common.logging_cfg import SysLogInit
from common.ui.refactored_main_window import RefactoredMainWindow, create_app
from common.http.httpserver import PyHttpServer
from cfg import g_cfg


def main():
    """主函数 - 启动应用程序"""
    try:
        # 1. 初始化日志系统
        SysLogInit('a6_fen_xing', 'logs/a1_kline_chart/a6_fen_xing')
        logging.info(f"工作目录: {work_dir}")
        
        # 2. 加载配置文件
        config = g_cfg.load_yaml()
        if not config:
            logging.error("配置文件加载失败")
            return 1
        
        # 3. 启动HTTP服务器（可选）
        http_server = PyHttpServer()
        http_server.start()
        logging.info("HTTP服务器启动完成")
        
        # 4. 创建Qt应用程序
        app = create_app()
        
        # 5. 创建主窗口（使用重构后的版本）
        main_window = RefactoredMainWindow(config)
        main_window.show()
        
        logging.info("应用程序启动完成")
        
        # 6. 进入事件循环
        return app.exec()
        
    except Exception as e:
        logging.error(f"应用程序启动失败: {str(e)}")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)