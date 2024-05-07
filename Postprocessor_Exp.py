# -*- coding: utf-8 -*-
"""
Created on Mon May  6 14:35:30 2024

@author: shant
"""

import datetime

loc = 'D:\Dr. Bohrer Lasertec\Projects\Postprocesser\EXP_kinetic.txt'

file = open(loc, 'r')
content = file.read()

header = """
Postprocessor Exp
Dr. Bohrer Lasertec GmbH
Custom Post Processor
File location: {}
Output Time: {}
""".format(
    loc, str(datetime.datetime.now())
)

filecontent = []
flag = False

filecontent.append(header)

with open(r'D:\Dr. Bohrer Lasertec\Projects\Postprocesser\EXP_kinetic.txt', 'r') as fp:
    for line_no, line in enumerate(fp):
        if line_no > 15:
            if 'F' in line:
                if flag == False:
                    templine = 'M61'
                    filecontent.append(templine)
                    flag == True
                else:
                    templine = 'M62'
                    filecontent.append(templine)
            filecontent.append(line)

for i in filecontent:
    print(i)