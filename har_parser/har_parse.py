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
from scipy import integrate
import pandas as pd
import asciiplotlib as apl

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
    for i in range(len(l)):
        for j in range(i):
            l[i] += l[j]
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
    tmp_percent_bytes = page_load_df_list[i]["percent_bytes"]
    n = page_load_df_list[i].columns[2]
    page_load_df_list[i].drop(n, axis = 1, inplace = True)
    page_load_df_list[i][n] = get_aggregate(tmp_percent_bytes.copy())

    # Percent objects
    tmp_percent_objects = page_load_df_list[i]["percent_objects"]
    n = page_load_df_list[i].columns[4]
    page_load_df_list[i].drop(n, axis = 1, inplace = True)
    page_load_df_list[i][n] = get_aggregate(tmp_percent_objects.copy())
# Clear variables
del tmp_percent_bytes; del tmp_percent_objects; del n

# Plot general relationships
print("RELATIONSHIP VISUALIZATIONS (for page load 1 only):\n")
print(" Time vs. Percentage of bytes retrieved at time t")
fig = apl.figure()
fig.plot(page_load_df_list[0]["time_to_onload"], page_load_df_list[0]["percent_bytes"])
fig.show()

# import matplotlib.pyplot as plt
# plt.plot(page_load_df_list[0]["time_to_onload"], page_load_df_list[0]["percent_bytes"])
# plt.show()