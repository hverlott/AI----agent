import json
import logging
import inspect
from typing import Dict, Any, List, Callable, Optional

logger = logging.getLogger(__name__)

class SkillRegistry:
    """
    技能注册中心 (Skill Registry)
    负责管理和执行所有注册的技能（工具/函数）。
    支持 Function Calling 格式导出。
    """
    def __init__(self):
        self._skills: Dict[str, Dict[str, Any]] = {}

    def register_tool(self, name: str, description: str, parameters: Dict[str, Any]):
        """
        装饰器：注册一个函数为技能
        :param name: 工具名称 (e.g., "check_order")
        :param description: 工具描述
        :param parameters: JSON Schema 格式的参数定义
        """
        def decorator(func: Callable):
            self._skills[name] = {
                "name": name,
                "description": description,
                "parameters": parameters,
                "func": func
            }
            return func
        return decorator

    def get_tools_definition(self, tenant_id: str = None, db = None) -> List[Dict[str, Any]]:
        """
        获取符合 OpenAI Function Calling 格式的工具定义列表
        :param tenant_id: 租户ID (用于DB过滤)
        :param db: 数据库实例
        """
        tools = []
        
        # 1. Get enabled skills from DB
        enabled_skills = set()
        db_configs = {}
        if tenant_id and db:
            try:
                # Assuming db.get_enabled_skills returns list of dicts with 'name' and 'config_json'
                # We use list_skills and filter enabled=1
                skills = db.list_skills(tenant_id)
                for s in skills:
                    if s.get("enabled"):
                        enabled_skills.add(s.get("name"))
                        db_configs[s.get("name")] = s.get("config") or {}
            except Exception as e:
                logger.error(f"Failed to load skills from DB: {e}")
                # Fallback: enable all if DB fails? Or none? 
                # Let's enable built-ins by default if no DB info, but strict is better.
                pass
        else:
            # If no context, enable all (backward compatibility or default behavior)
            enabled_skills = set(self._skills.keys())

        for name, skill in self._skills.items():
            # Filter
            if tenant_id and db and name not in enabled_skills:
                continue
                
            tools.append({
                "type": "function",
                "function": {
                    "name": skill["name"],
                    "description": skill["description"],
                    "parameters": skill["parameters"]
                }
            })
        return tools

    def execute_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        """
        执行指定名称的工具
        """
        skill = self._skills.get(name)
        if not skill:
            return f"Error: Tool '{name}' not found."
        
        try:
            func = skill["func"]
            # 支持异步或同步函数（这里暂时只处理同步，如果是异步需要在上层 await）
            # 实际上在 ai.py 调用时通常是异步环境，但这里 execute 是同步封装
            # 如果 func 是 async，则需要在外部 await。为了简化，假设 skills 都是同步的 IO 操作或快速计算
            if inspect.iscoroutinefunction(func):
                # 这是一个限制，如果需要支持 async tools，架构需要调整
                # 这里暂时返回提示，或者要求注册时只能是同步函数
                return f"Error: Async tool '{name}' execution not supported in sync context."
            
            result = func(**arguments)
            return str(result)
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return f"Error executing tool '{name}': {str(e)}"

# Global Registry Instance
skill_registry = SkillRegistry()

# --- 内置基础技能示例 ---

@skill_registry.register_tool(
    name="get_current_time",
    description="获取当前系统时间",
    parameters={
        "type": "object",
        "properties": {
            "timezone": {
                "type": "string",
                "description": "时区，例如 'Asia/Shanghai'"
            }
        },
        "required": []
    }
)
def get_current_time(timezone: str = "Asia/Shanghai"):
    from datetime import datetime
    import pytz
    try:
        tz = pytz.timezone(timezone)
        return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %Z")
    except Exception:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@skill_registry.register_tool(
    name="calculator",
    description="执行简单的数学计算",
    parameters={
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "数学表达式，例如 '12 * 5 + 10'"
            }
        },
        "required": ["expression"]
    }
)
def calculator(expression: str):
    # 安全起见，仅允许简单字符
    import re
    if not re.match(r"^[0-9+\-*/().\s]+$", expression):
        return "Error: Invalid characters in expression."
    try:
        # pylint: disable=eval-used
        return str(eval(expression))
    except Exception as e:
        return f"Error: {e}"

