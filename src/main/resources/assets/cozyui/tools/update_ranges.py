#!/usr/bin/env python3
"""
行号维护工具 — 对 extract_config.json 执行批量行号偏移。

用法:
    python tools/update_ranges.py <config> <偏移量列表>

偏移量列表格式 — 每个偏移量用逗号分隔：
    <起始行>:<增量>

示例:
    # 在源文件第 246 行之后插入了 2 行，第 472 行之后插入了 3 行
    python tools/update_ranges.py extracted/extract_config.json 247:+2,475:+3

    # 也支持负偏移（删除行）
    python tools/update_ranges.py extracted/extract_config.json 250:-1

偏移规则：
    - 对 config 中每个 range 的起止行号应用所有符合条件的偏移量
    - 条件：range 的起始行 >= 偏移起始行  → 起止都 += 增量
    - 偏移量按起始行升序处理（避免嵌套偏移互相干扰）
"""

import json, sys, re


def parse_offsets(offset_str: str):
    """解析 '247:+2,475:+3' → [(247, 2), (475, 3)]"""
    offsets = []
    for part in offset_str.split(','):
        part = part.strip()
        m = re.match(r'^(\d+)\s*:\s*([+-]\d+)$', part)
        if not m:
            print(f"  ✗ 无法解析偏移量: {part} (格式: 行号:+/-增量)")
            sys.exit(1)
        offsets.append((int(m.group(1)), int(m.group(2))))
    offsets.sort(key=lambda x: x[0])
    return offsets


def apply_offsets(value, offsets):
    """对单个 range 起止值应用偏移列表"""
    for start_line, delta in offsets:
        if value >= start_line:
            value += delta
    return value


def update_config(config_path, offsets):
    print(f"  配置文件: {config_path}")
    print(f"  偏移量: {offsets}")

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    total_updates = 0
    for comp in config.get('components', []):
        # simple 模式
        for ri, r in enumerate(comp.get('ranges', [])):
            old = tuple(r)
            r[0] = apply_offsets(r[0], offsets)
            r[1] = apply_offsets(r[1], offsets)
            if old != tuple(r):
                print(f"    {comp.get('name', comp.get('id'))}.ranges[{ri}]: {old} → {tuple(r)}")
                total_updates += 1

        # sub_components 模式
        for sub in comp.get('sub_components', []):
            for ri, r in enumerate(sub.get('ranges', [])):
                old = tuple(r)
                r[0] = apply_offsets(r[0], offsets)
                r[1] = apply_offsets(r[1], offsets)
                if old != tuple(r):
                    sub_name = sub.get('name', sub.get('id', f'sub[{ri}]'))
                    print(f"    {comp.get('name', comp.get('id'))}.{sub_name}.ranges[{ri}]: {old} → {tuple(r)}")
                    total_updates += 1

    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    print(f"\n  更新完成，共 {total_updates} 处变更")


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)

    config_path = sys.argv[1]
    offset_str = sys.argv[2]
    offsets = parse_offsets(offset_str)
    update_config(config_path, offsets)


if __name__ == '__main__':
    main()
