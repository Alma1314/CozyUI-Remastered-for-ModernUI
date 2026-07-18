#!/usr/bin/env python3
"""CinderUI — 转角参数验证脚本"""
import json, os

params_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                           'extracted', 'parameters.json')

with open(params_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

corner = data['corner_parameters']
print(f"CinderUI — 转角参数验证")
print(f"总形状: {data['total_shapes']}")
print(f"复合组件: {data['total_composites']}")
print(f"圆角矩形数: {len(corner)}\n")

print(f"{'名称':<30} {'尺寸':<10} {'t':<8} {'c':<8}")
print(f"{'-'*56}")
for cp in corner:
    name = cp['name'].rsplit('/', 1)[-1] if '/' in cp['name'] else cp['name']
    print(f"{name:<30} {cp['size']:<10} {cp['t']:<8} {cp['c']:<8}")
