from pymxs import runtime as rt

def has_non_ascii(s):
	for char in s:
		if ord(char) > 127:
			return True
	return False
    
step = 0
for currentObject in rt.objects:
	if has_non_ascii(currentObject.name):
		step = step + 1
		print(currentObject.name)
		currentObject.name = "TEMPLATE_NAME_" + str(step)
