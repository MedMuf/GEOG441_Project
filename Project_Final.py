import arcpy
import os
import math

from arcgis.gis import GIS
from arcpy import management as DM

# Allow overwriting outputs
arcpy.env.overwriteOutput = True

project = arcpy.mp.ArcGISProject("CURRENT") #Set project location
default_gdb = project.defaultGeodatabase #Set Geodatabase

path = default_gdb 
arcpy.env.workspace = path

print(arcpy.Exists(path)) #Determine if path exists
print(path)


map_obj = project.activeMap 

# These are examples – you can swap them with other Living Atlas content 
Terrain_items = [
    "58a541efc59545e6b7137f961d7de883"
]

#OSM layers sorted by continent, pulled from Living Atlas
osm_layers_by_continent = {
    "North America": [
        ("OSM_NA_Buildings", "2be4ad6652c649cbaea2be211555b1cf"),
        ("OSM_NA_Highways", "7afec250e02845868db89c83949a672f"),
        ("OSM_NA_Waterways", "7a7d92cef2c442c1a352d902e1f2f577")
    ],
    "South America": [
        ("OSM_SA_Buildings", "9e2de2cd58804a8baf286ac9639cc85f"),
        ("OSM_SA_Highways", "70c79ab73c15445492edecc53dac00c8"),
        ("OSM_SA_Waterways", "22783d44a7b0441c806c2977ff2800f3")
    ],
    "Central America": [
        ("OSM_CA_Buildings", "6b4bd2c5734e471fbc51deb9c5f24298"),
        ("OSM_CA_Highways", "a22dc4dc053e45008157f3bcf2894105"),
        ("OSM_CA_Waterways", "af162bf02efc4296878637a408f560df")
    ],
    "Europe": [
        ("OSM_EU_Buildings", "b9abc540c5524258a673ded17cc5f4f9"),
        ("OSM_EU_Highways", "d243222a50864c47ba97d30572839361"),
        ("OSM_EU_Waterways", "7bf80080749e4806b936c2b39e73b62e")
    ],
    "Africa": [
        ("OSM_AF_Buildings", "bb86721588ea49b6b44b10b7d5d2b0b1"),
        ("OSM_AF_Highways", "6d78851a40f54041a775d7c6f4b2633e"),
        ("OSM_AF_Waterways", "82232d0415c04e7086414dff7eb1310f")
    ],
    "Asia": [
        ("OSM_AS_Buildings", "efcea3961e8e417aae1f341b397684a2"),
        ("OSM_AS_Highways", "af989f50f24040e4890dce13ee1b1561"),
        ("OSM_AS_Waterways", "fb8b1e4383124e4ab51d7729552b0a88")
    ],
    "Australia & Oceania": [
        ("OSM_AU_Buildings", "651512cac36c48ba95c88c380ff8fac5"),
        ("OSM_AU_Highways", "919be41ae8194e65b49c70e2891d9d08"),
        ("OSM_AU_Waterways", "76659f9ea5bf4761b263ffe55f976d1a")
    ]
}



#Function to ask users for continent site
def get_user_layers():
    print("Please select your continent from the following list:")
    for i, continent in enumerate(osm_layers_by_continent.keys(), 1):
        print(f"{i}. {continent}") #Provides list of continents
    
    choice = input("Enter the number corresponding to your continent: ").strip()
    
    try:
        selected_continent = list(osm_layers_by_continent.keys())[int(choice) - 1]
        print(f"\nLoading layers for {selected_continent}:")
        for layer_name, layer_id in osm_layers_by_continent[selected_continent]:
            print(f" - {layer_name} (ID: {layer_id})")
        return osm_layers_by_continent[selected_continent]
    except (IndexError, ValueError):
        print("Invalid selection. Please try again.")
        return get_user_layers()

# Example usage
selected_layers = get_user_layers() #Add layers to list empty variable

print(selected_layers)


for layer_name, item_id in selected_layers:
    # Add the layer from the portal item ID
    url = f"https://www.arcgis.com/home/item.html?id={item_id}"
    layer = map_obj.addDataFromPath(url)
    layer.visible = False

#Add Terrain layer
for item_id in Terrain_items:
    lyr = map_obj.addDataFromPath(f"https://www.arcgis.com/home/item.html?id={item_id}")
    if lyr:
        lyr.visible = False




#Experiment for grouping them 
'''
# Iterate through each continent
for continent, layers in osm_layers_by_continent.items():
    # Create a group layer for the continent
    continent_group = map_obj.createGroupLayer(continent)

    for layer_name, item_id in layers:
        # Add the layer from the portal item ID
        url = f"https://www.arcgis.com/home/item.html?id={item_id}"
        layer = map_obj.addDataFromPath(url)
        
        # Add the layer into the continent group
        map_obj.addLayerToGroup(continent_group, layer, "AUTO_ARRANGE")
        map_obj.removeLayer(layer)

for item_id in Terrain_items:
    lyr = map_obj.addDataFromPath(f"https://www.arcgis.com/home/item.html?id={item_id}")
    if lyr:
        lyr.visible = False
'''

     

# User input: latitude and longitude
latitude = float(input("Enter latitude: ")) #Example: 35.289761
longitude = float(input("Enter longitude: ")) #Example:  -120.673041
area = float(input("Enter Polygon side length (km): ")) #AOI side length input

# Coordinate system (WGS 84 for lat/lon input)
spatial_ref_wgs84 = arcpy.SpatialReference(4326)  # WGS 1984

# Create the point geometry
point = arcpy.Point(longitude, latitude)
point_geom = arcpy.PointGeometry(point, spatial_ref_wgs84)

# Project the point to a projected coordinate system that uses meters 
spatial_ref_projected = arcpy.SpatialReference(3857)  # Web Mercator (meters)
projected_point = point_geom.projectAs(spatial_ref_projected)

# Get x, y from projected point
x = projected_point.centroid.X
y = projected_point.centroid.Y

half_side = (area * 1000)/2  

# Define corners
array = arcpy.Array([
    arcpy.Point(x - half_side, y - half_side),
    arcpy.Point(x - half_side, y + half_side),
    arcpy.Point(x + half_side, y + half_side),
    arcpy.Point(x + half_side, y - half_side),
    arcpy.Point(x - half_side, y - half_side)  # Close polygon
])

square_polygon = arcpy.Polygon(array, spatial_ref_projected)

arcpy.CopyFeatures_management(square_polygon, "AOI")


# Find the "AOI" layer you just created
layer = None
for lyr in map_obj.listLayers():
    if lyr.name == "AOI":
        layer = lyr
        break

if layer is not None:
    sym = layer.symbology

    # Make sure it uses a simple fill symbology
    if hasattr(sym, 'renderer'):
        sym.updateRenderer('SimpleRenderer')
        symbol = sym.renderer.symbol

        # Set fill to transparent
        symbol.color = {'RGB': [0, 0, 0, 0]}  # Transparent

        # Set outline to black, 2pt
        symbol.outlineColor = {'RGB': [0, 0, 0, 100]}  # Fully opaque black
        symbol.outlineWidth = 2  # Points

        # Apply changes
        layer.symbology = sym

square_polygon.extent

#List created to be used for layer exclusion in copy features step
excluded_names = ["Terrain", "World Topographic Map", "World Hillshade", "AOI"]


dic = [layer.name for layer in map_obj.listLayers()]

#List to be used for copy features chunk
dict = [x for x in dic if x not in excluded_names]

print(dict)



with arcpy.EnvManager(extent = square_polygon.extent):
            for i in dict: #Iterating through list from earlier  to be copied to AOI extent
                arcpy.management.CopyFeatures(
                    in_features = i,
                    out_feature_class = i + "Clipped",
                    config_keyword = "",
                    spatial_grid_1 = None,
                    spatial_grid_2 = None,
                    spatial_grid_3 = None
            )


raster_input = "Terrain"  
polygon = "AOI"
output_raster = "Terrain_clipped.tif"

# Max pixels allowed
max_pixels = 5000

# Get polygon extent
extent = arcpy.Describe(polygon).extent
xrange = extent.width
yrange = extent.height

# Compute cell size to stay under limit
cell_size = max(xrange / max_pixels, yrange / max_pixels)

print(f"Using calculated cell size: {cell_size}") #Cell size lengths would be in meters. 

# Set the cell size environment for the masking process
arcpy.env.cellSize = cell_size

# Perform Extract by Mask (or Clip)
clipped_AOI = arcpy.sa.ExtractByMask(raster_input, polygon)



ipt = str(input("What do unit do you want for contours (feet/meters):")) #Ask for contour unit
cont = int(input("What contour interval would you like:")) #Ask for contour interval

if ipt == "feet": #Set the z factor to adjust if the user wants a contour interval of feet
    z = 3.28 #Conversion factor for if user wants feet as terrain layer is in meters
else:
    z = 1

#Create contours
arcpy.sa.Contour(
    in_raster = "clipped_AOI",
    out_polyline_features = r"AOI_Contours",
    contour_interval = cont,
    base_contour = 0,
    z_factor = z,
    contour_type = "CONTOUR",
    max_vertices_per_feature = None
)

#Smooth contours to adjust for pixilation 
arcpy.cartography.SmoothLine(
    in_features = "AOI_Contours",
    out_feature_class = "smooth_AOI_contours",
    algorithm = "PAEK",  
    tolerance = "10"  # Adjust based on desired smoothness
)

        

#Used to determine and calculated the z tolerance needed to create TIN
elevMINres = arcpy.GetRasterProperties_management("clipped_AOI", "MINIMUM")
elevMAXres = arcpy.GetRasterProperties_management("clipped_AOI", "MAXIMUM")

elevMin = float(elevMINres.getOutput(0))
elevMax = float(elevMAXres.getOutput(0))

z_tol = (elevMax - elevMin) / 10

#Create TIN
arcpy.ddd.RasterTin(
    in_raster = "clipped_AOI",
    out_tin = r"clipped_AOI_RasterTin",
    z_tolerance = z_tol,
    max_points = 1500000, #Can be adjusted, higher number, more "accurate"
    z_factor = z
)

#Generate TIN domain
#Is the "interpolation" zone for which the tin layer will be placed on
arcpy.ddd.TinDomain(
    in_tin = "clipped_AOI_RasterTin",
    out_feature_class = "TinDomain",
    out_geometry_type = "POLYGON"
)

#Create mesh layer to fit to Clipped Raster layer
arcpy.ddd.InterpolatePolyToPatch(
    in_surface = "clipped_AOI_RasterTin",
    in_feature_class = "TinDomain",
    out_feature_class = r"Mesh",
    max_strip_size = 1024,
    z_factor = 1, #Don't use z variable as we don't want to scale it twice (if in feet)
    area_field = "Area",
    surface_area_field = "SArea",
    pyramid_level_resolution= z_tol
)

#Smooted contours layer used to match the elevations of the mesh and clipped raster layer

'''
arcpy.ddd.InterpolateShape(
    in_surface = "clipped_AOI",
    in_feature_class = "smooth_AOI_contours",
    out_feature_class = r"clipped_AOI_Interpolate_Cont",
    sample_distance = None,
    z_factor = z,
    method = "BILINEAR",
    vertices_only = "DENSIFY",
    pyramid_level_resolution = 0,
    preserve_features = "EXCLUDE"
)
'''


excluded_names_final = ["Terrain", "World Topographic Map", "World Hillshade", 'AOI_Contours', 'TinDomain', 'OSM_Waterways_EU', 'OSM_Highways_EU', 'OSM_Buildings_EU', 'clipped_AOI', 'clipped_AOI_RasterTin']


dic_final = [layer.name for layer in map_obj.listLayers()]
dict_export = [x for x in dic_final if x not in excluded_names_final]
print(dict_export)

#Export files to dwg file
arcpy.conversion.ExportCAD(
    in_features=dict_export,
    Output_Type="DWG_R2018",
    Output_File="clipped_AOI_CAD.dwg",
    Ignore_FileNames="Ignore_Filenames_in_Tables",
    Append_To_Existing="Overwrite_Existing_Files",
    Seed_File=None
)


