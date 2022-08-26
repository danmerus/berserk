max_seq = 0 
curr_max = 0	
with open('input.txt', 'r', encoding='utf-8') as f:
	data = f.read()
func_ = lambda x: list(map(int, x.splitlines())).count(max(map(int, x.splitlines())))
max_seq = func_(data)
print(max_seq)
with open('output.txt', 'w', encoding='utf-8') as out:
	out.write(str(max_seq))