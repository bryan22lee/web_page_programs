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

# Get HAR archive File name (as command-line argument)
har = sys.argv[1]
with open(har, 'r') as f:
    har_parser = HarParser(json.loads(f.read()))

# Get total in bytes for _bytesIn and _objectSize
total_bytesIn = total_objectSize = byteCount = objectCount = 0
for page in har_parser.pages:
    for entry in page.entries:
        if (entry["_bytesIn"] >= 0):
            total_bytesIn += entry["_bytesIn"]
            byteCount += 1
        if (entry["_objectSize"] >= 0):
            total_objectSize += entry["_objectSize"]
            objectCount += 1
print("IN BYTES:")
print("Total bytes retrieved: " + str(total_bytesIn) + ", Count: " + str(byteCount))
print("Total objects retrieved: " + str(total_objectSize) + ", Count: " + str(objectCount))
print()

# Calculate percentages of bytes retrived / objects retrieved, respetively, as a function of time (from 0 to onLoad)
