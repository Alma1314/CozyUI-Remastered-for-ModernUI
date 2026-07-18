#!/usr/bin/env python3
"""验证 extract_config.json ranges 与实际 SVG 文件是否一致"""
import re, json

svg_path = r'd:\Program Files (x86)\GoblinTechMotive\CinderUI\SourceCode 源代码\005-矢量图\005-无样式.svg'
cfg_path = r'd:\Program Files (x86)\GoblinTechMotive\CinderUI\extracted\extract_config.json'

with open(svg_path, 'r', encoding='utf-8') as f:
    lines = [line.rstrip() for line in f.readlines()]

# 追踪所有 <g>
stack = []
named_map = {}  # id -> (start, end)

for i, line in enumerate(lines):
    ln = i + 1
    stripped = line.strip()
    if stripped.startswith('<?') or stripped.startswith('<svg') or stripped.startswith('<!'):
        continue
    if stripped.startswith('</g>') and stack:
        has_id, gid, start = stack.pop()
        if has_id:
            named_map[gid] = (start, ln)
        continue
    if '<g' in stripped and not stripped.startswith('</'):
        m = re.search(r'id="([^"]+)"', line)
        if m:
            stack.append((True, m.group(1), ln))
        else:
            stack.append((False, None, ln))

# 加载 config
with open(cfg_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

# 定义映射关系
id_to_config = {
    '_物品栏-2': ('物品栏', '物品栏'),
    '_副手': ('物品栏', '副手'),
    '_选中': ('物品栏', '选中'),
    '_界面模板': ('界面模板', None),
    '_界面模板_通用背包': ('界面模板 通用背包', None),
    '_本体': ('药水效果', '本体'),
    '_选中-2': ('药水效果', '本体（选中）'),
    '_框本体': ('文本框', '框本体'),
    '_框本体_选中_': ('文本框', '框本体（选中）'),
    '_框底部-2': ('勾选框', '框底部'),
    '_框本体-2': ('勾选框', '框本体'),
    '_框本体_绿色_': ('勾选框', '框本体（绿色）'),
    '_框本体_选中_-2': ('勾选框', '框本体（选中）'),
    '_红色_': ('勾选框', '红色×'),
    '_绿色_': ('勾选框', '绿色√'),
    '_滑块-2': ('滑块', '滑块'),
    '_滑块导轨-2': ('滑块', '滑块导轨'),
    '_滑块禁用': ('滑块', '滑块禁用'),
    '_滑块常态': ('滑块', '滑块常态'),
    '_滑块选中': ('滑块', '滑块选中'),
    '_按钮禁用': ('按钮', '按钮禁用'),
    '_按钮常态': ('按钮', '按钮常态'),
    '_按钮选中': ('按钮', '按钮选中'),
    '_按钮禁用-2': ('按钮_20x', '按钮禁用'),
    '_按钮常态-2': ('按钮_20x', '按钮常态'),
    '_按钮选中-2': ('按钮_20x', '按钮选中'),
    '_按钮禁用-3': ('按钮_20x_无渐变', '按钮禁用'),
    '_按钮常态-3': ('按钮_20x_无渐变', '按钮常态'),
    '_按钮选中-3': ('按钮_20x_无渐变', '按钮选中'),
    '_按钮禁用-4': ('按钮_18x', '按钮禁用'),
    '_按钮常态-4': ('按钮_18x', '按钮常态'),
    '_按钮选中-4': ('按钮_18x', '按钮选中'),
    '_小地图_B': ('小地图 B', '小地图 B'),
    '_小地图_A': ('小地图 A', '小地图 A'),
}

errors = []
for gid, (actual_start, actual_end) in named_map.items():
    if gid in id_to_config:
        comp_name, sub_name = id_to_config[gid]
        # 在 config 中查找
        for c in config["components"]:
            if c["name"] == comp_name:
                if sub_name is None:
                    # simple component
                    if "ranges" in c:
                        cfg_ranges = c["ranges"]
                        if len(cfg_ranges) >= 1:
                            cfg_start, cfg_end = cfg_ranges[0]
                            if cfg_start != actual_start or cfg_end != actual_end:
                                errors.append(f'{comp_name}: config [{cfg_start},{cfg_end}] != actual [{actual_start},{actual_end}] (id={gid})')
                else:
                    if "sub_components" in c:
                        for sc in c["sub_components"]:
                            if sc["name"] == sub_name:
                                for r in sc["ranges"]:
                                    cfg_start, cfg_end = r
                                    if cfg_start != actual_start or cfg_end != actual_end:
                                        errors.append(f'{comp_name}/{sub_name}: config [{cfg_start},{cfg_end}] != actual [{actual_start},{actual_end}] (id={gid})')
                                break

if errors:
    print("❌ MISMATCHES:")
    for e in errors:
        print(f"  {e}")
else:
    print("✅ 所有 ranges 匹配！")

print(f"\n总计检查 {len([g for g in id_to_config if g in named_map])} 个组件")
