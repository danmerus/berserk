max_seq = 0 
curr_max = 0	
in_ = "1\n2\n2"
for val in input().split():
	if int(val) == 0:
		break
	elif int(val) > curr_max:
		curr_max = int(val)
		max_seq = 1
	elif int(val) == curr_max:
		max_seq += 1

print(str(max_seq))
