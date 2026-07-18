"""
SVG Component Extractor — 从大型 SVG 中提取指定组件组的矢量资源

用法:
    python extract_svg_component.py <svg_file> <group_id> <output_dir> [--bbox x,y,w,h]

示例:
    python extract_svg_component.py "005-无样式.svg" "_按钮_18x" "extracted/按钮_18x"
    python extract_svg_component.py "005-无样式.svg" "_按钮_18x" "extracted/按钮_18x" --bbox 1622,482,72,72

功能:
    1. 解析指定组的层级结构（<g id="..."> 嵌套）
    2. 收集所有引用资源（url(#gradient-id)）
    3. 从 <defs> 中提取完整 gradient 定义
    4. 生成独立 SVG 文件 + 复合 SVG + JSON 元数据

注意:
    - 默认不做坐标平移，保留原始画布坐标
    - 使用 --bbox 参数手动指定 viewBox（格式: x,y,w,h）
    - 自动计算包围盒功能暂时禁用（因为相对坐标处理复杂）
"""
import sys, os, re, json, xml.etree.ElementTree as ET
from collections import defaultdict

NS = {'svg': 'http://www.w3.org/2000/svg', 'xlink': 'http://www.w3.org/1999/xlink'}

def parse_svg(svg_path):
    """解析 SVG 文件，返回 ElementTree"""
    with open(svg_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # 注册命名空间
    for prefix, uri in NS.items():
        ET.register_namespace(prefix, uri)
    return ET.fromstring(content), content

def find_group(root, group_id):
    """查找指定 ID 的组元素"""
    for elem in root.iter():
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        if tag == 'g' and elem.get('id') == group_id:
            return elem
    return None

def collect_refs(element, refs=None):
    """收集元素及其子元素中所有引用的资源 ID"""
    if refs is None:
        refs = set()

    # 检查所有属性中的 url(#...) 引用
    for attr, value in element.attrib.items():
        if value and 'url(#' in value:
            match = re.search(r'url\(#([^)]+)\)', value)
            if match:
                refs.add(match.group(1))

    # 检查 xlink:href 引用
    href = element.get('{http://www.w3.org/1999/xlink}href')
    if href and href.startswith('#'):
        refs.add(href[1:])

    # 递归子元素
    for child in element:
        collect_refs(child, refs)

    return refs

def extract_defs(root, refs):
    """从 defs 中提取引用的资源定义"""
    defs = None
    for elem in root.iter():
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        if tag == 'defs':
            defs = elem
            break

    if not defs:
        return []

    extracted = []
    for elem in defs:
        elem_id = elem.get('id')
        if elem_id in refs:
            extracted.append(elem)
            # 如果是 xlink:href 引用，也需要提取被引用的原定义
            href = elem.get('{http://www.w3.org/1999/xlink}href')
            if href and href.startswith('#'):
                original_id = href[1:]
                if original_id not in refs:
                    refs.add(original_id)
                    # 递归查找原定义
                    for orig in defs:
                        if orig.get('id') == original_id:
                            extracted.insert(0, orig)
                            break

    return extracted

def calc_bbox(element):
    """计算元素及其子元素的包围盒（基于 path/rect/ellipse 的坐标）"""
    min_x, min_y = float('inf'), float('inf')
    max_x, max_y = float('-inf'), float('-inf')

    def parse_path_d(d):
        """从 path d 属性提取所有坐标点"""
        nums = re.findall(r'[-\d.]+', d)
        points = []
        for i in range(0, len(nums)-1, 2):
            try:
                x, y = float(nums[i]), float(nums[i+1])
                points.append((x, y))
            except:
                pass
        return points

    def update_bbox(elem, parent_dx=0, parent_dy=0):
        nonlocal min_x, min_y, max_x, max_y
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag

        # 处理当前元素的 transform
        transform = elem.get('transform', '')
        local_dx, local_dy = parent_dx, parent_dy
        if 'translate' in transform:
            match = re.search(r'translate\(([-\d.]+)[,\s]+([-\d.]+)\)', transform)
            if match:
                local_dx += float(match.group(1))
                local_dy += float(match.group(2))

        if tag == 'path':
            d = elem.get('d')
            if d:
                for x, y in parse_path_d(d):
                    min_x = min(min_x, x + local_dx)
                    max_x = max(max_x, x + local_dx)
                    min_y = min(min_y, y + local_dy)
                    max_y = max(max_y, y + local_dy)

        elif tag == 'rect' or tag == 'image':
            x = float(elem.get('x', 0)) + local_dx
            y = float(elem.get('y', 0)) + local_dy
            w = float(elem.get('width', 0))
            h = float(elem.get('height', 0))
            min_x = min(min_x, x)
            max_x = max(max_x, x + w)
            min_y = min(min_y, y)
            max_y = max(max_y, y + h)

        elif tag == 'ellipse' or tag == 'circle':
            cx = float(elem.get('cx', 0)) + local_dx
            cy = float(elem.get('cy', 0)) + local_dy
            r = float(elem.get('r', 0)) if tag == 'circle' else float(elem.get('rx', 0))
            ry_val = float(elem.get('ry', r)) if tag == 'ellipse' else r
            min_x = min(min_x, cx - r)
            max_x = max(max_x, cx + r)
            min_y = min(min_y, cy - ry_val)
            max_y = max(max_y, cy + ry_val)

        # 递归子元素
        for child in elem:
            update_bbox(child, local_dx, local_dy)

    update_bbox(element)

    if min_x == float('inf'):
        return 0, 0, 100, 100  # 默认值

    return min_x, min_y, max_x - min_x, max_y - min_y

def translate_d(d, dx, dy):
    """将 SVG path d 中的坐标整体偏移 (dx, dy)"""
    def offset_num(m):
        val = float(m.group(0))
        # 判断是 x 还是 y：基于位置奇偶性
        # 简化处理：所有数字都尝试偏移
        return str(val + (dx if m.start() % 2 == 0 else dy))

    # 更精确的处理：按命令参数顺序
    result = []
    pos = 0
    pattern = re.compile(r'([MmLlHhVvCcSsQqTtAaZz])([^MmLlHhVvCcSsQqTtAaZz]*)')

    for m in pattern.finditer(d):
        result.append(d[pos:m.start()])
        cmd = m.group(1)
        nums_str = m.group(2).strip()

        if not nums_str:
            result.append(cmd)
            pos = m.end()
            continue

        nums = re.findall(r'-?\d+(?:\.\d+)?', nums_str)  # 正确提取数字（包括负数）
        new_nums = []

        abs_cmd = cmd.upper()
        if abs_cmd in ('M', 'L', 'T'):
            for i in range(0, len(nums), 2):
                if i+1 < len(nums):
                    new_nums.append(f"{float(nums[i]) + (dx if cmd.isupper() else 0):.3f}")
                    new_nums.append(f"{float(nums[i+1]) + (dy if cmd.isupper() else 0):.3f}")
        elif abs_cmd == 'H':
            for v in nums:
                new_nums.append(f"{float(v) + (dx if cmd.isupper() else 0):.3f}")
        elif abs_cmd == 'V':
            for v in nums:
                new_nums.append(f"{float(v) + (dy if cmd.isupper() else 0):.3f}")
        elif abs_cmd == 'C':
            for i in range(0, len(nums), 6):
                if i+5 < len(nums):
                    for j in range(6):
                        offset = dx if j % 2 == 0 else dy
                        new_nums.append(f"{float(nums[i+j]) + (offset if cmd.isupper() else 0):.3f}")
        elif abs_cmd in ('S', 'Q'):
            for i in range(0, len(nums), 4):
                if i+3 < len(nums):
                    for j in range(4):
                        offset = dx if j % 2 == 0 else dy
                        new_nums.append(f"{float(nums[i+j]) + (offset if cmd.isupper() else 0):.3f}")
        elif abs_cmd == 'A':
            for i in range(0, len(nums), 7):
                if i+6 < len(nums):
                    new_nums.extend([nums[i], nums[i+1], nums[i+2], nums[i+3], nums[i+4]])  # rx,ry,rot,large,sweep
                    new_nums.append(f"{float(nums[i+5]) + (dx if cmd.isupper() else 0):.3f}")
                    new_nums.append(f"{float(nums[i+6]) + (dy if cmd.isupper() else 0):.3f}")
        else:
            new_nums = nums  # Z/z 无参数

        result.append(cmd + ' ' + ' '.join(new_nums))
        pos = m.end()

    result.append(d[pos:])
    return ''.join(result)

def translate_element(elem, dx, dy):
    """将元素坐标整体偏移 (dx, dy)"""
    tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag

    if tag == 'path':
        d = elem.get('d')
        if d:
            elem.set('d', translate_d(d, dx, dy))

    elif tag == 'rect' or tag == 'image':
        x = float(elem.get('x', 0))
        y = float(elem.get('y', 0))
        elem.set('x', f"{x + dx:.3f}")
        elem.set('y', f"{y + dy:.3f}")

    elif tag == 'ellipse' or tag == 'circle':
        cx = float(elem.get('cx', 0))
        cy = float(elem.get('cy', 0))
        elem.set('cx', f"{cx + dx:.3f}")
        elem.set('cy', f"{cy + dy:.3f}")

    elif tag == 'g':
        # 递归处理子元素
        for child in elem:
            translate_element(child, dx, dy)

def serialize_defs(defs_elems):
    """将 defs 元素序列化为字符串"""
    lines = []
    for elem in defs_elems:
        # 手动序列化，保留属性顺序
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        attrs = []
        for attr, val in elem.attrib.items():
            attr_name = attr.split('}')[-1] if '}' in attr else attr
            attrs.append(f'{attr_name}="{val}"')
        attrs_str = ' '.join(attrs)

        if tag == 'linearGradient':
            stops = []
            for stop in elem:
                stop_attrs = []
                for attr, val in stop.attrib.items():
                    attr_name = attr.split('}')[-1] if '}' in attr else attr
                    stop_attrs.append(f'{attr_name}="{val}"')
                stops.append(f'      <stop { " ".join(stop_attrs) }/>')
            lines.append(f'    <linearGradient {attrs_str}>')
            lines.extend(stops)
            lines.append('    </linearGradient>')
        else:
            lines.append(f'    <{tag} {attrs_str}/>')

    return '\n'.join(lines)

def serialize_element(elem, indent='  '):
    """将元素序列化为 SVG 字符串"""
    tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
    attrs = []
    for attr, val in elem.attrib.items():
        attr_name = attr.split('}')[-1] if '}' in attr else attr
        attrs.append(f'{attr_name}="{val}"')
    attrs_str = ' '.join(attrs)

    if len(elem) == 0:
        return f'{indent}<{tag} {attrs_str}/>'
    else:
        lines = [f'{indent}<{tag} {attrs_str}>']
        for child in elem:
            lines.append(serialize_element(child, indent + '  '))
        lines.append(f'{indent}</{tag}>')
        return '\n'.join(lines)

def extract_component(svg_path, group_id, output_dir, bbox=None):
    """提取指定组件组

    Args:
        svg_path: SVG 文件路径
        group_id: 要提取的组 ID
        output_dir: 输出目录
        bbox: 手动指定的包围盒 (x, y, w, h)，可选
    """
    root, raw_content = parse_svg(svg_path)
    target_group = find_group(root, group_id)

    if not target_group:
        print(f"错误: 未找到组 '{group_id}'")
        return None

    print(f"找到组: {group_id}")

    # 1. 解析子组结构
    subgroups = []
    for elem in target_group.iter():
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        if tag != 'g':
            continue
        if elem == target_group:
            continue
        child_id = elem.get('id')
        if child_id:
            refs = collect_refs(elem)
            subgroups.append({
                'id': child_id,
                'element': elem,
                'refs': refs,
            })

    print(f"  子组数: {len(subgroups)}")

    # 2. 收集所有引用资源
    all_refs = set()
    for sg in subgroups:
        all_refs.update(sg['refs'])

    print(f"  引用资源: {len(all_refs)} 个 gradient")

    # 3. 提取 defs
    defs_elems = extract_defs(root, all_refs)
    defs_str = serialize_defs(defs_elems)

    # 4. 确定 viewBox
    if bbox:
        viewbox_x, viewbox_y, viewbox_w, viewbox_h = bbox
    else:
        # 默认使用原始 SVG 的 viewBox（从根元素提取）
        svg_root = None
        for elem in root.iter():
            tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            if tag == 'svg':
                svg_root = elem
                break
        if svg_root:
            vb = svg_root.get('viewBox', '0 0 2000 2000')
            parts = vb.split()
            viewbox_x, viewbox_y, viewbox_w, viewbox_h = float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3])
        else:
            viewbox_x, viewbox_y, viewbox_w, viewbox_h = 0, 0, 2000, 2000

    # 5. 生成母版 SVG（每个顶层子组 = 一个状态的完整按钮）
    os.makedirs(output_dir, exist_ok=True)

    metadata = {
        'source': os.path.basename(svg_path),
        'group_id': group_id,
        'viewbox': [viewbox_x, viewbox_y, viewbox_w, viewbox_h],
        'states': [],
    }

    # 按名称分组：按钮常态、按钮禁用、按钮选中
    # 子组 ID 格式: _按钮禁用_0-10, _按钮禁用_1-5, _按钮禁用_2-7, _按钮禁用-4 等
    # 状态名 = ID 去掉前缀和后缀（如 "_按钮禁用_0-10" -> "按钮禁用"）
    state_groups = defaultdict(list)
    for sg in subgroups:
        raw_id = sg['id'].lstrip('_')
        # 去掉末尾的 _数字-数字 或 -数字 部分
        import re
        state_name = re.sub(r'[-_]\d+(?:-\d+)?$', '', raw_id)
        state_groups[state_name].append(sg)

    for state_name, child_groups in state_groups.items():
        # 该状态真正引用的渐变
        state_refs = set()
        for cg in child_groups:
            state_refs.update(cg['refs'])

        # 只提取该状态真正用到的渐变
        state_defs = extract_defs(root, state_refs)
        state_defs_str = serialize_defs(state_defs)

        # 合并所有子组
        content_parts = []
        for cg in child_groups:
            import copy
            cg_copy = copy.deepcopy(cg['element'])
            content_parts.append(serialize_element(cg_copy, '  '))

        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     viewBox="{viewbox_x} {viewbox_y} {viewbox_w} {viewbox_h}" width="{viewbox_w}" height="{viewbox_h}">
  <defs>
{state_defs_str}
  </defs>
{''.join(content_parts)}
</svg>
'''

        safe_name = state_name.replace('_', '-')
        out_path = os.path.join(output_dir, f'{safe_name}.svg')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)

        print(f"  OK {safe_name}.svg (refs: {len(state_refs)})")

        metadata['states'].append({
            'name': state_name,
            'refs': list(state_refs),
            'layers': len(child_groups),
        })

    # 6. 输出元数据
    meta_path = os.path.join(output_dir, 'metadata.json')
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"  OK metadata.json")

    return metadata

def main():
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)

    svg_path = sys.argv[1]
    group_id = sys.argv[2]
    output_dir = sys.argv[3]

    # 解析可选的 bbox 参数
    bbox = None
    if len(sys.argv) >= 5 and sys.argv[4] == '--bbox':
        if len(sys.argv) >= 6:
            bbox_parts = sys.argv[5].split(',')
            if len(bbox_parts) == 4:
                bbox = [float(x) for x in bbox_parts]

    extract_component(svg_path, group_id, output_dir, bbox)

if __name__ == '__main__':
    main()