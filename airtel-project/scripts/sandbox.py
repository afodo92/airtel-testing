values = '"RACK-01","RACK-02","RACK-03","RACK-04","RACK-05","RACK-06","RACK-07","RACK-08","RACK-09",'
for i in range(1,8):
    values = f'{values}"RACK-1{i}",'

print(values)