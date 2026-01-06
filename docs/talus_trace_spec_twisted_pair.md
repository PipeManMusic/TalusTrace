# Talus Trace Specification: Twisted Pair

## 4.3 Rotation

Anchors support 90-degree rotation increments via `rotate_90()`.

- 0° / 180° = Vertical Layout (Pin 1 is offset Y).
- 90° / 270° = Horizontal Layout (Pin 1 is offset X).

## Data Model (Excerpt)

| Field         | Type    | Description                       |
|-------------- |---------|-----------------------------------|
| id            | str     | Unique identifier                 |
| node_a        | tuple   | Anchor A position (x, y)          |
| node_b        | tuple   | Anchor B position (x, y)          |
| rotation_a    | int     | Anchor A rotation (degrees, 0-359)|
| rotation_b    | int     | Anchor B rotation (degrees, 0-359)|
| wire_id_1     | str     | Wire 1 ID                         |
| wire_id_2     | str     | Wire 2 ID                         |

(Other fields omitted for brevity.)
