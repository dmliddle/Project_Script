
# Import necessary modules
import arcpy
import os
import sys

#Import the Path function
from pathlib import Path
from arcpy.sa import Idw
# Define the scratch folder
scratch_folder = Path.cwd()
# Define the root folder
root_folder = scratch_folder.parent

# Define the data folder
data_folder = root_folder / "Data"

coral_data = str(root_folder / 'Data' / 'Processed' / 'coral_data_filtered.shp')


# Define output workspace
output_workspace = str(scratch_folder)
arcpy.env.workspace = output_workspace
arcpy.env.overwriteOutput = True

# User-defined inputs
selected_year = input("Enter the year to filter by (e.g., 2020): ")

try:
    # Create a temporary layer
    arcpy.MakeFeatureLayer_management(coral_data, "coral_layer")

    # Apply SQL query to filter rows by the selected year
    sql_query = f"Date_Year = {selected_year}"  # Date_Year is a Long (numeric)
    arcpy.SelectLayerByAttribute_management("coral_layer", "NEW_SELECTION", sql_query)

    # Ensure there are records selected
    if int(arcpy.GetCount_management("coral_layer")[0]) == 0:
        raise ValueError(f"No records found for year {selected_year}.")

    print(f"Records found for year {selected_year}. Proceeding with interpolation...")

    # Interpolation (IDW)
    tsa_dhw_field = "TSA_DHW"  # Double (numeric)
    cell_size = 10  # Adjust based on your raster resolution

    # Perform IDW interpolation
    idw_output = Idw(
        in_point_features="coral_layer",
        z_field=tsa_dhw_field,
        cell_size=cell_size,
        power=2  # Adjust power as needed
    )

    # Save the output raster
    output_raster = str(output_workspace / f"TSA_DHW_Interpolated_{selected_year}.tif")
    idw_output.save(output_raster)

    print(f"Interpolation completed. Output saved to {output_raster}")

except Exception as e:
    print(f"An error occurred: {e}")

finally:
    # Clean up
    arcpy.Delete_management("coral_layer")