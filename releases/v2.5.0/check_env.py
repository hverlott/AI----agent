#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
环境检查工具
检查系统环境、Python 版本、依赖包和配置文件
"""

import sys
import os
import platform
from pathlib import Path

def print_header(text):
    """打印标题"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def check_python_version():
    """检查 Python 版本"""
    print_header("1. Python 版本检查")
    
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    print(f"Python 版本: {version_str}")
    print(f"Python 路径: {sys.executable}")
    print(f"操作系统: {platform.system()} {platform.release()}")
    
    if version.major == 3 and version.minor >= 8:
        print("✅ Python 版本符合要求 (3.8+)")
        return True
    else:
        print("❌ Python 版本过低，需要 3.8 或更高版本")
        return False

def check_dependencies():
    """检查依赖包"""
    print_header("2. 依赖包检查")
    
    required_packages = {
        'telethon': '1.34.0',
        'openai': '1.30.0',
        'streamlit': '1.30.0',
        'python-dotenv': '1.0.0',
        'httpx': '0.27.0',
        'psutil': '5.9.0'
    }
    
    all_installed = True
    
    for package, min_version in required_packages.items():
        try:
            if package == 'python-dotenv':
                import dotenv
                installed_version = dotenv.__version__
            else:
                module = __import__(package)
                installed_version = getattr(module, '__version__', 'unknown')
            
            print(f"✅ {package}: {installed_version}")
        except ImportError:
            print(f"❌ {package}: 未安装")
            all_installed = False
    
    if not all_installed:
        print("\n💡 安装缺失的依赖包:")
        print("   pip install -r requirements.txt")
    
    return all_installed

def check_config_files():
    """检查配置文件"""
    print_header("3. 配置文件检查")
    
    files_to_check = {
        '.env': '环境配置文件',
        'prompt.txt': 'AI 人设配置',
        'keywords.txt': '触发关键词配置',
        'requirements.txt': '依赖包列表',
        'main.py': '主程序',
        'admin.py': '管理后台',
        'broadcast.py': '群发工具'
    }
    
    all_exist = True
    
    for filename, description in files_to_check.items():
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            print(f"✅ {filename:20s} - {description:15s} ({size} 字节)")
        else:
            print(f"❌ {filename:20s} - {description:15s} (缺失)")
            all_exist = False
    
    return all_exist

def check_env_variables():
    """检查环境变量"""
    print_header("4. 环境变量检查")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        required_vars = {
            'TELEGRAM_API_ID': 'Telegram API ID',
            'TELEGRAM_API_HASH': 'Telegram API Hash',
            'AI_API_KEY': 'AI API 密钥',
            'AI_BASE_URL': 'AI API 地址',
            'AI_MODEL_NAME': 'AI 模型名称'
        }
        
        all_set = True
        
        for var, description in required_vars.items():
            value = os.getenv(var)
            if value:
                # 隐藏敏感信息
                if 'KEY' in var or 'HASH' in var:
                    display_value = value[:8] + '...' if len(value) > 8 else '***'
                else:
                    display_value = value
                print(f"✅ {var:20s} - {description:15s} = {display_value}")
            else:
                print(f"❌ {var:20s} - {description:15s} (未设置)")
                all_set = False
        
        if not all_set:
            print("\n💡 请编辑 .env 文件，填写必要的配置")
        
        return all_set
    except ImportError:
        print("❌ python-dotenv 未安装，无法检查环境变量")
        return False

def check_session_files():
    """检查 Session 文件"""
    print_header("5. Session 文件检查")
    
    session_files = {
        'userbot_session.session': '主程序 Session',
        'admin_session.session': '管理后台 Session'
    }
    
    has_session = False
    
    for filename, description in session_files.items():
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            print(f"✅ {filename:25s} - {description} ({size} 字节)")
            has_session = True
        else:
            print(f"⚠️ {filename:25s} - {description} (未创建)")
    
    if not has_session:
        print("\n💡 Session 文件会在首次登录 Telegram 时自动创建")
        print("   运行: python main.py")
    
    return True  # Session 文件不是必需的，首次运行会创建

def provide_next_steps(results):
    """提供下一步操作建议"""
    print_header("📝 检查总结")
    
    issues = []
    
    if not results['python']:
        issues.append("升级 Python 到 3.8 或更高版本")
    
    if not results['dependencies']:
        issues.append("安装缺失的依赖包: pip install -r requirements.txt")
    
    if not results['config_files']:
        issues.append("确保所有必需文件都已下载")
    
    if not results['env_variables']:
        issues.append("编辑 .env 文件，填写 API 密钥和配置")
    
    if issues:
        print("\n❌ 发现以下问题需要解决：\n")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
        print("\n")
        return False
    else:
        print("\n✅ 所有检查通过！环境配置完成！\n")
        print("🚀 下一步操作：")
        print("\n   1. 首次登录 Telegram:")
        print("      python main.py")
        print("\n   2. 启动管理后台:")
        print("      streamlit run admin.py")
        print("      或运行: start_admin.bat (Windows) / ./start_admin.sh (Linux/Mac)")
        print("\n   3. 使用命令行群发:")
        print("      python broadcast.py")
        print("\n")
        return True

def main():
    """主函数"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        🤖 Telegram AI Bot - 环境检查工具                    ║
║                                                              ║
║  检查系统环境、依赖包和配置文件是否正确                     ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    results = {
        'python': check_python_version(),
        'dependencies': check_dependencies(),
        'config_files': check_config_files(),
        'env_variables': check_env_variables(),
        'session_files': check_session_files()
    }
    
    success = provide_next_steps(results)
    
    return 0 if success else 1

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ 检查已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 检查过程出错: {e}")
        sys.exit(1)


