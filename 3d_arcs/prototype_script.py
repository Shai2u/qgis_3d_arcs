# Import necessary QGIS modules
from qgis.core import QgsProject, QgsGeometry, QgsVectorLayer, QgsField, QgsFeature, QgsPoint, QgsPointXY, QgsVectorFileWriter
from qgis.PyQt.QtCore import QVariant
import numpy as np

def generate_arc(x1, y1, x2, y2, segments, y_angle, z_scale):
    # Define the EPSG code
    epsg_code = 3857

    # Define the two points
    point1 = QgsPoint(x1, y1)
    point2 = QgsPoint(x2, y2)

    # Calculate the center point for the circle
    # Create a vector layer to store the line
    line_layer = QgsVectorLayer("LineString?crs=EPSG:3857", "Line", "memory")
    provider = line_layer.dataProvider()
    provider.addAttributes([QgsField("Name", QVariant.String)])
    line_layer.updateFields()
    line_geometry = QgsGeometry.fromPolyline([point1, point2])

    # Get the center coordinate
    center_point = QgsGeometry.fromPointXY(line_geometry.centroid().asPoint())

    # Get the origin coordinate
    origin = QgsGeometry.fromPointXY(QgsPointXY(0, 0))

    # Specify the radius for the circle
    radius = int(line_geometry.length()/2)

    # Create the circle polygon
    circle = origin.buffer(radius, segments)

    # Populate array with X,Y,Z coordinates
    for i in range(len(circle.asPolygon()[0])):
        point_ = circle.asPolygon()[0][i]
        if i == 0:
            points_array = np.array([[point_.x(), point_.y(), 0.0]])
        else:
            points_array = np.append(points_array, np.array([[point_.x(), point_.y(), 0.0]]), axis=0)


    # Define rotation angles in radians
    angle_x = np.radians(0)  # Rotation around Y-axis

    angle_y = np.radians(y_angle)  # Rotation around Y-axis

    # Calculate the bearing between the two points
    bearing = point2.azimuth(point1)

    angle_z = np.radians(bearing)  # Rotation around Z-axis

    # Apply the rotation around Y-axis (using the standard 3D rotation matrix)
    rotation_x = np.array([
        [1, 0, 0, 0],
        [0, np.cos(angle_x), -np.sin(angle_x), 0],
        [0, np.sin(angle_x), np.cos(angle_x), 0],
        [0, 0, 0, 1]
    ])

    rotation_y = np.array([
        [np.cos(angle_y), 0, np.sin(angle_y), 0],
        [0, 1, 0, 0],
        [-np.sin(angle_y), 0, np.cos(angle_y), 0],
        [0, 0, 0, 1]
    ])

    # Apply the rotation around Z-axis (using the standard 3D rotation matrix)
    rotation_z = np.array([
        [np.cos(angle_z), -np.sin(angle_z), 0, 0],
        [np.sin(angle_z), np.cos(angle_z), 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
    ])

    # Apply scaling along the Z-axis
    scaling_z = np.array([
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, z_scale, 0],
        [0, 0, 0, 1]
    ])
    inverse_center_translation = np.array([
        [1, 0, 0, center_point.asPoint().x()],
        [0, 1, 0, center_point.asPoint().y()],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
    ])

    points_array = np.hstack([points_array, np.ones((points_array.shape[0], 1))])
    # Apply the transformation to the points
    transformed_points = np.dot(points_array, rotation_y)


    # get only positive points
    transformed_points = transformed_points[transformed_points[:,2]>=-0.1]

    # Sort by Y and remove duplicates
    unique_data = np.unique(transformed_points, axis=0)
    sorted = unique_data[unique_data[:,1].argsort()]

    # Continue transformation
    transformed_points = np.dot(sorted, rotation_z)
    transformed_points = np.dot(transformed_points, scaling_z)
    transformed_points = transformed_points.dot(inverse_center_translation.T)


    stacked_array = transformed_points
    # TODO add 0 and last point

    # Create a list of 3D points (replace with your own coordinates)
    polyline_points = []
    for i in range(stacked_array.shape[0]):
        x = stacked_array[i][0]
        print(x)
        y = stacked_array[i][1]
        z = stacked_array[i][2]
        polyline_points.append(QgsPoint(x, y, z))

    # Create a QgsGeometry for the 3D polyline
    polyline = QgsGeometry.fromPolyline(polyline_points)

    # Create a memory vector layer to store the 3D polyline
    polyline_layer = QgsVectorLayer(f"LineStringZ?crs=EPSG:{epsg_code}", "Polyline 3D", "memory")
    provider = polyline_layer.dataProvider()
    provider.addAttributes([QgsField("Name", QVariant.String)])
    polyline_layer.updateFields()
    polyline_layer.startEditing()

    # Create a feature with the 3D polyline
    feature = QgsFeature()
    feature.setGeometry(polyline)
    feature.setAttributes(["Line"])

    # Add the feature to the layer
    provider.addFeatures([feature])

    # Update the layer's extent
    polyline_layer.updateExtents()
    polyline_layer.commitChanges()
    # Add the layer to the QGIS map canvas (optional)
    QgsProject.instance().addMapLayer(polyline_layer)

    # Refresh the map canvas
    iface.mapCanvas().refresh()


generate_arc(3834358, 3699610, 3877714, 3757735, 10, 90, 0.5)