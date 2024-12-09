# We need to insert a heading here

# Import necessary modules
import arcpy
import os
import sys
import pandas as pd

# Import the Path function
from pathlib import Path
# Import necessary ArcPy tools
from arcpy.sa import SplineWithBarriers, Con

# Define Current Folder
script_folder = Path.cwd()
# Define the root folder
root_folder = script_folder.parent
# Define the scratch folder
scratch_folder = root_folder / "Scratch"
# Define the data folder
data_folder = root_folder / "Data"
# Define the file path to our processed coral data folder
coral_data = str(root_folder / 'Data' / 'Processed' / 'coral_data_filtered.shp')

# Define ArcPy environment workspace
arcpy.env.workspace = str(scratch_folder)
# Define output workspace
output_workspace = str(scratch_folder)
# Define final output workspace
final_workspace = root_folder / "Final_Outputs"
# Enable output overwrite
arcpy.env.overwriteOutput = True # This currently isn't working right

# Tool to interpolate coral bleaching by year and create raster heat maps by year

# Loop through each year
for year in range(2002, 2017):  # Loops through years 2002-2016
    print(f"Processing year: {year}")
    
    # Filter the input data by year
    yearly_data = arcpy.management.MakeFeatureLayer(
        coral_data, f"yearly_data_{year}", f"Date_Year = {year}"
    )
    
    # Generate output names for this year
    bounding_geometry_output = f"coral_bounds_{year}"
    spline_raster = f"v:\\Final_Project\\Scratch\\coral_bleach_spline_{year}.tif"
    con_raster = f"v:\\Final_Project\\Scratch\\Con_coral_bleach_{year}.tif"
    clipped_raster = f"v:\\Final_Project\\Final_Outputs\\coral_bleaching_{year}.tif"

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
        yearly_data, "Percent_Bl", bounding_geometry_output, # We should fix this column in our final version
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

# Site method Tool

# List available site names for the user
site_names = []
with arcpy.da.SearchCursor(coral_data, ["Site_Name"]) as cursor:
    for row in cursor:
        if row[0] not in site_names:
            site_names.append(row[0])

# Display available site names and prompt user selection
print("Available site names:")
for i, site in enumerate(site_names):
    print(f"{i + 1}: {site}")

site_choice = int(input("Select a site by entering its number: ")) - 1
selected_site = site_names[site_choice]

print(f"You selected: {selected_site}")

# Filter the coral data to only include the selected site
site_layer = "in_memory\\selected_site"
arcpy.management.MakeFeatureLayer(
    coral_data, site_layer, f"Site_Name = '{selected_site}'"
)

# Create buffer zones around each point
buffer_output = str(final_workspace / f"{selected_site}_Buffer.shp")
arcpy.analysis.Buffer(
    in_features=site_layer,
    out_feature_class=buffer_output,
    buffer_distance_or_field="500 Meters",  # Adjust distance as needed
    line_side="FULL",
    line_end_type="ROUND",
    dissolve_option="ALL"  # Dissolves all individual buffers into one
)

print(f"Minimum Bounding Geometry created: {mbg_output}")

# Initialize results dictionary
results = {"Year": [], "Bleaching_Percentage": []}

# Loop through rasters for each year
for year in range(2002, 2017):  # Iterate through years 2002-2016
    print(f"Processing year: {year}")
    
    raster_path = f"v:\\Final_Project\\Scratch\\Clipped_coral_bleach_{year}.tif" # Scratch should be changed to Final_Outputs once the previous section is run.
    
    if arcpy.Exists(raster_path):
        # Extract raster value within the selected site
        try:
            extracted_points = arcpy.sa.ExtractValuesToPoints(site_layer, raster_path, "in_memory\\extracted_points")
            
            # Calculate mean bleaching percentage within the site
            values = []
            with arcpy.da.SearchCursor("in_memory\\extracted_points", ["RASTERVALU"]) as cursor:
                for row in cursor:
                    if row[0] is not None:
                        values.append(row[0])
            
            # Calculate mean or handle no data
            if values:
                mean_bleaching = sum(values) / len(values)
            else:
                mean_bleaching = "No Data"
            
            results["Year"].append(year)
            results["Bleaching_Percentage"].append(mean_bleaching)
        
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