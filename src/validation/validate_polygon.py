from typing import Any


# Return the orientation of three points for segment intersection checks.
def _ccw(
    point_a: tuple[float, float],
    point_b: tuple[float, float],
    point_c: tuple[float, float],
) -> bool:
    return (point_c[1] - point_a[1]) * (point_b[0] - point_a[0]) > (
        point_b[1] - point_a[1]
    ) * (point_c[0] - point_a[0])


# Check whether two line segments cross using the standard CCW test.
def _segments_intersect(
    point_a: tuple[float, float],
    point_b: tuple[float, float],
    point_c: tuple[float, float],
    point_d: tuple[float, float],
) -> bool:
    return _ccw(point_a, point_c, point_d) != _ccw(point_b, point_c, point_d) and _ccw(
        point_a, point_b, point_c
    ) != _ccw(point_a, point_b, point_d)


# Detect an intersection between non-adjacent polygon edges.
def _has_self_intersection(points: list[tuple[float, float]]) -> bool:
    edge_count = len(points)
    for first_index in range(edge_count):
        first_end = (first_index + 1) % edge_count
        for second_index in range(first_index + 1, edge_count):
            second_end = (second_index + 1) % edge_count
            if (
                first_index == second_index
                or first_end == second_index
                or second_end == first_index
            ):
                continue
            if _segments_intersect(
                points[first_index],
                points[first_end],
                points[second_index],
                points[second_end],
            ):
                return True
    return False


# Validate one polygon coordinate object against image dimensions.
def validate_polygon(
    coordinate: dict[str, Any], image_width: Any, image_height: Any
) -> list[dict[str, str]]:
    x_coordinates = coordinate.get("x")
    y_coordinates = coordinate.get("y")
    if not isinstance(x_coordinates, list) or not isinstance(y_coordinates, list):
        return [{"severity": "ERROR", "code": "non_numeric_coordinate"}]

    if len(x_coordinates) != len(y_coordinates):
        return [{"severity": "ERROR", "code": "coordinate_count_mismatch"}]

    point_count = len(x_coordinates)
    if point_count == 0:
        return [{"severity": "ERROR", "code": "empty_polygon"}]
    if point_count < 3:
        return [{"severity": "ERROR", "code": "insufficient_points"}]

    coordinates = x_coordinates + y_coordinates
    if any(type(value) not in (int, float) for value in coordinates):
        return [{"severity": "ERROR", "code": "non_numeric_coordinate"}]

    issues = []
    if any(value < 0 for value in coordinates):
        issues.append({"severity": "WARNING", "code": "negative_coordinate"})

    if (
        isinstance(image_width, (int, float))
        and isinstance(image_height, (int, float))
        and (
            any(value > image_width for value in x_coordinates)
            or any(value > image_height for value in y_coordinates)
        )
    ):
        issues.append({"severity": "WARNING", "code": "out_of_bounds_coordinate"})

    points = list(zip(x_coordinates, y_coordinates))
    if _has_self_intersection(points):
        issues.append({"severity": "INFO", "code": "possible_self_intersection"})

    return issues


# Report duplicate coordinate lists once for an image.
def validate_duplicate_annotations(
    annotations: list[dict[str, Any]],
) -> list[dict[str, str]]:
    coordinates_seen = []
    for annotation in annotations:
        coordinate = annotation["coordinate"]
        coordinate_key = (coordinate["x"], coordinate["y"])
        if coordinate_key in coordinates_seen:
            return [{"severity": "WARNING", "code": "duplicate_annotation"}]
        coordinates_seen.append(coordinate_key)
    return []
