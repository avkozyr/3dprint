import re
import sys
import zipfile
from pathlib import Path

VERTEX = re.compile(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"\s*/>')
TRIANGLE = re.compile(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"[^>]*/>')
OBJECT = re.compile(r'(<object id="(\d+)"[^>]*>\s*<mesh>)(.*?)(</mesh>)', re.S)
PART = re.compile(r'<part id="(\d+)".*?</part>', re.S)


def bounds(vertices):
    xs, ys, zs = zip(*vertices)
    return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


def read_mesh(block):
    vertices = [tuple(map(float, m)) for m in VERTEX.findall(block)]
    triangles = [tuple(map(int, m)) for m in TRIANGLE.findall(block)]
    return vertices, triangles


def read_plate_file(path):
    with zipfile.ZipFile(path) as archive:
        text = archive.read("3D/3dmodel.model").decode()
    meshes = {m.group(2): read_mesh(m.group(3)) for m in OBJECT.finditer(text)}
    components = re.findall(r'<component [^>]*objectid="(\d+)"', text)
    order = components or list(meshes)
    return [meshes[object_id] for object_id in order]


def reposition(new_vertices, old_vertices):
    (ox0, oy0, oz0), (ox1, oy1, _) = bounds(old_vertices)
    (nx0, ny0, nz0), (nx1, ny1, _) = bounds(new_vertices)
    dx = (ox0 + ox1) / 2 - (nx0 + nx1) / 2
    dy = (oy0 + oy1) / 2 - (ny0 + ny1) / 2
    dz = oz0 - nz0
    return [(x + dx, y + dy, z + dz) for x, y, z in new_vertices]


def unchanged(vertices, triangles, old_vertices, old_triangles):
    if triangles != old_triangles or len(vertices) != len(old_vertices):
        return False
    return all(abs(a - b) < 1e-4 for new, old in zip(vertices, old_vertices) for a, b in zip(new, old))


def write_mesh(vertices, triangles):
    lines = ["\n    <vertices>"]
    lines += [f'     <vertex x="{x:.7g}" y="{y:.7g}" z="{z:.7g}"/>' for x, y, z in vertices]
    lines += ["    </vertices>", "    <triangles>"]
    lines += [f'     <triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in triangles]
    lines += ["    </triangles>", "   "]
    return "\n".join(lines)


def part_sources(model_settings):
    sources = {}
    for part in PART.finditer(model_settings):
        block = part.group(0)
        source_file = re.search(r'key="source_file" value="([^"]*)"', block).group(1)
        volume = int(re.search(r'key="source_volume_id" value="(\d+)"', block).group(1))
        sources[part.group(1)] = (Path(source_file).name, volume)
    return sources


def update_face_counts(model_settings, face_counts):
    def replace_part(part):
        block = part.group(0)
        count = face_counts[part.group(1)]
        return re.sub(r'(<mesh_stat face_count=")\d+', rf"\g<1>{count}", block)

    def replace_object(match):
        block = PART.sub(replace_part, match.group(0))
        total = sum(face_counts[p] for p in re.findall(r'<part id="(\d+)"', block))
        return re.sub(r'(<metadata face_count=")\d+', rf"\g<1>{total}", block, count=1)

    return re.sub(r'<object id="\d+">.*?</object>', replace_object, model_settings, flags=re.S)


def build(template_path, plates_dir, output_path):
    plates = {}
    face_counts = {}
    report = []
    with zipfile.ZipFile(template_path) as template:
        model_settings = template.read("Metadata/model_settings.config").decode()
        sources = part_sources(model_settings)
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as output:
            for entry in template.infolist():
                data = template.read(entry.filename)
                if entry.filename.startswith("3D/Objects/") and entry.filename.endswith(".model"):
                    text = data.decode()

                    def replace(match):
                        part_id = match.group(2)
                        plate_name, volume = sources[part_id]
                        if plate_name not in plates:
                            plates[plate_name] = read_plate_file(Path(plates_dir) / plate_name)
                        new_vertices, triangles = plates[plate_name][volume]
                        old_vertices, old_triangles = read_mesh(match.group(3))
                        placed = reposition(new_vertices, old_vertices)
                        face_counts[part_id] = len(triangles)
                        shift = max(
                            abs(a - b)
                            for p, q in zip(bounds(placed), bounds(old_vertices))
                            for a, b in zip(p, q)
                        )
                        report.append((part_id, plate_name, volume, len(old_triangles), len(triangles), shift))
                        if unchanged(placed, triangles, old_vertices, old_triangles):
                            return match.group(0)
                        return match.group(1) + write_mesh(placed, triangles) + match.group(4)

                    data = OBJECT.sub(replace, text).encode()
                elif entry.filename == "Metadata/model_settings.config":
                    continue
                output.writestr(entry.filename, data)
            output.writestr("Metadata/model_settings.config", update_face_counts(model_settings, face_counts))
    return report


if __name__ == "__main__":
    template_path, plates_dir, output_path = sys.argv[1:4]
    for part_id, plate_name, volume, old_faces, new_faces, shift in build(template_path, plates_dir, output_path):
        print(f"part {part_id}: {plate_name}[{volume}] faces {old_faces} -> {new_faces}, bounds change {shift:.6f} mm")
