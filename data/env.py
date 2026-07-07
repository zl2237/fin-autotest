"""Data 层共享环境加载器

根据 TEST_ENV 环境变量，加载 `data/<domain>/<name>_{env}.yaml`。
"""
import os
from pathlib import Path
from typing import Dict, Any

import yaml


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """递归合并两个字典，override 优先级更高"""
    result = dict(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def _load_yaml(name: str, package: str = None) -> Dict[str, Any]:
    """加载指定 name 的 YAML。

    有 TEST_ENV 时：只加载 <name>_{env}.yaml（环境专属，无 base 文件）。
    无 TEST_ENV 时：加载 <name>.yaml（默认 base）。
    """
    env = os.environ.get("TEST_ENV", "").strip()

    # 定位当前 data 子包的目录
    if package is None:
        caller_frame = None
        try:
            import sys
            caller_frame = sys._getframe(1)
        except Exception:
            pass
        if caller_frame is not None:
            yaml_dir = Path(caller_frame.f_code.co_filename).parent
        else:
            yaml_dir = Path(__file__).parent
    else:
        yaml_dir = Path(__file__).parent / package

    cfg: Dict[str, Any] = {}

    if env:
        # 环境专属文件（唯一来源）
        env_path = yaml_dir / f"{name}_{env}.yaml"
        if env_path.exists():
            with open(env_path, encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
        else:
            raise FileNotFoundError(
                f"配置文件不存在: {env_path} (TEST_ENV={env})"
            )
    else:
        # 默认 base 文件
        base_path = yaml_dir / f"{name}.yaml"
        if base_path.exists():
            with open(base_path, encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
        else:
            raise FileNotFoundError(f"配置文件不存在: {base_path}")

    return cfg
