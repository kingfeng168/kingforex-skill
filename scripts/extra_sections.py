# -*- coding: utf-8 -*-
"""extra_sections —— 稳定模块名别名

背景：v2.5.2 / v2.5.4 / v2.5.6 生成器均以 `import extra_sections as XS` 引用本模块，
但仓库内实际文件名带日期后缀（extra_sections_20260916.py）。
在全新机器上首次运行时因找不到 extra_sections.py 而 ModuleNotFoundError。

本文件仅做转发，两侧永远同源、无需手工同步。
后续「调准格式」若新建 extra_sections_<新日期>.py，只需改下面这一行 import。
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import extra_sections_20260916 as _impl          # noqa: E402

for _n in dir(_impl):
    if not _n.startswith("_"):
        globals()[_n] = getattr(_impl, _n)
del _n

__all__ = [n for n in dir(_impl) if not n.startswith("_")]
__doc__ = (_impl.__doc__ or "") + "\n\n(本文件为稳定别名，实体实现见 extra_sections_20260916.py)"
