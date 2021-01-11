# when running realsense-viewer, the export JSON function can be used to
# get settings for high-accuracy mode, etc.

import os
import json
fname = "high-density-a-factor.json"
string_output_fname = os.path.basename(fname).split('.')[0] + '.txt'
j = json.load(open(fname))
final_string = []
for key in j:
    final_string.append( '\\"%s\\" : \\"%s\\"' % (key, j[key]))

final_string = "{%s}" % ','.join(final_string)

f = open(string_output_fname, "w")
f.write(final_string)
f.close()
