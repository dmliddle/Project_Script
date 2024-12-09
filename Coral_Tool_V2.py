
# Import necessary modules
import arcpy
import os
import sys
import pandas as pd

# Import the Path function
from pathlib import Path
# Import necessary ArcPy tools
from arcpy.sa import SplineWithBarriers, Con

# Enable output overwrite
arcpy.env.overwriteOutput = True

# Define the root folder
root_folder = scratch_folder.parent
# Define the scratch folder
scratch_folder = root_folder / "Scratch"
# Define the data folder
data_folder = root_folder / "Data"

coral_data = str(root_folder / 'Data' / 'Processed' / 'coral_data_filtered.shp')

# Define output workspace
output_workspace = str(scratch_folder)
arcpy.env.workspace = output_workspace
arcpy.env.overwriteOutput = True


# Loop through each year
for year in range(2002, 2017):  # Includes 2016
    print(f"Processing year: {year}")
    
    # Filter the input data by year
    yearly_data = arcpy.management.MakeFeatureLayer(
        coral_data, f"yearly_data_{year}", f"Date_Year = {year}"
    )
    
    # Generate output names for this year
    bounding_geometry_output = f"coral_bounds_{year}"
    spline_raster = f"v:\\Final_Project\\Scratch\\coral_bleach_spline_{year}.tif"
    con_raster = f"v:\\Final_Project\\Scratch\\Con_coral_bleach_{year}.tif"
    clipped_raster = f"v:\\Final_Project\\Scratch\\Clipped_coral_bleach_{year}.tif"

    # Step 1: Create Minimum Bounding Geometry
    arcpy.management.MinimumBoundingGeometry(
        in_features=yearly_data, 
        out_feature_class=bounding_geometry_output, 
        geometry_type="CONVEX_HULL", 
        group_option="ALL", 
        mbg_fields_option="NO_MBG_FIELDS"
    )
    
    print(f"Created bounding geometry for year {year}.")
    
    # Step 2: Perform Spline with Barriers
    spline_result = SplineWithBarriers(
        yearly_data, "Percent_Bl", bounding_geometry_output, 
        "2.29812000000002E-02", 0  # Spline parameters
    )
    spline_result.save(spline_raster)
    
    print(f"Created spline raster for year {year}.")
    
    # Step 3: Remove Negative Values with Con
    con_result = Con(
        spline_result, 0, spline_result, "VALUE < 0"
    )
    con_result.save(con_raster)
    
    print(f"Corrected raster for year {year}.")
    
        # Step 4: Clip the Raster by Bounding Geometry
    arcpy.sa.ExtractByMask(con_raster, bounding_geometry_output).save(clipped_raster)
    print(f"Clipped raster saved for year {year}.")

    # Clean up the temporary layer
    arcpy.management.Delete(f"yearly_data_{year}")

print("Processing complete!")

# User inputs coordinates
x_coord = float(input("Enter the X coordinate (Longitude): "))
y_coord = float(input("Enter the Y coordinate (Latitude): "))

# Create a temporary point feature class for the input coordinates
temp_point = "in_memory\\temp_point"
arcpy.management.CreateFeatureclass("in_memory", "temp_point", "POINT", spatial_reference=4326)
with arcpy.da.InsertCursor(temp_point, ["SHAPE@XY"]) as cursor:
    cursor.insertRow([(x_coord, y_coord)])

# Initialize results dictionary
results = {"Year": [], "Bleaching_Percentage": []}

# Loop through rasters for each year
for year in range(2002, 2017):  # Includes 2016
    print(f"Processing year: {year}")
    
    raster_path = f"v:\\Final_Project\\Scratch\\Clipped_coral_bleach_{year}.tif"
    
    if arcpy.Exists(raster_path):
        # Extract raster value at the location
        try:
            extracted_point = arcpy.sa.ExtractValuesToPoints(temp_point, raster_path, "in_memory\\extracted_point")
            
            # Read the extracted value
            with arcpy.da.SearchCursor("in_memory\\extracted_point", ["RASTERVALU"]) as cursor:
                for row in cursor:
                    bleaching_value = row[0]
                    if bleaching_value is None:
                        bleaching_value = "No Data"
                    
                    results["Year"].append(year)
                    results["Bleaching_Percentage"].append(bleaching_value)
                    
        except Exception as e:
            print(f"Error extracting value for year {year}: {e}")
            results["Year"].append(year)
            results["Bleaching_Percentage"].append("No Data")
    
    else:
        print(f"Raster for year {year} not found.")
        results["Year"].append(year)
        results["Bleaching_Percentage"].append("No Data")

# Convert results to a pandas DataFrame
results_df = pd.DataFrame(results)

# Display results in the console
print("\nBleaching Percentage Table by Year")
print(results_df.to_string(index=False))