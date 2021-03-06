# Parse a HAR archive file to calculate ByteIndex and ObjectIndex
# as in the "Measuring the Quality of Experience of Web users" paper
# by Bocchi et al.

# Implementaion by Chanik Bryan Lee

# ByteIndex is computed by integral (1 - B(t)) dt from 0 to onLoad
#   where B(t) is the percentage of bytes received at time t

# ObjectIndex is computed by integral (1 - O(t)) dt from 0 to onLoad
#   where O(t) is the percentage of objects received at time t

# Take in a HAR archive as input, return ByteIndex and ObjectIndex values:
import sys
import json
from haralyzer import HarParser, HarPage
from numpy import trapz
import pandas as pd
import asciiplotlib as apl
# import matplotlib.pyplot as plt

# Handle too many or not enough inputs
if len(sys.argv) < 2:
    raise Exception("Error: need a path to HAR file as command-line argument")
elif len(sys.argv) > 2:
    raise Exception("Error: gave too many command-line arguments")

# Get HAR archive File name (as command-line argument)
har = sys.argv[1]
with open(har, 'r') as f:
    har_parser = HarParser(json.loads(f.read()))

# Get onLoad per page load
page_onLoad = []
for item in har_parser.har_data["pages"]:
    page_onLoad.append(item.get("pageTimings").get("onLoad"))

# Get total in bytes for _bytesIn and _objectSize
numPages = 0
total_bytesIn = []
total_objectSize = []
for page in har_parser.pages:
    numPages += 1
    byteSize = objSize = 0
    for entry in page.entries:
        byteSize += int(entry["_bytesIn"])
        objSize += int(entry["_objectSize"])
    total_bytesIn.append(byteSize)
    total_objectSize.append(objSize)

if numPages == 1:
    print(str(numPages) + " Page Load\n")
else:
    print(str(numPages) + " Page Loads\n")
print("IN BYTES (per page load):")
print("Total bytes retrieved: " + str(total_bytesIn))
print("Total objects retrieved: " + str(total_objectSize))
print()

# Get raw values for time, bytes, objects until onLoad endpoint
time_to_onload = []
bytes_to_onload = []
objects_to_onload = []
pageCount = 0
for page in har_parser.pages:
    l1 = []
    l2 = []
    l3 = []
    for entry in page.entries:
        l1.append(entry["time"])
        l2.append(int(entry["_bytesIn"]))
        l3.append(int(entry["_objectSize"]))
    time_to_onload.append(l1)
    bytes_to_onload.append(l2)
    objects_to_onload.append(l3)

# Check that all page loads have the same number of time, _bytesIn, and _objectSize information
for i in range(len(time_to_onload)):
    if len(time_to_onload[i]) != len(bytes_to_onload[i]):
        raise Exception("Error: time_to_onload != bytes_to_onload for index " + str(i))
    if len(time_to_onload[i]) != len(objects_to_onload[i]):
        raise Exception("Error: time_to_onload != objects_to_onload for index " + str(i))
    if len(bytes_to_onload[i]) != len(objects_to_onload[i]):
        raise Exception("Error: bytes_to_onload != objects_to_onload for index " + str(i))

# Calculate percentages of bytes and objects retrieved with respect to time (from 0 to onLoad)
bytes_to_onload_percentages = []
objects_to_onload_percentages = []
for i in range(len(total_bytesIn)):
    l1 = []
    l2 = []
    for j in range(0, len(time_to_onload[i])):
        l1.append(bytes_to_onload[i][j] / total_bytesIn[i])
        l2.append(objects_to_onload[i][j] / total_objectSize[i])
    bytes_to_onload_percentages.append(l1)
    objects_to_onload_percentages.append(l2)
del l1; del l2; del l3 # From before

# Takes in a list and returns aggregate, i.e. each item of list becomes value of that item added with all item before it
def get_aggregate(l):
    cpy = l.copy()
    for i in range(len(l)):
        for j in range(i):
            l[i] += cpy[j]
    del cpy
    return l

# Make list of dataframes based on page load index and sort them by time
page_load_df_list = [] # List of dataframes for each web page load from HAR archive file
for i in range(len(time_to_onload)):
    # Reassignment to create new dataframes
    tmp_dat = {"time_to_onload":time_to_onload[i], "raw_bytes":bytes_to_onload[i], "percent_bytes":bytes_to_onload_percentages[i],
               "raw_objects":objects_to_onload[i], "percent_objects":objects_to_onload_percentages[i]}
    tmp_df = pd.DataFrame(tmp_dat, columns=["time_to_onload", "raw_bytes", "percent_bytes", "raw_objects", "percent_objects"])
    # Sort by time
    tmp_df = tmp_df.sort_values(by = ["time_to_onload"])
    page_load_df_list.append(tmp_df)
del tmp_dat; del tmp_df

# Percentage accumulation over time
for i in range(len(page_load_df_list)):
    # Percent bytes
    tmp_list_a = []
    for a in page_load_df_list[i]["percent_bytes"]:
        tmp_list_a.append(a)
    page_load_df_list[i]["percent_bytes"] = get_aggregate(tmp_list_a.copy())

    # Percent objects
    tmp_list_b = []
    for b in page_load_df_list[i]["percent_objects"]:
        tmp_list_b.append(b)
    page_load_df_list[i]["percent_objects"] = get_aggregate(tmp_list_b.copy())
# Delete variables from memory
del tmp_list_a; del tmp_list_b

# Plot general relationships
if numPages != 1:
    print("RELATIONSHIP VISUALIZATIONS (for page load 1 only):\n")
else:
    print("RELATIONSHIP VISUALIZATIONS:\n")

# Percent bytes vs. time
print(" Percentage of bytes retrieved vs. Time")
fig = apl.figure()
fig.plot(page_load_df_list[0]["time_to_onload"], page_load_df_list[0]["percent_bytes"])
fig.show()
# Percentage objects vs. time
print("\n Percentage of objects retrieved vs. Time")
fig = apl.figure()
fig.plot(page_load_df_list[0]["time_to_onload"], page_load_df_list[0]["percent_objects"])
fig.show()

# matplotlib.pyplot visualizations
# plt.plot(page_load_df_list[0]["time_to_onload"], page_load_df_list[0]["percent_bytes"])
# plt.show()
# plt.plot(page_load_df_list[0]["time_to_onload"], page_load_df_list[0]["percent_objects"])
# plt.show()

# Function fitting (regression)
print("\n\n(Integration with the composite trapezoidal rule)\n")
# Compute (1 - x(t)) for both percenty_bytes and percent_objects for each web page load
integrate_df_list = []
for i in page_load_df_list:
    integrate_percent_bytes = []
    integrate_percent_objects = []
    for j, k in zip(i["percent_bytes"], i["percent_objects"]):
        integrate_percent_bytes.append(1 - j)
        integrate_percent_objects.append(1 - k)
    # Create dataframe
    integrate_dat = {"time":i["time_to_onload"], "integrate_percent_bytes":integrate_percent_bytes, "integrate_percent_objects":integrate_percent_objects}
    integrate_df = pd.DataFrame(integrate_dat, columns=["time", "integrate_percent_bytes", "integrate_percent_objects"])
    integrate_df_list.append(integrate_df)

# Compute and print onLoad, byteIndex, and objectIndex for each web page load
print("RESULTS (onLoad, byteIndex, objectIndex) per each web page load:\n")

# Compute byteIndex & objectIndex
list_byteIndex = []
list_objectIndex = []
for i in range(len(integrate_df_list)):
    # Get relevant lists for integration
    y1 = list(integrate_df_list[i]["integrate_percent_bytes"])
    y2 = list(integrate_df_list[i]["integrate_percent_objects"])
    x = list(integrate_df_list[i]["time"])

    # Set integration endpoint to onLoad such that the integral is bounded by [0, onLoad]
    for j in range(len(x)):
        if x[j] > page_onLoad[i]:
            # Trim the lists to the onLoad endpoint
            del x[j:]; del y1[j:]; del y2[j:]
            break

    # byteIndex
    # Integration using trapezoidal rule
    list_byteIndex.append(trapz(y1, x=x))

    # objectIndex
    # Integration using trapezoidal rule
    list_objectIndex.append(trapz(y2, x=x))
# Delete variables from memory
del x; del y1; del y2

# Print results
for i in range(len(page_onLoad)):
    print(" Page Load " + str(i + 1) + ": (" + str(page_onLoad[i]) + ", " + str(list_byteIndex[i]) + ", " + str(list_objectIndex[i]) + ")")