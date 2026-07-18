"""Debug the fix_pill_to_rounded function"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from tools.extract import fix_pill_to_rounded, is_straight

knots = [
    {'before': {'x':0,'y':43}, 'anchor':{'x':0,'y':43}, 'after':{'x':0,'y':43}},
    {'before': {'x':26.8,'y':43}, 'anchor':{'x':26.8,'y':43}, 'after':{'x':25.3,'y':43}},
    {'before': {'x':67,'y':36.7}, 'anchor':{'x':67,'y':26.875}, 'after':{'x':67,'y':19.719}},
    {'before': {'x':67,'y':9.055}, 'anchor':{'x':67,'y':16.125}, 'after':{'x':67,'y':9.055}},
    {'before': {'x':26.8,'y':3.281}, 'anchor':{'x':26.8,'y':0}, 'after':{'x':26.8,'y':0}},
    {'before': {'x':0,'y':0}, 'anchor':{'x':0,'y':0}, 'after':{'x':0,'y':0}},
]

xs = [k['anchor']['x'] for k in knots]
ys = [k['anchor']['y'] for k in knots]
print(f'bbox: x=[{min(xs):.1f},{max(xs):.1f}] y=[{min(ys):.1f},{max(ys):.1f}]')
print(f'w={max(xs)-min(xs):.1f} h={max(ys)-min(ys):.1f}')

for i in range(6):
    prev, curr = knots[i-1], knots[i]
    straight = is_straight(prev, curr)
    dx = abs(curr['anchor']['x'] - prev['anchor']['x'])
    dy = abs(curr['anchor']['y'] - prev['anchor']['y'])
    print(f'  seg[{i}]: ({prev["anchor"]["x"]:.1f},{prev["anchor"]["y"]:.1f}) -> ({curr["anchor"]["x"]:.1f},{curr["anchor"]["y"]:.1f})  dx={dx:.2f} dy={dy:.2f} straight={straight}')

print()
result = fix_pill_to_rounded(knots)
if len(result) == 8:
    for i, k in enumerate(result):
        print(f'  [{i}] anchor=({k["anchor"]["x"]:.3f}, {k["anchor"]["y"]:.3f})  before=({k["before"]["x"]:.3f},{k["before"]["y"]:.3f})  after=({k["after"]["x"]:.3f},{k["after"]["y"]:.3f})')
