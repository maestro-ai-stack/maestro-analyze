"""错误层级。"""


class AnalystError(Exception):
    """基础错误。"""


class DataLoadError(AnalystError):
    """数据加载失败。"""


class AnalysisError(AnalystError):
    """分析过程出错。"""


class TemplateError(AnalystError):
    """模板解析/执行出错。"""
