import xml.parsers.expat
import re

def nextpoint(prev, mode, dxy):
    x, y = 0, 0
    if mode in 'lhvV':  x += prev[0]
    if mode in 'lhvH':  y += prev[1]
    if mode in 'lhLH':  x += dxy[0]
    if mode in 'lvLV':  y += dxy[1]
    return x, y

def get_points(d):
    mode = 'L'
    point = (0, 0)
    result = []
    for value in d.split():
        if value in 'mzMZ':
            continue
        elif value in 'lhvLHV':
            mode = value
        elif value.isalpha():
            mode = 'L'
        else:
            value = tuple(float(v) for v in value.split(','))
            dxy = (value * 2)[:2]
            point = nextpoint(point, mode, dxy)
            result.append(point)
    return result


def mk_handler(path_dict):
    def start_element(name, attrs):
        if 'id' in attrs and 'd' in attrs:
            points = get_points(attrs['d'])
            path_dict[attrs['id']] = points
    return start_element

def get_path_dict(raw_svg):
    path_dict = {}
    p = xml.parsers.expat.ParserCreate()
    p.StartElementHandler = mk_handler(path_dict)
    p.Parse(raw_svg, 1)
    return path_dict


def points_string(points, json_point, indent_level, indent_width):
    if indent_level < 0:
        sep = ', '
    else:
        indent = ' ' * indent_width if indent_width >= 0 else '\t'
        sep = ',\n' + indent * indent_level
    return sep.join(json_point(p) for p in points)

def eval_command(command, json_point, path_dict):
    path_id = ''
    level = 0
    width = -1
    singular_point = False
    point_index = 0
    integer = False
    for c in command.split():
        if c.startswith('-LV='):
            level = int(float(c[4:]))
        elif c.startswith('-W='):
            width = int(float(c[3:]))
        elif c.startswith('-P='):
            singular_point = True
            point_index = int(float(c[3:]))
        elif c.startswith('-INT'):
            integer = True
        else:
            path_id = c
    if path_id in path_dict:
        points = path_dict[path_id]
        if singular_point:
            return json_point(points[point_index], integer)
        else:
            return points_string(points, json_point, level, width)
    else:
        return ''


def read(filename):
    with open(filename, 'r') as f:
        return ''.join(f.readlines())

def write(filename, content):
    with open(filename, 'w') as f:
        f.write(content)

def appendwrite(filename, content):
    with open(filename, 'a') as f:
        f.write(content)


def json_point(svg_point, integer=False):
    x, y = svg_point
    x = (x - 8160/2) / 2
    y = (4788/2 - y) / 2
    if integer:
        return f'[{int(x)}, {int(y)}]'
    return f'[{x}, {y}]'

if __name__ == '__main__':
    svg_filename = './taipei.svg'
    template_filename = './city_temp.json'
    json_filename = './city.json'
    
    path_dict = get_path_dict(read(svg_filename))
    
    template_json = read(template_filename)
    
    write(json_filename, '')
    start = 0
    for match in re.finditer('"###(.+)###"', template_json):
        content = template_json[start : match.start()]
        start = match.end()
        appendwrite(json_filename, content)
        content = eval_command(match.group(1), json_point, path_dict)
        appendwrite(json_filename, content)
    content = template_json[start:]
    appendwrite(json_filename, content)
    
