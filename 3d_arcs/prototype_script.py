# Import necessary QGIS modules
from qgis.core import QgsProject, QgsGeometry, QgsVectorLayer, QgsField, QgsFeature, QgsPoint, QgsPointXY, QgsVectorFileWriter
from qgis.PyQt.QtCore import QVariant
import numpy as np

def rotation_x(rad_angle):
    return  np.array([
        [1, 0, 0, 0],
        [0, np.cos(rad_angle), -np.sin(rad_angle), 0],
        [0, np.sin(rad_angle), np.cos(rad_angle), 0],
        [0, 0, 0, 1]
    ])


def rotation_y(rad_angle):
    return np.array([
        [np.cos(rad_angle), 0, np.sin(rad_angle), 0],
        [0, 1, 0, 0],
        [-np.sin(rad_angle), 0, np.cos(rad_angle), 0],
        [0, 0, 0, 1]
    ])

def rotation_z(rad_angle):
    return np.array([
        [np.cos(rad_angle), -np.sin(rad_angle), 0, 0],
        [np.sin(rad_angle), np.cos(rad_angle), 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
    ])

def scale_z(scale_):
    return np.array([
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, scale_, 0],
        [0, 0, 0, 1]
    ])

def translate(x, y):
    return np.array([
        [1, 0, 0, x],
        [0, 1, 0, y],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
    ])

def generate_arc(layer, x1, y1, x2, y2, segments, y_angle, z_scale, location):
    # Define the EPSG code
    epsg_code = 3857

    # Define the two points
    point1 = QgsPoint(x1, y1)
    point2 = QgsPoint(x2, y2)

    # Calculate the center point for the circle
    # Create a vector layer to store the line
    #line_layer = QgsVectorLayer(f"LineString?crs=EPSG:{epsg_code}", "Line", "memory")
    provider = layer.dataProvider()

    line_geometry = QgsGeometry.fromPolyline([point1, point2])

    # Get the center coordinate
    center_point = QgsGeometry.fromPointXY(line_geometry.centroid().asPoint())

    # Get the origin coordinate
    origin = QgsGeometry.fromPointXY(QgsPointXY(0, 0))

    # Specify the radius for the circle
    radius = int(line_geometry.length()/2)

    # Create the circle polygon
    circle = origin.buffer(radius, segments)

    points_array = np.array([])
    # Populate array with X,Y,Z coordinates
    for i in range(len(circle.asPolygon()[0])):
        point_ = circle.asPolygon()[0][i]
        if i == 0:
            points_array = np.array([[point_.x(), point_.y(), 0.0]])
        else:
            points_array = np.append(points_array, np.array([[point_.x(), point_.y(), 0.0]]), axis=0)


    # Calculate the bearing between the two points
    bearing = point2.azimuth(point1)

    points_array = np.hstack([points_array, np.ones((points_array.shape[0], 1))])
    # Apply the transformation to the points
    transformed_points = np.dot(points_array, rotation_y(np.radians(90)))

    # get only positive points
    transformed_points = transformed_points[transformed_points[:,2]>=-0.1]

    # Sort by Y and remove duplicates
    unique_data = np.unique(transformed_points, axis=0)
    sorted = unique_data[unique_data[:,1].argsort()]
    transformed_points = np.dot(sorted, rotation_y(np.radians(y_angle - 90)))

    # Continue transformation
    transformed_points = np.dot(transformed_points, rotation_z(np.radians(bearing)))
    
    # Scale arc in z axis
    transformed_points = np.dot(transformed_points, scale_z(z_scale))
    transformed_points = transformed_points.dot(translate(center_point.asPoint().x(), center_point.asPoint().y()).T)

    stacked_array = transformed_points
    # TODO add 0 and last point

    # Create a list of 3D points (replace with your own coordinates)
    polyline_points = []
    for i in range(stacked_array.shape[0]):
        x = stacked_array[i][0]
        y = stacked_array[i][1]
        z = stacked_array[i][2]
        polyline_points.append(QgsPoint(x, y, z))

    # Create a QgsGeometry for the 3D polyline
    polyline = QgsGeometry.fromPolyline(polyline_points)

    # # Create a memory vector layer to store the 3D polyline
    # layer = QgsVectorLayer(f"LineStringZ?crs=EPSG:{epsg_code}", "Polyline 3D", "memory")
    provider = layer.dataProvider()
    # provider.addAttributes(fields)
    # layer.updateFields()
    layer.startEditing()

    # Create a feature with the 3D polyline
    feature = QgsFeature()
    feature.setGeometry(polyline)
    feature.setAttributes([ location, x1, y1, x2, y2])

    # Add the feature to the layer
    provider.addFeatures([feature])

    # Update the layer's extent
    layer.updateExtents()
    layer.commitChanges()
    # Add the layer to the QGIS map canvas (optional)


    # Refresh the map canvas
    #iface.mapCanvas().refresh()
    print('completed appending')
    return layer


def generate_arc_layer(layer_name):
    fields = [
        # QgsField('date', QVariant.DateTime),
        QgsField('location', QVariant.String),
        QgsField('east', QVariant.Int),
        QgsField('north', QVariant.Int),
        QgsField('east_g', QVariant.Int),
        QgsField('north_g', QVariant.Int)
    ]
    epsg_code = 3857
    # Create a memory vector layer to store the 3D polyline
    polyline_layer = QgsVectorLayer(f"LineStringZ?crs=EPSG:{epsg_code}", layer_name, "memory")
    provider = polyline_layer.dataProvider()
    provider.addAttributes(fields)
    polyline_layer.updateFields()
    return polyline_layer

layer = generate_arc_layer('Missles to Israel')

# Define the path to your Excel file
# csv_file_path = '/Users/shai/Documents/Projects/qgis_3d_arcs/sample/israel_rockets_with_random_launch_3857_2023_09_09_2023_10_20.csv'
layer_input = '/Users/shai/Documents/Projects/qgis_3d_arcs/sample/example_lines_with_length.geojson'

# Load the Excel file as a QgsVectorLayer
# csv_layer = QgsVectorLayer(f'{csv_file_path}', 'CSV Layer', 'ogr')
polyline_layer = QgsVectorLayer(f'{layer_input}', 'input Layer', 'ogr')

# Get the field names
# field_names = csv_layer.fields().names()

count = 0
for feature in polyline_layer.getFeatures():
    #features = [feature for feature in polyline_layer.getFeatures()]
    #feature = features[0]
    first_point = feature.geometry().asPolyline()[0]
    last_point = feature.geometry().asPolyline()[-1]
    x1 = first_point.x()
    y1 = first_point.y()

    x2 = last_point.x()
    y2 = last_point.y()
    location = feature['locations']
    # date_time = str(feature['date_time'])
    segments, y_angle, z_scale = 10, 90, 0.5
    layer = generate_arc(layer, int(x1), int(y1), int(x2), int(y2), segments, y_angle, z_scale, location)
    #count += 1
    #if count >3:
    #    break

QgsProject.instance().addMapLayer(layer)

# for feature in vecotr_layer.getFeatures():
#     x1 = feature['east']
#     y1 = feature['north']
#     x2 = feature['east_g']
#     y2 = feature['north_g']
#     location = feature['locations']
#     date_time = feature['date_time']
#     layer = generate_arc(layer, int(x1), int(y1), int(x2), int(y2), 10, 90, 0.5, location, date_time)


# Iterate through features and retrieve data
# for feature in csv_layer.getFeatures():
#     x1 = feature['east']
#     y1 = feature['north']
#     x2 = feature['east_g']
#     y2 = feature['north_g']
#     location = feature['locations']
#     date_time = feature['date_time']
#     layer = generate_arc(layer, int(x1), int(y1), int(x2), int(y2), 10, 90, 0.5, location, date_time)



#     QgsProject.instance().addMapLayer(layer)

# create the layer first then iterate the rows and generate the features and add them to the layer
