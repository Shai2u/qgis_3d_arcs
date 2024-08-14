# Import necessary QGIS modules
from qgis.core import QgsProject, QgsGeometry, QgsVectorLayer, QgsField, QgsFeature, QgsPoint, QgsPointXY, QgsCoordinateTransform, QgsCoordinateReferenceSystem
from qgis.PyQt.QtCore import QVariant
import numpy as np

EPSG_3D_CODE = 3857

def rotation_x(rad_angle):
    """
    Perform a rotation around the x-axis.

    Parameters:
    rad_angle (float): The angle of rotation in radians.

    Returns:
    numpy.ndarray: The rotation matrix.

    """
    return np.array([
        [1, 0, 0, 0],
        [0, np.cos(rad_angle), -np.sin(rad_angle), 0],
        [0, np.sin(rad_angle), np.cos(rad_angle), 0],
        [0, 0, 0, 1]
    ])


def rotation_y(rad_angle):
    """
    Perform a rotation around the y-axis.

    Parameters:
    rad_angle (float): The angle of rotation in radians.

    Returns:
    numpy.ndarray: The rotation matrix.

    """
    return np.array([
        [np.cos(rad_angle), 0, np.sin(rad_angle), 0],
        [0, 1, 0, 0],
        [-np.sin(rad_angle), 0, np.cos(rad_angle), 0],
        [0, 0, 0, 1]
    ])

def rotation_z(rad_angle):
    """
    Perform a rotation around the z-axis.

    Parameters:
    rad_angle (float): The angle of rotation in radians.

    Returns:
    numpy.ndarray: The rotation matrix.

    """
    return np.array([
        [np.cos(rad_angle), -np.sin(rad_angle), 0, 0],
        [np.sin(rad_angle), np.cos(rad_angle), 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
    ])

def scale_z(scale_: float) -> np.ndarray:
    """
    Perform a scaling along the z-axis.

    Parameters:
    scale_ (float): The scaling factor.

    Returns:
    numpy.ndarray: The scaling matrix.

    """
    return np.array([
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, scale_, 0],
        [0, 0, 0, 1]
    ])

def translate(x: float, y: float) -> np.ndarray:
    """
    Perform a translation in 3D space.

    Parameters:
    x (float): The translation distance along the x-axis.
    y (float): The translation distance along the y-axis.

    Returns:
    numpy.ndarray: The translation matrix.

    """
    return np.array([
        [1, 0, 0, x],
        [0, 1, 0, y],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
    ])

def create_3d_empty_layer_from_layer(layer):
    """
    Create a 3D empty layer from an existing layer.

    Parameters:
    layer (QgsVectorLayer): The input layer.

    Returns:
    QgsVectorLayer: The 3D empty layer.

    """
    # Create a memory vector layer to store the 3D polyline
    layer_3d = QgsVectorLayer(f"LineStringZ?crs=EPSG:{EPSG_3D_CODE}", layer.name(), "memory")
    provider = layer_3d.dataProvider()
    provider.addAttributes([QgsField(field.name(), field.type()) for field in layer.fields()])
    layer_3d.updateFields()
    return layer_3d

def generate_arc_qpoints_from_geometry(geometry_: QgsGeometry, segments: int, y_angle: float, z_scale: float) -> list[QgsPoint]:
    """
    Generate 3D points along an arc based on the input line geometry.

    Parameters:
    geometry_ (QgsGeometry): The input geometry representing the arc.
    segments (int): The number of segments to divide the arc into.
    y_angle (float): The angle of rotation around the y-axis.
    z_scale (float): The scaling factor along the z-axis.

    Returns:
    List[QgsPoint]: The list of 3D points representing the arc.

    """
    # Define the start and end points of the line
    start_point = QgsPoint(geometry_.asPolyline()[0])
    end_point = QgsPoint(geometry_.asPolyline()[-1])

    # Get the center point of the arc
    center_point = QgsGeometry.fromPointXY(geometry_.centroid().asPoint())

    # Create a circle polygon with the specified radius
    radius = int(geometry_.length() / 2)
    circle = QgsGeometry.fromPointXY(QgsPointXY(0, 0)).buffer(radius, segments)

    # Create an empty array to store the X, Y, Z coordinates
    points_array = np.array([[point.x(), point.y(), 0.0] for point in circle.asPolygon()[0]])

    # Calculate the bearing between the start and end points
    bearing = end_point.azimuth(start_point)

    # Apply transformations to the points
    points_array = np.hstack([points_array, np.ones((points_array.shape[0], 1))])
    transformed_points = np.dot(points_array, rotation_y(np.radians(90)))
    transformed_points = transformed_points[transformed_points[:, 2] >= -0.1]
    unique_data = np.unique(transformed_points, axis=0)
    sorted_points = unique_data[unique_data[:, 1].argsort()]
    transformed_points = np.dot(sorted_points, rotation_y(np.radians(y_angle - 90)))
    transformed_points = np.dot(transformed_points, rotation_z(np.radians(bearing)))
    transformed_points = np.dot(transformed_points, scale_z(z_scale))
    transformed_points = transformed_points.dot(translate(center_point.asPoint().x(), center_point.asPoint().y()).T)

    # Create a list of QgsPoint objects from the transformed points
    QgsPoint_list = []
    for i in range(transformed_points.shape[0]):
        x = transformed_points[i][0]
        y = transformed_points[i][1]
        z = transformed_points[i][2]
        QgsPoint_list.append(QgsPoint(x, y, z))
    return QgsPoint_list

def append_geometry_data_to_3d_arc(layer_3d: QgsVectorLayer, QgsPoint_list: list[QgsPoint], feature: QgsFeature) -> QgsVectorLayer:
    """
    Append geometry data to a 3D arc layer.

    Parameters:
    layer_3d (QgsVectorLayer): The 3D arc layer.
    QgsPoint_list (List[QgsPoint]): The list of 3D points representing the arc.
    feature (QgsFeature): The input feature.

    Returns:
    QgsVectorLayer: The updated 3D arc layer.

    """
    provider = layer_3d.dataProvider()

    # Create a QgsGeometry for the 3D polyline
    polyline = QgsGeometry.fromPolyline(QgsPoint_list)

    layer_3d.startEditing()

    # Create a feature with the 3D polyline
    new_feature = QgsFeature()
    new_feature.setGeometry(polyline)
    
    # Set attribute values for the new feature
    attributes_ = [feature[field_name] for field_name in layer_3d.fields().names()]

    new_feature.setAttributes(attributes_)
        
            
    # Add the feature to the layer
    provider.addFeatures([new_feature])

    layer_3d.updateExtents()
    layer_3d.commitChanges()
    
    # Return the updated layer
    return layer_3d

def reproject_layer(layer):
    """
    Reproject a layer to the target CRS.

    Parameters:
    layer (QgsVectorLayer): The input layer to be reprojected.

    Returns:
    QgsVectorLayer: The reprojected layer.

    """
    if not str(EPSG_3D_CODE) in layer.crs().authid():

        # Define the target CRS
        target_crs = QgsCoordinateReferenceSystem(EPSG_3D_CODE)

        # Create a new layer for the reprojected data
        reprojected_layer = QgsVectorLayer("Point?crs=EPSG:3857", layer.name(), "memory")

        # Get the transform object
        transform = QgsCoordinateTransform(layer.crs(), target_crs, QgsProject.instance())

        # Copy the fields from the original layer to the new one
        provider = reprojected_layer.dataProvider()
        provider.addAttributes([QgsField(field.name(), field.type()) for field in layer.fields()])
        # provider.addAttributes(layer.fields())
        reprojected_layer.updateFields()

        reprojected_layer.startEditing()
        # Reproject each feature and add it to the new layer
        for feature in layer.getFeatures():
            geom = feature.geometry()
            geom.transform(transform)
            reprojected_feature = feature
            reprojected_feature.setGeometry(geom)
            reprojected_layer.addFeature(reprojected_feature)

        reprojected_layer.updateExtents()
        reprojected_layer.commitChanges()
        return reprojected_layer
    else:
        return layer

def main(layer: QgsVectorLayer, segments: int, y_angle: float, z_scale: float) -> QgsVectorLayer:
    """
    Generate a 3D arc layer based on the input layer.

    Parameters:
    layer (QgsVectorLayer): The input layer.
    segments (int): The number of segments to divide the arc into.
    y_angle (float): The angle of rotation around the y-axis.
    z_scale (float): The scaling factor along the z-axis.

    Returns:
    QgsVectorLayer: The 3D arc layer.

    """
    # Create an empty 3D layer based on the input layer
    layer_3d = create_3d_empty_layer_from_layer(layer)

    # Reproject the input layer to EPSG:3857
    layer_rep = reproject_layer(layer)
    # Iterate over each feature in the input layer
    for feature in layer_rep.getFeatures():
        # Generate a list of 3D points representing the arc for the current feature
        QgsPoint_list = generate_arc_qpoints_from_geometry(feature.geometry(), segments, y_angle, z_scale)
        
        # Append the geometry data to the 3D arc layer
        layer_3d = append_geometry_data_to_3d_arc(layer_3d, QgsPoint_list, feature)
    
    # Return the updated 3D arc layer
    return layer_3d

if __name__ == "__main__":
    layer = iface.activeLayer()
    segments, y_angle, z_scale = 10, 90, 0.5
    layer_arc_3d = main(layer, segments, y_angle, z_scale)

    
