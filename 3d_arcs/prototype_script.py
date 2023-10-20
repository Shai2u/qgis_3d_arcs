# Import necessary QGIS modules
from qgis.core import QgsProject, QgsGeometry, QgsVectorLayer, QgsField, QgsFeature, QgsPoint, QgsPointXY, QgsVectorFileWriter
from qgis.PyQt.QtCore import QVariant
import numpy as np

# Define the EPSG code
epsg_code = 3857

# Create a new memory layer with EPSG 3857
layer_name = "Arc"
point_layer = QgsVectorLayer(f"Point?crs=EPSG:{epsg_code}", layer_name, "memory")
provider = point_layer.dataProvider()

# Add fields for attributes if needed
provider.addAttributes([QgsField("Name", QVariant.String)])
point_layer.updateFields()

# Define the two points
# point1 = QgsGeometry.fromPointXY(QgsPointXY(3834358, 3699610))
# point2 = QgsGeometry.fromPointXY(QgsPointXY(3877714, 3757735))
point1 = QgsPoint(3834358, 3699610)
point2 = QgsPoint(3877714, 3757735)

# Calculate the center point for the circle
# Create a vector layer to store the line
line_layer = QgsVectorLayer("LineString?crs=EPSG:4326", "Line", "memory")
provider = line_layer.dataProvider()
provider.addAttributes([QgsField("Name", QVariant.String)])
line_layer.updateFields()
line_geometry = QgsGeometry.fromPolyline([point1, point2])


# Create a feature for the line
feature = QgsFeature()
feature.setGeometry(line_geometry)
feature.setAttributes(["Line"])
line_layer.dataProvider().addFeatures([feature])

# Add the layer to the project
QgsProject.instance().addMapLayer(line_layer)

# Get the center coordinate
center_point = QgsGeometry.fromPointXY(line_geometry.centroid().asPoint())

# Get the origin coordinate
origin = QgsGeometry.fromPointXY(QgsPointXY(0, 0))

# Specify the radius for the circle (adjust as needed)


# Calculate the distance between the two points
# distance_area = QgsDistanceArea()
# distance = distance_area.measureLine(point1, point2)
radius = int(line_geometry.length()/2)

# Create the circle polygon
circle = origin.buffer(radius,5)



for i in range(len(circle.asPolygon()[0])):
    point_ = circle.asPolygon()[0][i]
    if i == 0:
        points_array = np.array([[point_.x(), point_.y(), 0.0]])
    else:
        points_array = np.append(points_array, np.array([[point_.x(), point_.y(), 0.0]]), axis=0)


# Define rotation angles in radians
angle_x = np.radians(90)  # Rotation around Y-axis

angle_y = np.radians(90)  # Rotation around Y-axis

# get bearing
angle_z = np.radians(45)  # Rotation around Z-axis

# center_translation = np.array([
#     [1, 0, 0, -1 * center_point.asPoint().x()],
#     [0, 1, 0, -1 * center_point.asPoint().y()],
#     [0, 0, 1, 0],
#     [0, 0, 0, 1]
# ])

# Apply the rotation around Y-axis (using the standard 3D rotation matrix)

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
    [0, 0, 0.75, 0],
    [0, 0, 0, 1]
])
inverse_center_translation = np.array([
    [1, 0, 0, center_point.asPoint().x()],
    [0, 1, 0, center_point.asPoint().y()],
    [0, 0, 1, 0],
    [0, 0, 0, 1]
])
# Combine the rotations and scaling
# matrix = rotation_y.dot(rotation_z).dot(inverse_center_translation)
matrix = rotation_y.dot(inverse_center_translation)

points_array = np.hstack([points_array, np.ones((points_array.shape[0], 1))])
# Apply the transformation to the points
# transformed_points = points_array.dot(matrix.T)
# transformed_points = np.dot(points_array, np.dot(rotation_y,rotation_z).T)
# transformed_points = np.dot(points_array, np.dot(np.dot(rotation_x,rotation_y), rotation_z).T)
transformed_points = np.dot(points_array, rotation_x.T)
# transformed_points = np.dot(points_array, rotation_y.T)
transformed_points = np.dot(points_array, rotation_z.T)

# get only positive points
# transformed_points = transformed_points[transformed_points[:,2]>0]
# transformed_points = transformed_points.dot(inverse_center_translation.T)

# Drop the last column
transformed_points = transformed_points[:, :-1]
# TODO add 0 and last point

# Create a new feature and set its geometry
feature = QgsFeature()
feature.setGeometry(circle)

polygon_layer = QgsVectorLayer(f"Polygon?crs=EPSG:{epsg_code}", "Buffer Layer", "memory")
provider = polygon_layer.dataProvider()

# Add attributes to the buffer layer (if needed)
provider.addAttributes([QgsField("Name", QVariant.String)])
polygon_layer.updateFields()

# Add the feature to the layer
polygon_layer.startEditing()

buffer_feature = QgsFeature()
buffer_feature.setGeometry(circle)
buffer_feature.setAttributes(["buffer"])


polygon_layer.addFeature(buffer_feature)


# Commit changes and stop editing
polygon_layer.commitChanges()

# Add the layer to the project
QgsProject.instance().addMapLayer(polygon_layer)


# Create a list of 3D points (replace with your own coordinates)
polyline_points = []
for i in range(transformed_points.shape[0]):
    x = transformed_points[i][0]
    print(x)
    y = transformed_points[i][1]
    z = transformed_points[i][2]
    polyline_points.append(QgsPoint(x, y, z))

# Create a QgsGeometry for the 3D polyline
polyline = QgsGeometry.fromPolyline(polyline_points)

# Create a memory vector layer to store the 3D polyline
polyline_layer = QgsVectorLayer("LineStringZ", "3D Polyline", "memory")
pr = polyline_layer.dataProvider()

# Create a feature with the 3D polyline
feature = QgsFeature()
feature.setGeometry(polyline)

# Add the feature to the layer
pr.addFeatures([feature])

# Update the layer's extent
polyline_layer.updateExtents()

# Add the layer to the QGIS map canvas (optional)
QgsProject.instance().addMapLayer(polyline_layer)

# Save the layer to a file (optional)
output_file = "path_to_output_file.shp"
writer = QgsVectorFileWriter.writeAsVectorFormat(polyline_layer, output_file, "UTF-8", driverName="ESRI Shapefile")

if writer:
    print("3D polyline saved to", output_file)
else:
    print("Failed to save the 3D polyline.")
# Refresh the map canvas
iface.mapCanvas().refresh()

