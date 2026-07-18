#!/usr/bin/env python3
"""
CinderUI — CozyUI+ PSD 全自动提取器

从 005.psd 提取所有矢量形状，含颜色/渐变/阴影，按复合组件输出。

用法:
    python tools/extract.py

输出:
    extracted/svg/{full_path}.svg       — 带颜色的独立 SVG
    extracted/json/{full_path}.json     — 结构化元数据
    extracted/composites/{group}/       — 复合组件索引
    extracted/parameters.json           — 转角参数汇总
"""

import struct, json, os
from psd_tools import PSDImage
from psd_tools.api.layers import ShapeLayer

PSD_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                        'SourceCode 源代码', '005.psd')
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'extracted')
SVG_DIR = os.path.join(OUT_DIR, 'svg')
JSON_DIR = os.path.join(OUT_DIR, 'json')
COMPOSITE_DIR = os.path.join(OUT_DIR, 'composites')


# ═══════════════════════════════════════════
#   PSD 矢量路径解析
# ═══════════════════════════════════════════

def is_vector(layer):
    return isinstance(layer, ShapeLayer) or \
           (hasattr(layer, 'has_vector_mask') and layer.has_vector_mask())


def parse_knots(layer):
    if not hasattr(layer, 'vector_mask') or not layer.vector_mask:
        return []
    vm = layer.vector_mask
    data = vm._data
    raw = None
    if hasattr(data, 'path') and hasattr(data.path, 'tobytes'):
        raw = data.path.tobytes()
    if raw is None and hasattr(data, 'tobytes'):
        raw = data.tobytes()
    if not raw:
        return []
    knots = []
    offset = 0
    while offset + 26 <= len(raw):
        sel = struct.unpack('>H', raw[offset:offset+2])[0]
        if sel in (1, 2, 4, 5):
            vals = struct.unpack('>iiiiii', raw[offset+2:offset+26])
            knots.append({
                'before': {'x': vals[0]/256.0, 'y': vals[1]/256.0},
                'anchor': {'x': vals[2]/256.0, 'y': vals[3]/256.0},
                'after':  {'x': vals[4]/256.0, 'y': vals[5]/256.0},
            })
        offset += 26
    return knots


def knots_to_pixel(knots, bbox_px):
    if not knots:
        return []
    all_x = [k['before']['x'] for k in knots] + [k['after']['x'] for k in knots]
    all_y = [k['before']['y'] for k in knots] + [k['after']['y'] for k in knots]
    all_x += [k['anchor']['x'] for k in knots]
    all_y += [k['anchor']['y'] for k in knots]
    vmin_x, vmax_x = min(all_x), max(all_x)
    vmin_y, vmax_y = min(all_y), max(all_y)
    vw, vh = vmax_x - vmin_x, vmax_y - vmin_y
    pw, ph = bbox_px[2], bbox_px[3]
    if vw == 0 or vh == 0:
        return []
    return [{
        'before': {'x': round((k['before']['x'] - vmin_x) / vw * pw, 3),
                   'y': round((k['before']['y'] - vmin_y) / vh * ph, 3)},
        'anchor': {'x': round((k['anchor']['x'] - vmin_x) / vw * pw, 3),
                   'y': round((k['anchor']['y'] - vmin_y) / vh * ph, 3)},
        'after':  {'x': round((k['after']['x'] - vmin_x) / vw * pw, 3),
                   'y': round((k['after']['y'] - vmin_y) / vh * ph, 3)},
    } for k in knots]


def classify(kc):
    return {8: 'rounded_rect', 6: 'pill', 4: 'rect'}.get(kc, f'{kc}_knot')


# ═══════════════════════════════════════════
#   颜色 / 效果提取
# ═══════════════════════════════════════════

def extract_color_from_clr(clr_dict):
    r = float(clr_dict.get(b'Rd  ', 0))
    g = float(clr_dict.get(b'Grn ', 0))
    b = float(clr_dict.get(b'Bl  ', 0))
    if r == 0 and g == 0 and b == 0:
        r = float(clr_dict.get(b'redFloat', 0)) * 255
        g = float(clr_dict.get(b'greenFloat', 0)) * 255
        b = float(clr_dict.get(b'blueFloat', 0)) * 255
    return f'rgb({int(round(r))},{int(round(g))},{int(round(b))})'


def extract_gradient(grad_dict):
    colors = []
    for c in grad_dict.get(b'Clrs', []):
        if b'Clr ' in c:
            rgb = extract_color_from_clr(c[b'Clr '])
            pos = int(c.get(b'Lctn', 0)) / 4096.0
            colors.append({'rgb': rgb, 'position': round(pos, 3)})
    return {
        'colors': colors,
        'angle': float(grad_dict.get(b'Angl', 90)),
    }


def extract_layer_style(layer):
    result = {'fill': None, 'gradient': None, 'inner_shadow': None}
    tb = layer.tagged_blocks
    if not tb:
        return result

    for key in tb.keys():
        if b'vscg' in key:
            data = tb[key].data
            if hasattr(data, 'items') and b'Clr ' in data:
                result['fill'] = extract_color_from_clr(data[b'Clr '])

    for key in tb.keys():
        if b'lfx2' in key:
            data = tb[key].data
            if not hasattr(data, 'items'):
                continue
            if b'solidFill' in data:
                sf = data[b'solidFill']
                if sf.get(b'enab', False) and b'Clr ' in sf:
                    result['fill'] = extract_color_from_clr(sf[b'Clr '])
            if b'FrFX' in data:
                fx = data[b'FrFX']
                if fx.get(b'enab', False) and b'Grad' in fx:
                    result['gradient'] = extract_gradient(fx[b'Grad'])
            if b'IrSh' in data:
                irsh = data[b'IrSh']
                if irsh.get(b'enab', False):
                    shadow = {
                        'opacity': float(irsh.get(b'Opct', 0)),
                        'angle': float(irsh.get(b'lagl', 0)),
                        'distance': float(irsh.get(b'Dstn', 0)),
                        'choke': float(irsh.get(b'Ckmt', 0)),
                        'size': float(irsh.get(b'blur', 0)),
                    }
                    if b'Clr ' in irsh:
                        shadow['color'] = extract_color_from_clr(irsh[b'Clr '])
                    result['inner_shadow'] = shadow
    return result


# ═══════════════════════════════════════════
#   转角参数
# ═══════════════════════════════════════════

def extract_corner_params(knots):
    if len(knots) != 8:
        return None
    xs = [k['anchor']['x'] for k in knots]
    ys = [k['anchor']['y'] for k in knots]
    vmin_x, vmax_x = min(xs), max(xs)
    vmin_y, vmax_y = min(ys), max(ys)
    kw, kh = vmax_x - vmin_x, vmax_y - vmin_y
    if kw == 0 or kh == 0:
        return None
    an = [((k['anchor']['x'] - vmin_x) / kw, (k['anchor']['y'] - vmin_y) / kh) for k in knots]
    left_ys = sorted([ny for nx, ny in an if nx < 0.01])
    top_xs = sorted([nx for nx, ny in an if ny < 0.01])
    if not left_ys or not top_xs:
        return None
    return {'t': round(min(left_ys), 4), 'c': round(min(top_xs), 4)}


# ═══════════════════════════════════════════
#   SVG 生成 + 6→8 节点升级
# ═══════════════════════════════════════════

def fix_pill_to_rounded(px_knots):
    """
    将 6 节点 Pill 升级为 8 节点圆角矩形。
    从直线段提取转角半径 rx，完全重新生成 8 节点。
    关键设计：直边段的控制点 ≡ 锚点（is_straight 自然为 True），
    转角曲线只由转角段的控制点驱动。
    """
    if len(px_knots) != 6:
        return px_knots

    # 计算包围盒
    xs = [k['anchor']['x'] for k in px_knots]
    ys = [k['anchor']['y'] for k in px_knots]
    w = max(xs) - min(xs)
    h = max(ys) - min(ys)
    if w == 0 or h == 0:
        return px_knots

    # 从水平直线段提取转角半径 rx
    rx = 0
    for i in range(6):
        prev, curr = px_knots[i-1], px_knots[i]
        if is_straight(prev, curr):
            dx = abs(curr['anchor']['x'] - prev['anchor']['x'])
            dy = abs(curr['anchor']['y'] - prev['anchor']['y'])
            if dx > 1 and dy < 1:  # 水平直线段
                rx = max(rx, dx)
    if rx == 0:
        return px_knots

    # rx 是顶部/底部平直段的长度
    # ry 由比例推导
    t = rx / w
    t = min(t, 0.49)
    ry = h * t
    k = 0.55  # cubic bezier arc approxim

    def knot(ax, ay):
        """生成锚点 = 控制点 ≡ 锚点的 knot（直边段控制点）"""
        return {
            'before': {'x': round(ax, 3), 'y': round(ay, 3)},
            'anchor': {'x': round(ax, 3), 'y': round(ay, 3)},
            'after':  {'x': round(ax, 3), 'y': round(ay, 3)},
        }

    def corner(ax, ay, cax, cay, cbx, cby):
        """生成转角结点（控制点 ≠ 锚点）"""
        return {
            'before': {'x': round(cax, 3), 'y': round(cay, 3)},
            'anchor': {'x': round(ax, 3), 'y': round(ay, 3)},
            'after':  {'x': round(cbx, 3), 'y': round(cby, 3)},
        }

    # 8 节点排列顺序（顺时针）：
    # [0] 左边缘上 → [1] 左边缘下 → [2] 下边缘左 → [3] 下边缘右
    # → [4] 右边缘下 → [5] 右边缘上 → [6] 上边缘右 → [7] 上边缘左
    return [
        knot(0, ry),                    # [0] 左边缘上端
        knot(0, h - ry),                 # [1] 左边缘下端
        corner(rx, h,                   # [2] 左下转角
               rx, h - ry * k,          # 入控制点：沿下边缘向左拉出
               rx * k, h),              # 出控制点：沿左边缘向下拉出
        knot(w - rx, h),                 # [3] 下边缘右端
        corner(w, h - ry,               # [4] 右下转角
               w - rx * k, h - ry,      # 入控制点：沿下边缘向右拉出
               w, h - ry * k),          # 出控制点：沿右边缘向下拉出
        knot(w, ry),                     # [5] 右边缘上端
        corner(w - rx, 0,               # [6] 右上转角
               w, ry * k,               # 入控制点：沿右边缘向上拉出
               w - rx * k, 0),          # 出控制点：沿上边缘向右拉出
        corner(rx, 0,                   # [7] 左上转角
               rx * k, 0,               # 入控制点：沿上边缘向左拉出
               rx, ry * k),             # 出控制点：沿左边缘向上拉出
    ]


def is_straight(prev, curr, eps=0.05):
    """
    判断从 prev → curr 的段是否为直线。
    当 prev 的出控制点 ≈ prev 锚点，且 curr 的入控制点 ≈ curr 锚点时 → 直线。
    （PS 导出的 SVG 就是用这个规则：控制点和锚点重合时用 L 不用 C）
    """
    da = abs(prev['after']['x'] - prev['anchor']['x']) + abs(prev['after']['y'] - prev['anchor']['y'])
    db = abs(curr['before']['x'] - curr['anchor']['x']) + abs(curr['before']['y'] - curr['anchor']['y'])
    return da < eps and db < eps


def path_to_d(px_knots):
    """从像素节点列表生成 SVG path 'd' 属性字符串"""
    n = len(px_knots)
    parts = [f"M{px_knots[0]['anchor']['x']:.3f} {px_knots[0]['anchor']['y']:.3f}"]
    for i in range(1, n):
        prev, curr = px_knots[i-1], px_knots[i]
        if is_straight(prev, curr):
            parts.append(f"L{curr['anchor']['x']:.3f} {curr['anchor']['y']:.3f}")
        else:
            parts.append(f"C{prev['after']['x']:.3f} {prev['after']['y']:.3f} "
                         f"{curr['before']['x']:.3f} {curr['before']['y']:.3f} "
                         f"{curr['anchor']['x']:.3f} {curr['anchor']['y']:.3f}")
    last, first = px_knots[-1], px_knots[0]
    if is_straight(last, first):
        parts.append('Z')
    else:
        parts.append(f"C{last['after']['x']:.3f} {last['after']['y']:.3f} "
                     f"{first['before']['x']:.3f} {first['before']['y']:.3f} "
                     f"{first['anchor']['x']:.3f} {first['anchor']['y']:.3f}Z")
    return ' '.join(parts)


def make_svg(px_knots, bbox, fill='rgb(0,0,0)', gradient=None):
    if not px_knots or len(px_knots) < 2:
        return None
    pw, ph = bbox[2], bbox[3]
    d = path_to_d(px_knots)

    svg_parts = [f'<svg xmlns="http://www.w3.org/2000/svg" '
                 f'width="{pw}px" height="{ph}px" viewBox="0 0 {pw} {ph}">']

    if gradient:
        grad_id = 'PSgrad_0'
        stops = ''
        for c in gradient['colors']:
            stops += f'    <stop offset="{int(c["position"]*100)}%" stop-color="{c["rgb"]}" stop-opacity="1"/>\n'
        svg_parts.append(f'  <defs>\n'
                         f'    <linearGradient id="{grad_id}" x1="0%" x2="0%" y1="100%" y2="0%">\n'
                         f'{stops}'
                         f'    </linearGradient>\n'
                         f'  </defs>')
        svg_parts.append(f'  <path fill-rule="evenodd" fill="url(#{grad_id})" d="{d}"/>')
    else:
        svg_parts.append(f'  <path fill-rule="evenodd" fill="{fill}" d="{d}"/>')

    svg_parts.append('</svg>')
    return '\n'.join(svg_parts)


# ═══════════════════════════════════════════
#   复合组件
# ═══════════════════════════════════════════

def build_composite(shape_entries):
    layers = []
    for s in shape_entries:
        name = s['name']
        z = 0
        parts = name.rsplit(' ', 1)
        if len(parts) == 2 and parts[1].isdigit():
            z = int(parts[1])
        layers.append({
            'z_index': z,
            'name': name,
            'bbox': s['bbox'],
            'shape_type': s.get('shape_type', 'unknown'),
            'fill': s.get('fill'),
            'gradient': s.get('gradient'),
            'inner_shadow': s.get('inner_shadow'),
            'svg_file': s['svg_file'],
        })
    layers.sort(key=lambda x: x['z_index'])
    return layers


# ═══════════════════════════════════════════
#   主流程
# ═══════════════════════════════════════════

def main():
    for d in [SVG_DIR, JSON_DIR, COMPOSITE_DIR]:
        os.makedirs(d, exist_ok=True)

    psd = PSDImage.open(PSD_PATH)
    print(f"CinderUI — 全自动提取 {os.path.basename(PSD_PATH)}")
    print(f"画布: {psd.width}x{psd.height}\n")

    flat_shapes = []
    group_shapes = {}

    def collect(layers, parent_chain=''):
        for layer in layers:
            name = layer.name or '(unnamed)'
            chain = f"{parent_chain}/{name}" if parent_chain else name
            if layer.is_group():
                collect(layer, chain)
            elif is_vector(layer):
                bbox = [layer.left, layer.top, layer.width, layer.height]
                raw_knots = parse_knots(layer)
                if len(raw_knots) < 4:
                    continue
                px_knots = knots_to_pixel(raw_knots, bbox)
                px_knots = fix_pill_to_rounded(px_knots)
                style = extract_layer_style(layer)
                entry = {
                    'type': 'shape',
                    'name': name,
                    'parent_chain': parent_chain,
                    'full_path': chain,
                    'bbox': bbox,
                    'knot_count': len(raw_knots),
                    'shape_type': classify(len(raw_knots)),
                    'fill': style['fill'],
                    'gradient': style['gradient'],
                    'inner_shadow': style['inner_shadow'],
                    'knots_px': px_knots,
                }
                cp = extract_corner_params(raw_knots)
                if cp:
                    entry['corner_params'] = cp
                flat_shapes.append(entry)
                if parent_chain:
                    group_shapes.setdefault(parent_chain, []).append(entry)

    collect(psd)

    # ——— 输出独立形状 ———
    for s in flat_shapes:
        fname = s['full_path'].replace(' ', '_').replace('/', '--').replace('__', '_')
        fill_color = s['fill'] or 'rgb(0,0,0)'
        svg = make_svg(s['knots_px'], s['bbox'], fill_color, s.get('gradient'))
        if svg:
            s['svg_file'] = f"{fname}.svg"
            with open(os.path.join(SVG_DIR, s['svg_file']), 'w', encoding='utf-8') as f:
                f.write(svg)
        s['json_file'] = f"{fname}.json"
        json_out = {k: v for k, v in s.items() if k not in ('knots_px',)}
        with open(os.path.join(JSON_DIR, s['json_file']), 'w', encoding='utf-8') as f:
            json.dump(json_out, f, ensure_ascii=False, indent=2)

    # ——— 复合组件 ———
    composites = []
    for group_path, shapes in sorted(group_shapes.items()):
        if len(shapes) < 2:
            continue
        composite = build_composite(shapes)
        if len(composite) < 2:
            continue
        group_safe = group_path.replace(' ', '_').replace('/', '--').replace('__', '_')
        comp_dir = os.path.join(COMPOSITE_DIR, group_safe)
        os.makedirs(comp_dir, exist_ok=True)

        # 计算复合视口基准（所有层的 left/top 最小值）
        base_left = min(l['bbox'][0] for l in composite)
        base_top = min(l['bbox'][1] for l in composite)
        comp_w = max(l['bbox'][0] + l['bbox'][2] for l in composite) - base_left
        comp_h = max(l['bbox'][1] + l['bbox'][3] for l in composite) - base_top

        # 生成合成 SVG：从各层的 path 提取 path + 渐变，叠到一个 viewport
        svg_parts = [f'<svg xmlns="http://www.w3.org/2000/svg" '
                     f'width="{comp_w}px" height="{comp_h}px" viewBox="0 0 {comp_w} {comp_h}">']
        grad_count = 0
        # 收集所有渐变到 defs
        defs_parts = ['  <defs>']
        has_defs = False
        for l in composite:
            s = next(s for s in flat_shapes
                     if s['name'] == l['name'] and s['parent_chain'] == group_path)
            if s.get('gradient'):
                grad_count += 1
                gid = f"grad_{grad_count}"
                has_defs = True
                stops = ''
                for c in s['gradient']['colors']:
                    stops += f'      <stop offset="{int(c["position"]*100)}%" stop-color="{c["rgb"]}" stop-opacity="1"/>\n'
                defs_parts.append(f'    <linearGradient id="{gid}" x1="0%" x2="0%" y1="100%" y2="0%">\n'
                                  f'{stops}    </linearGradient>')
        if has_defs:
            svg_parts.append('\n'.join(defs_parts) + '\n  </defs>')

        # 按 z-index 从低到高叠加各层
        for l in composite:
            s = next(s for s in flat_shapes
                     if s['name'] == l['name'] and s['parent_chain'] == group_path)
            dx = l['bbox'][0] - base_left
            dy = l['bbox'][1] - base_top
            fill = l['fill'] or 'rgb(0,0,0)'
            if s.get('gradient'):
                fill = f"url(#grad_{grad_count})"
                grad_count -= 1
            # 生成该层 path
            px = s['knots_px']
            d = path_to_d(px)
            trans = ''
            if dx != 0 or dy != 0:
                trans = f' transform="translate({dx}, {dy})"'
            svg_parts.append(f'  <path{trans} fill-rule="evenodd" fill="{fill}" d="{d}"/>')

        svg_parts.append('</svg>')
        comp_svg = '\n'.join(svg_parts)

        comp_info = {
            'group_name': group_path,
            'layer_count': len(composite),
            'composite_viewport': [comp_w, comp_h],
            'layers': [{
                'z_index': l['z_index'],
                'name': l['name'],
                'fill': l['fill'],
                'gradient': l['gradient'],
                'inner_shadow': l['inner_shadow'],
                'bbox': l['bbox'],
                'offset_relative_to_composite': [l['bbox'][0] - base_left, l['bbox'][1] - base_top],
                'shape_type': l['shape_type'],
            } for l in composite],
        }
        composites.append(comp_info)
        with open(os.path.join(comp_dir, 'composite.json'), 'w', encoding='utf-8') as f:
            json.dump(comp_info, f, ensure_ascii=False, indent=2)
        with open(os.path.join(comp_dir, 'composite.svg'), 'w', encoding='utf-8') as f:
            f.write(comp_svg)

    # ——— 参数汇总 ———
    corner_params = []
    for s in flat_shapes:
        if s.get('corner_params'):
            corner_params.append({
                'name': s['full_path'],
                'size': f"{s['bbox'][2]}x{s['bbox'][3]}",
                'shape_type': s['shape_type'],
                'fill': s.get('fill'),
                **s['corner_params'],
            })

    params = {
        'psd': {'width': psd.width, 'height': psd.height},
        'total_shapes': len(flat_shapes),
        'total_composites': len(composites),
        'corner_parameters': sorted(corner_params, key=lambda x: x['size']),
        'composites': composites,
    }
    with open(os.path.join(OUT_DIR, 'parameters.json'), 'w', encoding='utf-8') as f:
        json.dump(params, f, ensure_ascii=False, indent=2)

    print(f"提取完成！")
    print(f"  形状数: {len(flat_shapes)}")
    print(f"  复合组件: {len(composites)}（含 {sum(c['layer_count'] for c in composites)} 层）")
    print(f"  SVG: {SVG_DIR}/")
    print(f"  JSON: {JSON_DIR}/")
    print(f"  Composites: {COMPOSITE_DIR}/")


if __name__ == '__main__':
    main()
