#!/usr/bin/env python3
"""
从 005-无样式.svg 按行范围提取 UI 组件，并对 _1 层应用边缘发光效果。

用法:
    python tools/extract_components.py [--config extracted/extract_config.json]

配置格式参见 extracted/extract_config.json
"""

import os, re, json, sys, copy
from collections import defaultdict
from xml.etree import ElementTree as ET

# ── 命名空间 ──
SVG_NS = 'http://www.w3.org/2000/svg'
XLINK_NS = 'http://www.w3.org/1999/xlink'

# ── 物品栏纹理基 pattern（硬编码，供 href 链解析注入）──
TEXTURE_BASE_PATTERN = '''    <linearGradient id="_新建渐变色板_12" x1="108" y1="68" x2="108" y2="0" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#7f8083"/>
      <stop offset="1" stop-color="#737477"/>
    </linearGradient>
    <linearGradient id="_未命名的渐变_765" x1="36" y1="140" x2="36" y2="72" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#7f8083"/>
      <stop offset="1" stop-color="#737477"/>
    </linearGradient>
    <linearGradient id="_新建渐变色板_11" x1="36" y1="68" x2="36" y2="0" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#8f9093"/>
      <stop offset="1" stop-color="#838487"/>
    </linearGradient>
    <linearGradient id="_未命名的渐变_812" x1="108" y1="140" x2="108" y2="72" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#8f9093"/>
      <stop offset="1" stop-color="#838487"/>
    </linearGradient>
    <pattern id="界面模板_2_2物品槽_外框_纹理_基" patternUnits="userSpaceOnUse" width="144" height="144">
      <rect x="72" width="72" height="68" fill="url(#_新建渐变色板_12)"/>
      <rect y="72" width="72" height="68" fill="url(#_未命名的渐变_765)"/>
      <rect width="72" height="68" fill="url(#_新建渐变色板_11)"/>
      <rect x="72" y="72" width="72" height="68" fill="url(#_未命名的渐变_812)"/>
      <rect y="68" width="144" height="4" fill="#a1a2a5"/>
      <rect y="140" width="144" height="4" fill="#a1a2a5"/>
    </pattern>'''
NS = {'svg': SVG_NS, 'xlink': XLINK_NS}

for prefix, uri in NS.items():
    ET.register_namespace(prefix, uri)

CINDER_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ═══════════════════════════════════════════
#   path d 解析 — 求包围盒
# ═══════════════════════════════════════════

def parse_path_d(d):
    """解析 SVG path d 属性，返回绝对坐标点列表 [(x,y), ...]"""
    # 用正则提取命令+参数对
    pattern = re.compile(r'([MmLlHhVvCcSsQqTtAaZz])\s*([^MmLlHhVvCcSsQqTtAaZz]*)')
    tokens = pattern.findall(d)

    points = []
    cx, cy = 0, 0
    first_x, first_y = None, None

    for cmd, args_str in tokens:
        # 解析参数（支持逗号/空格/负号分隔）
        args = [float(x) for x in re.findall(r'-?\d+(?:\.\d+)?', args_str)]
        is_rel = cmd.islower()
        cmd_up = cmd.upper()
        arg_idx = 0

        if cmd_up == 'M':
            while arg_idx + 1 < len(args):
                dx, dy = args[arg_idx], args[arg_idx+1]
                if is_rel:
                    cx += dx
                    cy += dy
                else:
                    cx, cy = dx, dy
                first_x, first_y = cx, cy
                points.append((cx, cy))
                arg_idx += 2
                # 多坐标对的 M 后续当作 L
                is_rel, cmd_up = False, 'L'

        elif cmd_up == 'L':
            while arg_idx + 1 < len(args):
                dx, dy = args[arg_idx], args[arg_idx+1]
                if is_rel:
                    cx += dx; cy += dy
                else:
                    cx, cy = dx, dy
                points.append((cx, cy))
                arg_idx += 2

        elif cmd_up == 'H':
            while arg_idx < len(args):
                if is_rel:
                    cx += args[arg_idx]
                else:
                    cx = args[arg_idx]
                points.append((cx, cy))
                arg_idx += 1

        elif cmd_up == 'V':
            while arg_idx < len(args):
                if is_rel:
                    cy += args[arg_idx]
                else:
                    cy = args[arg_idx]
                points.append((cx, cy))
                arg_idx += 1

        elif cmd_up == 'C':
            while arg_idx + 5 < len(args):
                c1x, c1y = args[arg_idx], args[arg_idx+1]
                c2x, c2y = args[arg_idx+2], args[arg_idx+3]
                ex, ey = args[arg_idx+4], args[arg_idx+5]
                if is_rel:
                    ex += cx; ey += cy
                cx, cy = ex, ey
                points.append((cx, cy))
                arg_idx += 6

        elif cmd_up == 'S':
            while arg_idx + 3 < len(args):
                c2x, c2y = args[arg_idx], args[arg_idx+1]
                ex, ey = args[arg_idx+2], args[arg_idx+3]
                if is_rel:
                    ex += cx; ey += cy
                cx, cy = ex, ey
                points.append((cx, cy))
                arg_idx += 4

        elif cmd_up == 'Q':
            while arg_idx + 3 < len(args):
                ex, ey = args[arg_idx+2], args[arg_idx+3]
                if is_rel:
                    ex += cx; ey += cy
                cx, cy = ex, ey
                points.append((cx, cy))
                arg_idx += 4

        elif cmd_up == 'T':
            while arg_idx + 1 < len(args):
                ex, ey = args[arg_idx], args[arg_idx+1]
                if is_rel:
                    ex += cx; ey += cy
                cx, cy = ex, ey
                points.append((cx, cy))
                arg_idx += 2

        elif cmd_up == 'A':
            while arg_idx + 6 < len(args):
                rx, ry, rot = args[arg_idx], args[arg_idx+1], args[arg_idx+2]
                large, sweep = args[arg_idx+3], args[arg_idx+4]
                ex, ey = args[arg_idx+5], args[arg_idx+6]
                if is_rel:
                    ex += cx; ey += cy
                cx, cy = ex, ey
                points.append((cx, cy))
                arg_idx += 7

        # Z/z — 回到起点，不添加新点

    if not points:
        return None
    return points


def compute_bbox(d):
    """从 path d 字符串计算包围盒 (min_x, min_y, max_x, max_y)"""
    points = parse_path_d(d)
    if not points:
        return None
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


# ═══════════════════════════════════════════
#   行范围提取
# ═══════════════════════════════════════════

def extract_lines(filepath, ranges):
    """
    从文件中按行范围提取文本。
    ranges: [(start, end), ...] 1-indexed，包含两端。
    返回合并后的字符串。
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    parts = []
    for start, end in ranges:
        if start < 1:
            start = 1
        if end > len(lines):
            end = len(lines)
        parts.append(''.join(lines[start-1:end]))
    return '\n'.join(parts)

# ═══════════════════════════════════════════
#   渐变收集
# ═══════════════════════════════════════════

def collect_refs_from_xml(element, refs=None):
    """收集元素及其子元素中所有 url(#...) 引用"""
    if refs is None:
        refs = set()

    text = ET.tostring(element, encoding='unicode')
    for m in re.finditer(r'url\(#([^)]+)\)', text):
        refs.add(m.group(1))

    href = element.get(f'{{{XLINK_NS}}}href', '') or element.get('href', '')
    if href and href.startswith('#'):
        refs.add(href[1:])

    for child in element:
        collect_refs_from_xml(child, refs)

    return refs


def extract_defs_from_source(root, refs):
    """从源 SVG 的 defs 中提取引用的渐变定义，返回 XML 字符串列表"""
    defs_elem = root.find(f'{{{SVG_NS}}}defs')
    if defs_elem is None:
        return []

    extracted = []
    for elem in defs_elem:
        elem_id = elem.get('id')
        if elem_id in refs:
            extracted.append(elem)
            # 检查 xlink:href 链
            href = elem.get(f'{{{XLINK_NS}}}href', '') or elem.get('href', '')
            if href and href.startswith('#'):
                orig_id = href[1:]
                if orig_id not in refs:
                    refs.add(orig_id)
                # 确保基定义也被提取（即使 refs 中已有，也可能尚未加入 extracted）
                already = any(e.get('id') == orig_id for e in extracted)
                if not already:
                    for orig in defs_elem:
                        if orig.get('id') == orig_id:
                            extracted.insert(0, orig)
                            break
    return extracted


# ═══════════════════════════════════════════
#   元素序列化
# ═══════════════════════════════════════════

def serialize_element(elem, indent='  '):
    """将 XML 元素序列化为字符串"""
    tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
    attrs = []
    for attr, val in elem.attrib.items():
        attr_name = attr.split('}')[-1] if '}' in attr else attr
        attrs.append(f'{attr_name}="{val}"')
    attrs_str = ' '.join(attrs)

    if len(elem) == 0 and (elem.text is None or elem.text.strip() == ''):
        return f'{indent}<{tag} {attrs_str}/>'
    elif len(elem) == 0:
        return f'{indent}<{tag} {attrs_str}>{elem.text}</{tag}>'

    lines = [f'{indent}<{tag} {attrs_str}>']
    if elem.text and elem.text.strip():
        lines.append(elem.text)
    for child in elem:
        lines.append(serialize_element(child, indent + '  '))
    lines.append(f'{indent}</{tag}>')
    return '\n'.join(lines)


def serialize_defs(defs_elems):
    """将 defs 元素列表序列化为字符串"""
    lines = []
    for elem in defs_elems:
        lines.append(serialize_element(elem, '    '))
    return '\n'.join(lines)


# ═══════════════════════════════════════════
#   边缘发光变换
# ═══════════════════════════════════════════

def apply_edge_glow(state_name, state_group, edge_color, edge_width):
    """
    对状态组中的 _1 层应用边缘发光变换。
    - state_group: XML Element (对应 <g data-name="按钮选中">)
    - edge_color: 边缘色
    - edge_width: 边缘总宽度（px）
    """
    # 传入的 state_group 就是 _1 层元素，直接用
    layer1 = state_group

    # 找到 layer1 中的 path
    path_elem = None
    for elem in layer1.iter():
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        if tag == 'path':
            path_elem = elem
            break

    if path_elem is None:
        print(f"  警告: {state_name} 的 _1 层未找到 path 元素")
        return None

    d = path_elem.get('d', '')
    if not d:
        return None

    # 计算包围盒
    bbox = compute_bbox(d)
    if bbox is None:
        return None

    min_x, min_y, max_x, max_y = bbox
    w = max_x - min_x
    h = max_y - min_y

    if w <= 0 or h <= 0:
        return None

    # 获取主色
    style = path_elem.get('style', '')
    fill_match = re.search(r'fill:\s*([^;]+)', style)
    main_color = fill_match.group(1) if fill_match else path_elem.get('fill', '#000000')

    # 生成唯一 ID
    safe_state = re.sub(r'[\s_-]+', '_', state_name)
    clip_id = f'clip_{safe_state}'
    grad_left_id = f'edge_grad_left_{safe_state}'
    grad_right_id = f'edge_grad_right_{safe_state}'

    # 构建替换结构
    # 1. clipPath 定义（使用原始 path）
    clip_path = ET.SubElement(ET.Element('temp'), f'{{{SVG_NS}}}clipPath')
    clip_path.set('id', clip_id)
    clip_path_elem = ET.SubElement(clip_path, f'{{{SVG_NS}}}path')
    clip_path_elem.set('d', d)

    # 2. 渐变定义
    left_grad = ET.SubElement(ET.Element('temp'), f'{{{SVG_NS}}}linearGradient')
    left_grad.set('id', grad_left_id)
    left_grad.set('x1', '0%')
    left_grad.set('y1', '0%')
    left_grad.set('x2', '100%')
    left_grad.set('y2', '0%')
    s1 = ET.SubElement(left_grad, f'{{{SVG_NS}}}stop')
    s1.set('offset', '0%')
    s1.set('stop-color', edge_color)
    s2 = ET.SubElement(left_grad, f'{{{SVG_NS}}}stop')
    s2.set('offset', '50%')
    s2.set('stop-color', edge_color)
    s3 = ET.SubElement(left_grad, f'{{{SVG_NS}}}stop')
    s3.set('offset', '100%')
    s3.set('stop-color', edge_color)
    s3.set('stop-opacity', '0')

    right_grad = ET.SubElement(ET.Element('temp'), f'{{{SVG_NS}}}linearGradient')
    right_grad.set('id', grad_right_id)
    right_grad.set('x1', '0%')
    right_grad.set('y1', '0%')
    right_grad.set('x2', '100%')
    right_grad.set('y2', '0%')
    s1r = ET.SubElement(right_grad, f'{{{SVG_NS}}}stop')
    s1r.set('offset', '0%')
    s1r.set('stop-color', edge_color)
    s1r.set('stop-opacity', '0')
    s2r = ET.SubElement(right_grad, f'{{{SVG_NS}}}stop')
    s2r.set('offset', '50%')
    s2r.set('stop-color', edge_color)
    s3r = ET.SubElement(right_grad, f'{{{SVG_NS}}}stop')
    s3r.set('offset', '100%')
    s3r.set('stop-color', edge_color)

    ew = min(edge_width, w / 2)  # 边缘宽度不超过半宽

    # 保存属性再清空
    saved_id = layer1.get('id', '')
    saved_data_name = layer1.get('data-name', f'{state_name} 1')

    # 3. 替换 layer1 的内容
    layer1.clear()
    if saved_id:
        layer1.set('id', saved_id)
    layer1.set('data-name', saved_data_name)

    # 用 g 包裹
    inner_g = ET.SubElement(layer1, f'{{{SVG_NS}}}g')
    inner_g.set('clip-path', f'url(#{clip_id})')

    # 底层：全宽主色
    full_rect = ET.SubElement(inner_g, f'{{{SVG_NS}}}rect')
    full_rect.set('x', f'{min_x:.3f}')
    full_rect.set('y', f'{min_y:.3f}')
    full_rect.set('width', f'{w:.3f}')
    full_rect.set('height', f'{h:.3f}')
    full_rect.set('fill', main_color)

    # 左侧边缘渐变矩形
    left_rect = ET.SubElement(inner_g, f'{{{SVG_NS}}}rect')
    left_rect.set('x', f'{min_x:.3f}')
    left_rect.set('y', f'{min_y:.3f}')
    left_rect.set('width', f'{ew:.3f}')
    left_rect.set('height', f'{h:.3f}')
    left_rect.set('fill', f'url(#{grad_left_id})')

    # 右侧边缘渐变矩形
    right_rect = ET.SubElement(inner_g, f'{{{SVG_NS}}}rect')
    right_rect.set('x', f'{max_x - ew:.3f}')
    right_rect.set('y', f'{min_y:.3f}')
    right_rect.set('width', f'{ew:.3f}')
    right_rect.set('height', f'{h:.3f}')
    right_rect.set('fill', f'url(#{grad_right_id})')

    return {
        'defs': ([clip_path] + [left_grad] + [right_grad]),
        'main_color': main_color,
        'bbox': {'x': min_x, 'y': min_y, 'w': w, 'h': h},
    }


# ═══════════════════════════════════════════
#   状态分组
# ═══════════════════════════════════════════

def group_states(root_elem):
    """
    从解析后的组件 XML 中按状态分组。
    返回 {状态名: [子层 g 元素列表]}
    """
    state_map = defaultdict(list)

    # 如果第一层只有一个子 g，钻进去（处理含外层包装组的情况）
    elems = list(root_elem)
    if len(elems) == 1:
        tag = elems[0].tag.split('}')[-1] if '}' in elems[0].tag else elems[0].tag
        if tag == 'g':
            elems = list(elems[0])

    for elem in elems:
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        if tag != 'g':
            continue

        cname = elem.get('data-name', elem.get('id', ''))
        state_name = re.sub(r'\s+\d+$', '', cname)

        # 解开状态组的子层：状态组的直接子 <g> 才是实际层
        child_layers = []
        for child in elem:
            child_tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            if child_tag == 'g':
                child_layers.append(child)

        state_map[state_name].extend(child_layers if child_layers else [elem])

    return dict(state_map)


# ═══════════════════════════════════════════
#   主流程
# ═══════════════════════════════════════════

def process_layers_to_svg(state_name, layers, vb, source_defs_elems, edge_glow_data, output_dir, global_edge_width):
    """
    处理状态的所有层、应用边缘发光、生成 SVG 内容并写出文件。
    
    Args:
        state_name: 状态名称（如"按钮选中"）
        layers: 层元素列表
        vb: (vx, vy, vw, vh) viewBox
        source_defs_elems: 源文件提取的渐变元素列表
        edge_glow_data: 边缘发光配置 dict 或 None
        output_dir: 输出目录
        global_edge_width: 全局边缘宽度
    Returns:
        dict: {svg_content, defs_content, state_refs, layers_count} 或 None
    """
    # 收集该状态的渐变引用
    state_refs = set()
    for l in layers:
        collect_refs_from_xml(l, state_refs)

    # 解析href链
    expanded_refs = set(state_refs)
    for d in source_defs_elems:
        if d.get('id') in state_refs:
            href = d.get(f'{{{XLINK_NS}}}href', '') or d.get('href', '')
            if href and href.startswith('#'):
                expanded_refs.add(href[1:])

    state_defs = [d for d in source_defs_elems if d.get('id') in expanded_refs]
    extra_defs = []

    # 排序层
    def layer_sort_key(l):
        cname = l.get('data-name', l.get('id', ''))
        m = re.search(r'(\d+)$', cname)
        return int(m.group(1)) if m else 0
    layers_sorted = sorted(layers, key=layer_sort_key)

    # 对每层应用边缘发光
    processed_layers = []
    for layer in layers_sorted:
        lname = layer.get('data-name', layer.get('id', ''))
        lid = layer.get('id', '')

        is_layer1 = (
            bool(re.search(r'\s1$', lname)) or
            bool(re.search(r'_1-\d+', lid)) or
            bool(re.search(r'_1_\d', lid))
        )

        if is_layer1 and edge_glow_data:
            edge_color = edge_glow_data['edge_color']
            ew = edge_glow_data.get('edge_width', global_edge_width)

            print(f"    应用边缘发光: edge_color={edge_color}, width={ew}")

            result = apply_edge_glow(state_name, layer, edge_color, ew)
            if result:
                extra_defs.extend(result['defs'])
                processed_layers.append(layer)
                print(f"      bbox: ({result['bbox']['x']:.0f}, {result['bbox']['y']:.0f}) "
                      f"w={result['bbox']['w']:.0f} h={result['bbox']['h']:.0f}")
                print(f"      main_color: {result['main_color']}")
            else:
                print(f"     边缘发光应用失败，保留原始层")
                processed_layers.append(layer)
        else:
            processed_layers.append(layer)

    # 序列化层内容
    content_parts = []
    for layer in processed_layers:
        content_parts.append(serialize_element(layer, '  '))

    # 序列化 defs
    defs_parts = []
    if state_defs:
        defs_parts.append(serialize_defs(state_defs))
    if extra_defs:
        defs_parts.append(serialize_defs(extra_defs))
    # 如果基 pattern 在 state_defs 中但其内部的渐变不在，注入完整硬编码块替换
    has_base_pattern = any(d.get('id', '').endswith('_基') for d in state_defs)
    has_texture_grads = any(d.get('id') in ('_新建渐变色板_12', '_未命名的渐变_765', '_新建渐变色板_11', '_未命名的渐变_812') for d in (state_defs or []))
    if has_base_pattern and not has_texture_grads:
        # 移除已提取的不完整的基 pattern（仅匹配 id 以 _基 结尾的 pattern，不影响 href 引用 _基 的实例 pattern）
        new_parts = []
        for d in state_defs:
            if not d.get('id', '').endswith('_基'):
                new_parts.append(serialize_element(d, ''))
        new_parts.append(TEXTURE_BASE_PATTERN)
        if extra_defs:
            new_parts.append(serialize_defs(extra_defs))
        defs_parts = new_parts
    defs_xml = '\n'.join(defs_parts) if defs_parts else ''

    # 生成 SVG
    vbx, vby, vbw, vbh = vb

    # 用 <g transform> 包裹所有内容来平移坐标，而非修改坐标值本身
    # 这样 userSpaceOnUse 渐变保持正确
    content_transformed = ''.join(content_parts)
    # 缩进包装
    wrapped_content = '\n'.join(f'  {line}' for line in content_transformed.strip().split('\n'))

    # 带 transform 的内容组（供复合SVG使用）
    content_group = f'<g transform="translate({-vbx:.3f}, {-vby:.3f})">\n{wrapped_content}\n</g>'

    svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     viewBox="0 0 {vbw} {vbh}" width="{vbw}" height="{vbh}">
  <defs>
{defs_xml}
  </defs>
{content_group}
</svg>
'''

    # 写出
    safe_name = re.sub(r'[*<>:"/\\|?]', '_', state_name)
    out_filename = f'{safe_name}.svg'
    out_path = os.path.join(output_dir, out_filename)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    print(f'  ✓ {out_filename}')

    return {
        'svg_content': svg_content,
        'defs_xml': defs_xml,
        'all_extra_xml': serialize_defs(extra_defs) if extra_defs else '',
        'wrapped_content': wrapped_content,
        'content_group': content_group,
        'state_refs': list(state_refs),
        'layers_count': len(layers),
        'filename': out_filename,
    }


def extract_svg_lines(filepath, ranges):
    """提取行范围并解析为 ElementTree，返回 root element"""
    raw_xml = extract_lines(filepath, ranges)
    if not raw_xml.strip():
        return None
    raw_xml = re.sub(r'</svg>\s*$', '', raw_xml.strip())
    raw_xml = re.sub(r'^<svg[^>]*>', '', raw_xml)
    fragment = f'<root xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">{raw_xml}</root>'
    try:
        return ET.fromstring(fragment)
    except ET.ParseError as e:
        print(f"  ✗ XML 解析失败: {e}")
        return None


def _parse_path_coords(d, x_vals, y_vals):
    """解析 SVG path d 属性，提取所有坐标到 x_vals/y_vals 中"""
    # 匹配命令字母+数字参数
    pattern = re.compile(r'([MLHVCHVmlhvchv])\s*([-\d\s.,eE]+?)(?=[MLHVCHVmlhvchv]|$)')
    cur_x = cur_y = 0.0
    first_x = first_y = 0.0  # 用于 Z/z 闭合
    for match in pattern.finditer(d):
        cmd = match.group(1)
        nums = [float(x) for x in re.findall(r'-?\d*\.?\d+(?:[eE][+-]?\d+)?', match.group(2))]
        if not nums:
            continue
        if cmd == 'M':
            cur_x, cur_y = nums[0], nums[1]
            first_x, first_y = cur_x, cur_y
            x_vals.append(cur_x); y_vals.append(cur_y)
            # M 后的多余坐标视为隐式 L
            for i in range(2, len(nums), 2):
                cur_x, cur_y = nums[i], nums[i+1]
                x_vals.append(cur_x); y_vals.append(cur_y)
        elif cmd == 'm':
            cur_x += nums[0]; cur_y += nums[1]
            first_x, first_y = cur_x, cur_y
            x_vals.append(cur_x); y_vals.append(cur_y)
            for i in range(2, len(nums), 2):
                cur_x += nums[i]; cur_y += nums[i+1]
                x_vals.append(cur_x); y_vals.append(cur_y)
        elif cmd == 'L':
            for i in range(0, len(nums), 2):
                cur_x, cur_y = nums[i], nums[i+1]
                x_vals.append(cur_x); y_vals.append(cur_y)
        elif cmd == 'l':
            for i in range(0, len(nums), 2):
                cur_x += nums[i]; cur_y += nums[i+1]
                x_vals.append(cur_x); y_vals.append(cur_y)
        elif cmd == 'H':
            for x in nums:
                cur_x = x; x_vals.append(cur_x)
        elif cmd == 'h':
            for x in nums:
                cur_x += x; x_vals.append(cur_x)
        elif cmd == 'V':
            for y in nums:
                cur_y = y; y_vals.append(cur_y)
        elif cmd == 'v':
            for y in nums:
                cur_y += y; y_vals.append(cur_y)
        elif cmd == 'C':  # 绝对三次贝塞尔
            for i in range(0, len(nums), 6):
                x_vals.extend([nums[i], nums[i+2], nums[i+4]])
                y_vals.extend([nums[i+1], nums[i+3], nums[i+5]])
                cur_x, cur_y = nums[i+4], nums[i+5]
        elif cmd == 'c':  # 相对三次贝塞尔
            for i in range(0, len(nums), 6):
                x_vals.extend([cur_x+nums[i], cur_x+nums[i+2], cur_x+nums[i+4]])
                y_vals.extend([cur_y+nums[i+1], cur_y+nums[i+3], cur_y+nums[i+5]])
                cur_x += nums[i+4]; cur_y += nums[i+5]
        elif cmd == 'S':  # 绝对平滑三次贝塞尔
            for i in range(0, len(nums), 4):
                x_vals.extend([nums[i], nums[i+2]])
                y_vals.extend([nums[i+1], nums[i+3]])
                cur_x, cur_y = nums[i+2], nums[i+3]
        elif cmd == 's':  # 相对平滑三次贝塞尔
            for i in range(0, len(nums), 4):
                x_vals.extend([cur_x+nums[i], cur_x+nums[i+2]])
                y_vals.extend([cur_y+nums[i+1], cur_y+nums[i+3]])
                cur_x += nums[i+2]; cur_y += nums[i+3]
        elif cmd in ('Z', 'z'):
            cur_x, cur_y = first_x, first_y


def compute_bbox_from_elements_flat(elements, padding=8):
    """
    从 XML 元素列表（含递归子元素）计算包围盒。
    elements: ElementTree 元素列表
    padding: 各边额外余量
    返回 [min_x, min_y, width, height] 或 None
    """
    x_vals, y_vals = [], []

    def walk(elem):
        tag = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
        if tag == 'rect':
            x = float(elem.get('x', 0))
            y = float(elem.get('y', 0))
            w = float(elem.get('width', 0))
            h = float(elem.get('height', 0))
            x_vals.extend([x, x + w])
            y_vals.extend([y, y + h])
        elif tag == 'line':
            x_vals.append(float(elem.get('x1', 0)))
            y_vals.append(float(elem.get('y1', 0)))
            x_vals.append(float(elem.get('x2', 0)))
            y_vals.append(float(elem.get('y2', 0)))
        elif tag == 'polyline':
            pts = elem.get('points', '')
            for coord in re.findall(r'([\d.]+)\s*,?\s*([\d.]+)', pts):
                x_vals.append(float(coord[0]))
                y_vals.append(float(coord[1]))
        elif tag == 'path':
            _parse_path_coords(elem.get('d', ''), x_vals, y_vals)
        elif tag == 'circle':
            cx = float(elem.get('cx', 0))
            cy = float(elem.get('cy', 0))
            r = float(elem.get('r', 0))
            x_vals.extend([cx - r, cx + r])
            y_vals.extend([cy - r, cy + r])
        elif tag == 'ellipse':
            cx = float(elem.get('cx', 0))
            cy = float(elem.get('cy', 0))
            rx = float(elem.get('rx', 0))
            ry = float(elem.get('ry', 0))
            x_vals.extend([cx - rx, cx + rx])
            y_vals.extend([cy - ry, cy + ry])
        # 递归子元素
        for child in elem:
            walk(child)

    for e in elements:
        walk(e)

    if not x_vals or not y_vals:
        return None

    min_x, max_x = min(x_vals), max(x_vals)
    min_y, max_y = min(y_vals), max(y_vals)
    min_x -= padding
    min_y -= padding
    max_x += padding
    max_y += padding
    return [min_x, min_y, max_x - min_x, max_y - min_y]


def extract_sub_component(sc, source_path, output_dir, config_vb, source_defs_elems, global_edge_width):
    """
    处理单个子组件（sub_component）。
    sc: 子组件配置 dict（含 name, ranges, edge_glow）
    """
    name = sc['name']
    ranges = sc['ranges']
    edge_glow = sc.get('edge_glow')

    print(f"\n  子组件: {name} (ranges: {ranges})")

    root = extract_svg_lines(source_path, ranges)
    if root is None:
        return None

    # 自动计算包围盒，替代手动配置的 viewBox
    auto_vb = compute_bbox_from_elements_flat([root], padding=8)
    if auto_vb:
        vb = auto_vb
        print(f"    自动 bbox: [{vb[0]:.0f}, {vb[1]:.0f}, {vb[2]:.0f}, {vb[3]:.0f}]")
    else:
        vb = config_vb
        print(f"    使用配置 viewBox: {vb}")

    # 获取该状态的所有子层
    # 检测根的直接子 <g> 中是否有 _1 层（data-name 以" 1"结尾，或 id 含 _1-/ _1_）
    direct_children_have_layer1 = False
    for child in root:
        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
        if tag == 'g':
            cname = child.get('data-name', child.get('id', ''))
            cid = child.get('id', '')
            if (re.search(r'\s1$', cname) or
                re.search(r'_1-\d+', cid) or
                re.search(r'_1_\d', cid)):
                direct_children_have_layer1 = True
                break

    layers = []
    for child in root:
        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
        if tag == 'g':
            if direct_children_have_layer1:
                # 直接子 <g> 本身就是层（如 界面 0/1/2），保留以传递 data-name/id 给 _1 检测
                layers.append(child)
            else:
                # 传统行为：展平子元素作为层（如按钮的 外框/1 层在包装器内部）
                child_layers = list(child)
                if child_layers:
                    layers.extend(child_layers)
                else:
                    layers.append(child)
        else:
            # 非 <g> 元素（如裸 <path>）也作为层
            layers.append(child)

    if not layers:
        layers = list(root)

    result = process_layers_to_svg(name, layers, vb, source_defs_elems,
                                    edge_glow, output_dir, global_edge_width)
    if result:
        result['name'] = name
    return result


def extract_component(comp_config, source_path, output_base, global_edge_width):
    """
    提取并处理单个组件。
    支持两种模式：
      - sub_components: 子对象独立提取，根对象创建复合SVG
      - ranges: 简单行范围提取（原有流程）
    """
    comp_id = comp_config.get('id', '')
    comp_name = comp_config.get('name', comp_id)
    vb = comp_config['viewBox']
    edge_glow_cfg = comp_config.get('edge_glow', {})

    safe_name = comp_name.replace(' ', '_').replace('/', '_')
    out_dir = os.path.join(output_base, safe_name)
    os.makedirs(out_dir, exist_ok=True)

    print(f"\n{'='*50}")
    print(f"提取组件: {comp_name} ({comp_id})")
    print(f"  viewBox: {vb}")
    print(f"  输出: {out_dir}")

    # 读取源 SVG 的 defs
    full_svg_path = os.path.join(CINDER_BASE, 'SourceCode 源代码', '005-矢量图', '005-无样式.svg')
    source_defs_elems = []
    all_refs = set()
    if os.path.exists(full_svg_path):
        try:
            full_tree = ET.parse(full_svg_path)
            full_root = full_tree.getroot()
        except Exception as e:
            print(f"  警告: 无法读取源 SVG: {e}")
            full_root = None
    else:
        full_root = None

    metadata = {
        'source': os.path.basename(full_svg_path) if os.path.exists(full_svg_path) else '005-无样式.svg',
        'component': comp_name,
        'viewBox': vb,
        'mode': 'sub_components' if 'sub_components' in comp_config else 'simple',
        'states': [],
    }

    # ── 模式1: sub_components ──
    if 'sub_components' in comp_config:
        print("  模式: sub_components")
        sub_results = []

        # 先收集所有子组件的 refs，统一提取渐变定义
        all_refs = set()
        for sc in comp_config['sub_components']:
            root = extract_svg_lines(source_path, sc['ranges'])
            if root is not None:
                for child in root:
                    collect_refs_from_xml(child, all_refs)

        if full_root:
            source_defs_elems = extract_defs_from_source(full_root, all_refs)
            print(f"  渐变定义: {len(source_defs_elems)}")

        for sc in comp_config['sub_components']:
            result = extract_sub_component(sc, source_path, out_dir, vb,
                                            source_defs_elems, global_edge_width)
            if result:
                sub_results.append(result)
                metadata['states'].append({
                    'name': result['name'],
                    'refs': result['state_refs'],
                    'layers': result['layers_count'],
                    'edge_glow': sc.get('edge_glow') is not None,
                })
                all_refs.update(result['state_refs'])

        # 生成复合SVG
        if sub_results:
            n = len(sub_results)
            _, _, comp_w, comp_h = vb
            # 完全覆盖堆叠（展示对齐）
            total_h = comp_h

            # 合并所有子组件 defs（源渐变 + 边缘发光），按 id 去重
            seen_def_ids = set()
            all_def_blocks = []

            # 1. 源渐变 defs
            if full_root:
                source_defs_elems = extract_defs_from_source(full_root, all_refs)
                for d in source_defs_elems:
                    block = serialize_element(d, '    ')
                    id_m = re.search(r'id="([^"]+)"', block)
                    if id_m and id_m.group(1) not in seen_def_ids:
                        seen_def_ids.add(id_m.group(1))
                        all_def_blocks.append(block)

            # 2. 额外 defs（边缘发光产生的 clipPath 和渐变）
            for sr in sub_results:
                extra_raw = sr.get('all_extra_xml', '')
                if not extra_raw:
                    continue
                # 用正则按完整标签拆分
                for tag_match in re.finditer(r'<(linearGradient|clipPath)[^>]*>.*?</\1>', extra_raw, re.DOTALL):
                    block = tag_match.group(0)
                    id_m = re.search(r'id="([^"]+)"', block)
                    if id_m and id_m.group(1) not in seen_def_ids:
                        seen_def_ids.add(id_m.group(1))
                        all_def_blocks.append(block)

            # 检查是否需要注入纹理基 pattern 的完整定义（含内联渐变）
            all_defs_str = '\n'.join(all_def_blocks)
            has_texture_base = bool(re.search(r'<pattern[^>]*id="[^"]*_基"', all_defs_str))
            has_texture_grads = 'linearGradient id="_新建渐变色板_12"' in all_defs_str
            if has_texture_base and not has_texture_grads:
                # 移除不完整的基 pattern
                all_def_blocks = [s for s in all_def_blocks if not re.search(r'<pattern[^>]*id="[^"]*_基"', s)]
                # 注入完整硬编码块（渐变 + 基 pattern）
                for bl in TEXTURE_BASE_PATTERN.split('\n'):
                    stripped = bl.strip()
                    if stripped:
                        all_def_blocks.append(stripped)
                all_defs_str = '\n'.join(all_def_blocks)

            composite_parts = [
                f'<?xml version="1.0" encoding="UTF-8"?>',
                f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"',
                f'     viewBox="0 0 {comp_w} {total_h}" width="{comp_w}" height="{total_h}">',
                f'  <defs>',
                all_defs_str,
                f'  </defs>',
            ]

            vx, vy, vw, vh = vb
            composite_parts.append(f'  <g transform="translate({-vx:.3f}, {-vy:.3f})">')
            for i, sr in enumerate(sub_results):
                # 完全覆盖堆叠——使用无 transform 的裸内容+统一的 config viewBox 平移
                for line in sr['wrapped_content'].split('\n'):
                    composite_parts.append(f'    {line}')
                composite_parts.append('')
            composite_parts.append('  </g>')
            composite_parts.append('</svg>')

            composite_svg = '\n'.join(composite_parts)
            comp_path = os.path.join(out_dir, f'{safe_name}_composite.svg')
            os.makedirs(os.path.dirname(comp_path), exist_ok=True)
            with open(comp_path, 'w', encoding='utf-8') as f:
                f.write(composite_svg)
            print(f'  ✓ {safe_name}_composite.svg (复合SVG, {n} 个子组件)')

        # 元数据
        meta_path = os.path.join(out_dir, 'metadata.json')
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        print(f'  ✓ metadata.json')
        return metadata

    # ── 模式2: ranges（简单提取，原有流程） ──
    if 'ranges' not in comp_config:
        print(f"  错误: 组件缺少 ranges 或 sub_components")
        return None

    ranges = comp_config['ranges']
    print(f"  模式: simple (ranges: {ranges})")

    # 提取并解析
    root = extract_svg_lines(source_path, ranges)
    if root is None:
        return None

    # 自动计算包围盒
    auto_vb = compute_bbox_from_elements_flat([root], padding=8)
    if auto_vb:
        vb = auto_vb
        print(f"    自动 bbox: [{vb[0]:.0f}, {vb[1]:.0f}, {vb[2]:.0f}, {vb[3]:.0f}]")
    else:
        print(f"    使用配置 viewBox: {vb}")

    # 状态分组
    state_groups = group_states(root)
    print(f"  状态数: {len(state_groups)}")
    if not state_groups:
        print(f"  ✗ 未识别到状态组")
        return None

    # 收集所有 refs
    for state_name, layers in state_groups.items():
        for l in layers:
            collect_refs_from_xml(l, all_refs)

    if full_root:
        source_defs_elems = extract_defs_from_source(full_root, all_refs)
    print(f"  渐变定义: {len(source_defs_elems)}")

    # 处理每个状态
    simple_svgs = {}
    simple_extra_defs = []
    for state_name, layers in state_groups.items():
        print(f"\n  处理状态: {state_name} ({len(layers)} 层)")
        edge_data = edge_glow_cfg.get(state_name) if edge_glow_cfg and 'edge_color' not in edge_glow_cfg else edge_glow_cfg

        result = process_layers_to_svg(state_name, layers, vb, source_defs_elems,
                                        edge_data, out_dir, global_edge_width)
        if result:
            metadata['states'].append({
                'name': state_name,
                'refs': result['state_refs'],
                'layers': result['layers_count'],
                'edge_glow': edge_data is not None,
            })
            simple_svgs[state_name] = result['wrapped_content']
            if result.get('all_extra_xml'):
                simple_extra_defs.append(result['all_extra_xml'])

    # ── simple 模式复合 SVG ──
    vx, vy, vw, vh = vb
    composite_parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"',
        f'     viewBox="0 0 {vw:.1f} {vh:.1f}" width="{vw:.1f}" height="{vh:.1f}">',
    ]
    # 合并 defs（源渐变 + 边缘发光 defs）
    all_composite_defs = []
    for d in source_defs_elems:
        d_str = serialize_element(d, '')
        if d_str.strip():
            all_composite_defs.append(d_str)
    for extra_xml in simple_extra_defs:
        for line in extra_xml.split('\n'):
            line = line.strip()
            if line:
                all_composite_defs.append(line)
    # 检查是否需要注入纹理基 pattern 的完整定义（含内联渐变）
    has_texture_base = any('id="' in s and '_基"' in s and 'pattern' in s for s in all_composite_defs)
    has_texture_grads = any('linearGradient id="_新建渐变色板_12"' in s for s in all_composite_defs)
    if has_texture_base and not has_texture_grads:
        # 移除不完整的基 pattern（仅匹配 id 自身以 _基 结尾的 pattern，避免误删 href 引用 _基 的实例 pattern）
        all_composite_defs = [s for s in all_composite_defs if not re.search(r'<pattern[^>]*id="[^"]*_基"', s)]
        # 注入完整硬编码块（渐变 + 基 pattern）
        for bl in TEXTURE_BASE_PATTERN.split('\n'):
            stripped = bl.strip()
            if stripped:
                all_composite_defs.append(stripped)
    if all_composite_defs:
        composite_parts.append('  <defs>')
        for dl in all_composite_defs:
            composite_parts.append(f'    {dl}')
        composite_parts.append('  </defs>')

    composite_parts.append(f'  <g transform="translate({-vx:.3f}, {-vy:.3f})">')
    for sname, content in simple_svgs.items():
        for line in content.split('\n'):
            composite_parts.append(f'    {line}')
        composite_parts.append('')
    composite_parts.append('  </g>')
    composite_parts.append('</svg>')

    composite_svg = '\n'.join(composite_parts)
    comp_path = os.path.join(out_dir, f'{safe_name}_composite.svg')
    os.makedirs(os.path.dirname(comp_path), exist_ok=True)
    with open(comp_path, 'w', encoding='utf-8') as f:
        f.write(composite_svg)
    print(f'  ✓ {safe_name}_composite.svg (复合SVG, {len(simple_svgs)} 个状态)')

    # 元数据
    meta_path = os.path.join(out_dir, 'metadata.json')
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f'  ✓ metadata.json')

    return metadata


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='从 005-无样式.svg 提取 UI 组件（支持边缘发光效果）')
    parser.add_argument('--config',
                        default='extracted/extract_config.json',
                        help='配置文件路径（相对于 CinderUI 目录）')
    parser.add_argument('--component', help='只处理指定组件 ID')

    args = parser.parse_args()

    # 加载配置
    config_path = os.path.join(CINDER_BASE, args.config.replace('\\', '/'))
    if not os.path.exists(config_path):
        print(f"错误: 配置文件不存在: {config_path}")
        sys.exit(1)

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    print("CinderUI — 组件提取器 (支持边缘发光)")
    print(f"配置: {config_path}")

    source_rel = config.get('source', 'SourceCode 源代码/005-矢量图/005-无样式.svg')
    source_path = os.path.join(CINDER_BASE, source_rel.replace('\\', '/'))

    if not os.path.exists(source_path):
        print(f"错误: 源 SVG 不存在: {source_path}")
        sys.exit(1)

    output_base = os.path.join(CINDER_BASE, config.get('output_base', 'extracted'))
    global_edge_width = config.get('edge_width_px', 8)

    components = config.get('components', [])
    print(f"组件数: {len(components)}")
    print(f"源文件: {source_path}")
    print(f"输出目录: {output_base}")

    for comp in components:
        if args.component and comp['id'] != args.component:
            continue

        extract_component(comp, source_path, output_base, global_edge_width)

    print(f"\n{'='*50}")
    print("完成！")

if __name__ == '__main__':
    main()
