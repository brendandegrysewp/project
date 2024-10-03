"""
Javascript Object Notation is an extremely common method for storing and 
transferring data that you will frequently run into. We are storing our
configurations for the client and server in this type of file, so we have
provided this playground file and playground.json as a quick orientation on how
to access the data. The data was generated with a quick GPT4 query.
"""

# step 1 is to import the json library which will do the heavy lifting for us
import json

# step 2 is to read in the file using the json library
# note, you may need to update the path depending on where you stored playground.json
with open('part1\playground.json','r') as f:
    data = json.load(f)

# if we examine our new data object we will see it is a dictionary
print(type(data))

# let's take a look at the keys
print(data.keys())

# The outer dictionary has a single key which is "school". We can use this key
# to move further into the dictionary and get more information
print(data['school'].keys())

# let's store a few things into variables
school_name = data['school']['name']
school_location = data['school']['location']

# we also want to get the department names and the courses but the departments
# key contains a list of dictionaries so it is a bit more work

# some empty storage
departments = []

# loop through the inner list of dictionaries
for department in data['school']['departments']:
    department_name = department['name']
    departments.append(department_name)

print(f'Here are the departments in {school_name}, which is located in {school_location}: {", ".join(departments)}')

# can you figure out how to get all of the courses in the school?

