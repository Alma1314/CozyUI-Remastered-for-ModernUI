"""
从 005-矢量图.svg 直接提取"按钮 18x"三个状态到 extracted/
保留所有 gradient 定义，调整 viewBox 裁剪到按钮内容区。
"""
import os, re

SRC = r"d:\Program Files (x86)\GoblinTechMotive\CinderUI\SourceCode 源代码\005-矢量图\005-无样式.svg"
OUT = r"d:\Program Files (x86)\GoblinTechMotive\CinderUI\extracted"

# ── 按钮 18x 的三层数据（SVG 原始坐标 1622,482,72x72）──────────────────────

# 层0: 外框剪裁 path（无填充，定义 clip region）
LAYER0 = 'M1666,482h-16c-22,0-28,6-28,28v16c0,22,6,28,28,28h16c22,0,28-6,28-28v-16c0-22-6-28-28-28Z'

# 层1: 中间实色层（6 节点 Pill path，留待研究圆角参数）
LAYERS1 = {
    '按钮禁用': 'M1626,510v16c0,19,5,24,24,24h16c19,0,24-5,24-24v-16h-64Z',
    '按钮常态': 'M1626,510v16c0,19,5,24,24,24h16c19,0,24-5,24-24v-16h-64Z',
    '按钮选中': 'M1626,510v16c0,19,5,24,24,24h16c19,0,24-5,24-24v-16h-64Z',
}

# 层2 rect: rx=24 的 Squircle 圆角矩形
LAYER2_RECT = 'x="1626" y="486" width="64" height="56" rx="24" ry="24"'

# 层2 stroke path（双线描边效果）
LAYER2_STROKE = {
    '按钮禁用': 'M1666,490c8.83,0,13.7,1.11,16.3,3.7,2.6,2.6,3.7,7.47,3.7,16.3v8c0,8.83-1.11,13.7-3.7,16.3-2.6,2.6-7.47,3.7-16.3,3.7h-16c-8.83,0-13.7-1.11-16.3-3.7-2.6-2.6-3.7-7.47-3.7-16.3v-8c0-8.83,1.11-13.7,3.7-16.3,2.6-2.6,7.47-3.7,16.3-3.7h16M1666,486h-16c-19,0-24,5-24,24v8c0,19,5,24,24,24h16c19,0,24-5,24-24v-8c0-19-5-24-24-24h0Z',
    '按钮常态': 'M1666,490c8.83,0,13.7,1.11,16.3,3.7,2.6,2.6,3.7,7.47,3.7,16.3v8c0,8.83-1.11,13.7-3.7,16.3-2.6,2.6-7.47,3.7-16.3,3.7h-16c-8.83,0-13.7-1.11-16.3-3.7-2.6-2.6-3.7-7.47-3.7-16.3v-8c0-8.83,1.11-13.7,3.7-16.3,2.6-2.6,7.47-3.7,16.3-3.7h16M1666,486h-16c-19,0-24,5-24,24v8c0,19,5,24,24,24h16c19,0,24-5,24-24v-8c0-19-5-24-24-24h0Z',
    '按钮选中': 'M1666,490c8.83,0,13.7,1.11,16.3,3.7,2.6,2.6,3.7,7.47,3.7,16.3v8c0,8.83-1.11,13.7-3.7,16.3-2.6,2.6-7.47,3.7-16.3,3.7h-16c-8.83,0-13.7-1.11-16.3-3.7-2.6-2.6-3.7-7.47-3.7-16.3v-8c0-8.83,1.11-13.7,3.7-16.3,2.6-2.6,7.47-3.7,16.3-3.7h16M1666,486h-16c-19,0-24,5-24,24v8c0,19,5,24,24,24h16c19,0,24-5,24-24v-8c0-19-5-24-24-24h0Z',
}

# 层1 填充色
LAYER1_FILL = {
    '按钮禁用': '#343130',
    '按钮常态': '#5c5958',
    '按钮选中': '#5d53a4',
}

# 层2 渐变 ID
LAYER2_GRAD = {
    '按钮禁用': '#_未命名的渐变_81',
    '按钮常态': '#_未命名的渐变_41-4',
    '按钮选中': '#_未命名的渐变_2-5',
}

LAYER2_STROKE_GRAD = {
    '按钮禁用': '#_新建渐变色板_3',
    '按钮常态': '#_新建渐变色板_4',
    '按钮选中': '#_新建渐变色板_5',
}

# 层0 填充色
LAYER0_FILL = {
    '按钮禁用': 'none',   # 黑色 frame，层2 rect 遮住
    '按钮常态': 'none',
    '按钮选中': '#fff',   # 白色 frame
}

# ── gradient 定义（从源文件 defs 提取）───────────────────────────────────────
# 按钮禁用: _未命名的渐变_81 (base, 单色 solid), _新建渐变色板_3 (双色)
# 按钮常态: _未命名的渐变_41 (base), _新建渐变色板_4
# 按钮选中: _未命名的渐变_2 (base), _新建渐变色板_5

GRADIENTS = """
    <!-- 按钮禁用 -->
    <linearGradient id="_未命名的渐变_41" data-name="未命名的渐变 41" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#7b7877"/>
      <stop offset="100%" stop-color="#83807f"/>
    </linearGradient>
    <linearGradient id="_未命名的渐变_81" data-name="未命名的渐变 81" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#343130"/>
      <stop offset="100%" stop-color="#302d2c"/>
    </linearGradient>
    <linearGradient id="_新建渐变色板_3" data-name="新建渐变色板 3" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#646160"/>
      <stop offset="100%" stop-color="#444140"/>
    </linearGradient>

    <!-- 按钮常态 -->
    <linearGradient id="_新建渐变色板_4" data-name="新建渐变色板 4" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#a3a09f"/>
      <stop offset="100%" stop-color="#c3c0bf"/>
    </linearGradient>

    <!-- 按钮选中 -->
    <linearGradient id="_未命名的渐变_2" data-name="未命名的渐变 2" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#786fcf"/>
      <stop offset="100%" stop-color="#7a7cdb"/>
    </linearGradient>
    <linearGradient id="_新建渐变色板_5" data-name="新建渐变色板 5" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#a1a9e8"/>
      <stop offset="100%" stop-color="#bac7ff"/>
    </linearGradient>
"""


def translate_d(d, dx, dy):
    """将 SVG path d 中的坐标整体偏移 (dx, dy)"""
    def sub(m):
        cmd = m.group(1)
        nums = m.group(2)
        if cmd in ('M', 'L', 'C', 'Q', 'A', 'Z', 'm', 'l', 'c', 'q', 'a', 'z', 'H', 'h', 'V', 'v', 'S', 's', 'T', 't'):
            if cmd.isupper():
                # 大写：绝对坐标，按增量偏移
                parts = nums.split(',')
                result = []
                for p in parts:
                    try:
                        result.append(f"{float(p) + (dx if len(result) % 2 == 0 else dy):.3f}")
                    except ValueError:
                        result.append(p)
                return cmd + ','.join(result)
            else:
                # 小写：相对坐标，直接用
                return m.group(0)
        return m.group(0)
    import re
    # 匹配命令字母 + 数字序列
    pattern = re.compile(r'([MmLlHhVvCcSsQqTtAaZz])([^MmLlHhVvCcSsQqTtAaZz]*)')
    result = []
    last_pos = 0
    for m in pattern.finditer(d):
        result.append(d[last_pos:m.start()])
        cmd = m.group(1)
        nums = m.group(2).strip()
        if nums:
            parts_str = re.split(r'([\s,]+)(?=[+-]?)', nums)
            merged = []
            i = 0
            while i < len(parts_str):
                if parts_str[i].strip() in (',', ' ', ''):
                    merged.append(parts_str[i])
                    i += 1
                else:
                    try:
                        val = float(parts_str[i])
                        # 判断是 x 还是 y：基于命令的参数顺序
                        if cmd.lower() in ('m', 'l', 't'):
                            merged.append(parts_str[i])
                            i += 1
                        elif cmd.lower() in ('c'):
                            # c dx1,dy1 dx2,dy2 dx,dy → 奇数位 x，偶数位 y
                            pass
                        else:
                            merged.append(parts_str[i])
                            i += 1
                    except (ValueError, IndexError):
                        merged.append(parts_str[i])
                        i += 1
            result.append(cmd + nums)
        else:
            result.append(m.group(0))
        last_pos = m.end()
    result.append(d[last_pos:])
    return ''.join(result)

    # 重写：按参数数量处理
    def rewrite_cmd(cmd, nums_str):
        nums = [x.strip() for x in re.split(r'[\s,]+', nums_str) if x.strip()]
        if not nums:
            return cmd
        abs_cmd = cmd.upper()
        n = len(nums)
        new_nums = []
        if abs_cmd in ('M', 'L', 'T'):
            for i in range(0, n, 2):
                if i+1 < n:
                    new_nums.append(f"{float(nums[i]) + dx:.3f}")
                    new_nums.append(f"{float(nums[i+1]) + dy:.3f}")
        elif abs_cmd in ('H'):
            for i, v in enumerate(nums):
                new_nums.append(f"{float(v) + dx:.3f}")
        elif abs_cmd in ('V'):
            for i, v in enumerate(nums):
                new_nums.append(f"{float(v) + dy:.3f}")
        elif abs_cmd == 'C':
            for i in range(0, n, 6):
                if i+5 < n:
                    new_nums.append(f"{float(nums[i]) + dx:.3f}")
                    new_nums.append(f"{float(nums[i+1]) + dy:.3f}")
                    new_nums.append(f"{float(nums[i+2]) + dx:.3f}")
                    new_nums.append(f"{float(nums[i+3]) + dy:.3f}")
                    new_nums.append(f"{float(nums[i+4]) + dx:.3f}")
                    new_nums.append(f"{float(nums[i+5]) + dy:.3f}")
        elif abs_cmd in ('S', 'Q'):
            for i in range(0, n, 4):
                if i+3 < n:
                    new_nums.append(f"{float(nums[i]) + dx:.3f}")
                    new_nums.append(f"{float(nums[i+1]) + dy:.3f}")
                    new_nums.append(f"{float(nums[i+2]) + dx:.3f}")
                    new_nums.append(f"{float(nums[i+3]) + dy:.3f}")
        elif abs_cmd in ('A'):
            for i in range(0, n, 7):
                if i+6 < n:
                    new_nums.append(nums[i])  # rx
                    new_nums.append(nums[i+1])  # ry
                    new_nums.append(nums[i+2])  # rotation
                    new_nums.append(nums[i+3])  # large-arc
                    new_nums.append(nums[i+4])  # sweep
                    new_nums.append(f"{float(nums[i+5]) + dx:.3f}")
                    new_nums.append(f"{float(nums[i+6]) + dy:.3f}")
        return cmd + ','.join(new_nums)

    def replacer(m):
        return rewrite_cmd(m.group(1), m.group(2))

    return pattern.sub(replacer, d)


def translate_rect(rect_str, dx, dy):
    """偏移 rect 坐标"""
    def sub(m):
        attrs = m.group(0)
        attrs = re.sub(r'x="([^"]+)"', lambda am: f'x="{float(am.group(1)) + dx:.3f}"', attrs)
        attrs = re.sub(r'y="([^"]+)"', lambda am: f'y="{float(am.group(1)) + dy:.3f}"', attrs)
        return attrs
    return re.sub(r'(x="[^"]+"|y="[^"]+"|width="[^"]+"|height="[^"]+"|rx="[^"]+"|ry="[^"]+")+', sub, rect_str)


def make_svg(state_name, l0_fill, l1_fill, l1_path, l2_rect, l2_grad, l2_stroke, l2_sgrad):
    """
    生成按钮 SVG。
    坐标已从画布 (1622,482) 平移到 (0,0)。
    viewBox: 0 0 72 64（72x72 画布裁剪到实际内容 68x60）
    """
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 72 64" width="72" height="64">
  <defs>
{GRADIENTS}
  </defs>

  <!-- 层0: 外框剪裁（无填充，定义 clip region） -->
  <path d="M44,0h-16C6,0,0,6,0,28v8c0,22,6,28,28,28h16c22,0,28-6,28-28v-8c0-22-6-28-28-28Z"
        fill="{l0_fill}" fill-rule="evenodd"/>

  <!-- 层1: 中间实色阴影层（6节点 Pill，顶部/底部为直角，留待研究圆角参数） -->
  <path d="M68,28v16c0,19-5,24-24,24h-16c-19,0-24-5-24-24v-16h64Z"
        fill="{l1_fill}" fill-rule="evenodd"/>

  <!-- 层2: 内层渐变填充 + 双线描边 -->
  <rect x="4" y="4" width="64" height="56" rx="24" ry="24" fill="url({l2_grad})"/>
  <path d="M44,8c8.83,0,13.7,1.11,16.3,3.7,2.6,2.6,3.7,7.47,3.7,16.3v8c0,8.83-1.11,13.7-3.7,16.3-2.6,2.6-7.47,3.7-16.3,3.7h-16c-8.83,0-13.7-1.11-16.3-3.7-2.6-2.6-3.7-7.47-3.7-16.3v-8c0-8.83,1.11-13.7,3.7-16.3,2.6-2.6,7.47-3.7,16.3-3.7h16M44,4h-16c-19,0-24,5-24,24v8c0,19,5,24,24,24h16c19,0,24-5,24-24v-8c0-19-5-24-24-24h0Z"
        fill="url({l2_sgrad})"/>
</svg>
'''


def main():
    os.makedirs(OUT, exist_ok=True)

    states = [
        ('按钮禁用', LAYER0_FILL['按钮禁用'], LAYER1_FILL['按钮禁用'],
         LAYERS1['按钮禁用'], LAYER2_RECT,
         LAYER2_GRAD['按钮禁用'], LAYER2_STROKE['按钮禁用'],
         LAYER2_STROKE_GRAD['按钮禁用']),

        ('按钮常态', LAYER0_FILL['按钮常态'], LAYER1_FILL['按钮常态'],
         LAYERS1['按钮常态'], LAYER2_RECT,
         LAYER2_GRAD['按钮常态'], LAYER2_STROKE['按钮常态'],
         LAYER2_STROKE_GRAD['按钮常态']),

        ('按钮选中', LAYER0_FILL['按钮选中'], LAYER1_FILL['按钮选中'],
         LAYERS1['按钮选中'], LAYER2_RECT,
         LAYER2_GRAD['按钮选中'], LAYER2_STROKE['按钮选中'],
         LAYER2_STROKE_GRAD['按钮选中']),
    ]

    for state, l0, l1, l1p, l2r, l2g, l2s, l2sg in states:
        svg = make_svg(state, l0, l1, l1p, l2r, l2g, l2s, l2sg)
        path = os.path.join(OUT, f'按钮_18x--{state}.svg')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(svg)
        print(f'  ✓ {os.path.basename(path)}')

    # 同时输出复合组件版本（3 层叠加）
    composite = f'''<?xml version="1.0" encoding="UTF-8"?>
<!-- 按钮_18x 复合组件（禁用/常态/选中 三个状态的父级组）-->
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 72 192" width="72" height="192">
  <defs>
{GRADIENTS}
  </defs>

  <!-- 禁用态 (y=0) -->
  <g transform="translate(0,0)">
    <path d="M44,0h-16C6,0,0,6,0,28v8c0,22,6,28,28,28h16c22,0,28-6,28-28v-8c0-22-6-28-28-28Z" fill="#0d0d0d" fill-rule="evenodd" opacity="0.6"/>
    <path d="M68,28v16c0,19-5,24-24,24h-16c-19,0-24-5-24-24v-16h64Z" fill="#343130" fill-rule="evenodd"/>
    <rect x="4" y="4" width="64" height="56" rx="24" ry="24" fill="url(#_未命名的渐变_81)"/>
    <path d="M44,8c8.83,0,13.7,1.11,16.3,3.7,2.6,2.6,3.7,7.47,3.7,16.3v8c0,8.83-1.11,13.7-3.7,16.3-2.6,2.6-7.47,3.7-16.3,3.7h-16c-8.83,0-13.7-1.11-16.3-3.7-2.6-2.6-3.7-7.47-3.7-16.3v-8c0-8.83,1.11-13.7,3.7-16.3,2.6-2.6,7.47-3.7,16.3-3.7h16M44,4h-16c-19,0-24,5-24,24v8c0,19,5,24,24,24h16c19,0,24-5,24-24v-8c0-19-5-24-24-24h0Z" fill="url(#_新建渐变色板_3)"/>
  </g>

  <!-- 常态 (y=64) -->
  <g transform="translate(0,64)">
    <path d="M44,0h-16C6,0,0,6,0,28v8c0,22,6,28,28,28h16c22,0,28-6,28-28v-8c0-22-6-28-28-28Z" fill="#000000" fill-rule="evenodd" opacity="0.4"/>
    <path d="M68,28v16c0,19-5,24-24,24h-16c-19,0-24-5-24-24v-16h64Z" fill="#5c5958" fill-rule="evenodd"/>
    <rect x="4" y="4" width="64" height="56" rx="24" ry="24" fill="url(#_未命名的渐变_41-4)"/>
    <path d="M44,8c8.83,0,13.7,1.11,16.3,3.7,2.6,2.6,3.7,7.47,3.7,16.3v8c0,8.83-1.11,13.7-3.7,16.3-2.6,2.6-7.47,3.7-16.3,3.7h-16c-8.83,0-13.7-1.11-16.3-3.7-2.6-2.6-3.7-7.47-3.7-16.3v-8c0-8.83,1.11-13.7,3.7-16.3,2.6-2.6,7.47-3.7,16.3-3.7h16M44,4h-16c-19,0-24,5-24,24v8c0,19,5,24,24,24h16c19,0,24-5,24-24v-8c0-19-5-24-24-24h0Z" fill="url(#_新建渐变色板_4)"/>
  </g>

  <!-- 选中 (y=128) -->
  <g transform="translate(0,128)">
    <path d="M44,0h-16C6,0,0,6,0,28v8c0,22,6,28,28,28h16c22,0,28-6,28-28v-8c0-22-6-28-28-28Z" fill="#fff" fill-rule="evenodd"/>
    <path d="M68,28v16c0,19-5,24-24,24h-16c-19,0-24-5-24-24v-16h64Z" fill="#5d53a4" fill-rule="evenodd"/>
    <rect x="4" y="4" width="64" height="56" rx="24" ry="24" fill="url(#_未命名的渐变_2-5)"/>
    <path d="M44,8c8.83,0,13.7,1.11,16.3,3.7,2.6,2.6,3.7,7.47,3.7,16.3v8c0,8.83-1.11,13.7-3.7,16.3-2.6,2.6-7.47,3.7-16.3,3.7h-16c-8.83,0-13.7-1.11-16.3-3.7-2.6-2.6-3.7-7.47-3.7-16.3v-8c0-8.83,1.11-13.7,3.7-16.3,2.6-2.6,7.47-3.7,16.3-3.7h16M44,4h-16c-19,0-24,5-24,24v8c0,19,5,24,24,24h16c19,0,24-5,24-24v-8c0-19-5-24-24-24h0Z" fill="url(#_新建渐变色板_5)"/>
  </g>
</svg>
'''
    comp_path = os.path.join(OUT, 'composites', '按钮_18x--复合.svg')
    os.makedirs(os.path.dirname(comp_path), exist_ok=True)
    with open(comp_path, 'w', encoding='utf-8') as f:
        f.write(composite)
    print(f'  ✓ composites/按钮_18x--复合.svg')

    print(f'\n提取完成！输出目录: {OUT}')


if __name__ == '__main__':
    main()
