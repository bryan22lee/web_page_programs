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
        byteSize += entry["_bytesIn"]
        objSize += entry["_objectSize"]
    total_bytesIn.append(byteSize)
    total_objectSize.append(objSize)

print(str(numPages) + " Page Loads\n")
print("IN BYTES (per page load):")
print("Total bytes retrieved: " + str(total_bytesIn))
print("Total objects retrieved: " + str(total_objectSize))
print()

# Check that there are the same number _bytesIn values and _objectSize values for each page load
for i, n in enumerate(total_bytesIn):
    if n != total_objectSize[i]:
        raise Exception("Unequal totals between _bytesIn and _objectSize for an index!")

# Calculate percentages of bytes retrived / objects retrieved, respetively, as a function of time (from 0 to onLoad)
