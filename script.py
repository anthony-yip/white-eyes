import numpy as np 
import cv2 as cv 
from matplotlib import pyplot as plt


def getTwoBoundingBox(array):
    full_array = np.full(len(array[1]), 255)
    for i in range(len(array)):
        if not np.array_equal(array[i],full_array):
            left_bound = i
            break
    for j in reversed(range(len(array))):
        if not np.array_equal(array[j],full_array):
            right_bound = j
            return left_bound,right_bound

def getAllBoundingBox(array):
    #to be used on a black image on white background. returns the bounding box of the black image.
    top,bottom = getTwoBoundingBox(array)
    rotated_array = np.rot90(array,3)
    left,right = getTwoBoundingBox(rotated_array)
    return top,bottom,left,right

#note: x and y values correspond to column and row values respectively
def getCoord(event,x,y,flags,param):
    #prints coordinate of mouse click location
    global ix, iy
    if event == cv.EVENT_LBUTTONDOWN:
        ix = x
        iy = y

def checkImage(image):
	#displays an image, allowing for interaction.
	#click at a point, then press 'p' to print the coordinate
	#use 'esc' to close the window
	cv.namedWindow('frame', cv.WINDOW_AUTOSIZE)
	cv.setMouseCallback('frame',getCoord)
	while(1):
		cv.imshow('frame', image) 
		k = cv.waitKey(1) & 0xFF
		if k == ord('p'):
			print(ix,iy)
		elif k == 27:
			break 
	cv.destroyAllWindows()

def analyseNumbers(img,threshold,uncertainty,s_b):
	#binarise img to only show black and white 
	ret,img = cv.threshold(img,245,255,cv.THRESH_BINARY_INV)
	dic = {}
	#iterate through each digit to be identified:
	for i in range(len(small)):
		#make copy instead of view
		locations = []
		master = (0,0)
		item = s_b[i]
		w, h = item.shape[::-1]
		result = cv.matchTemplate(img,item,cv.TM_CCOEFF_NORMED)
		loc = np.where( result >= threshold)
		for pt in zip(*loc[::-1]):
			locations.append(pt)
		#list of tuples of coordinates, sorted by first element (index 0)
		sorted_tuples = sorted(locations, key=lambda tup: tup[0])
		#iterate through each coordinate:
		for j in range(len(sorted_tuples)):
			coord = sorted_tuples[j]
			#value is a tuple of (threshold value, digit)
			value = (result[coord[1],coord[0]],i)
			if j == 0:
				#check if coordinate already exists in dic 
				if coord not in dic:
					dic[coord] = value
					master = coord
				elif dic[coord][0] > value[0]: #comparing threshold values
					#if existing value is better, don't edit it
					master = coord	
				else:
					dic[coord] = value
					master = coord
			else:
				#same point
				if sorted_tuples[j][0] - master[0] < uncertainty:
					#swap out master for current coordinate
					if dic[master][0] <= value[0]: #comparing threshold values
						dic.pop(master,None)
						dic[coord] = value
						master = coord
				#different point
				else: #do the same thing again
					if coord not in dic:
						dic[coord] = value
						master = coord
					elif dic[coord][0] > value[0]:
						master = coord	
					else:
						dic[coord] = value
						master = coord
	keys = list(dic.keys())
	#list of coordinates
	sorted_keys = sorted(keys, key=lambda tup: tup[0])
	#sorted list of coordinates
	#remove "duplicates"
	count = 0
	for i in range(len(sorted_keys)):
		if i != 0:
			current_coord = sorted_keys[i-count]
			previous_coord = sorted_keys[i-1-count]
			if current_coord[0] - previous_coord[0] < uncertainty:
				if dic[current_coord][0] > dic[previous_coord][0]:
					dic.pop(previous_coord,None)
					sorted_keys.pop(i-1-count)
				else:
					dic.pop(current_coord,None)
					sorted_keys.pop(i-count)
				count += 1
	return dic

def analyseCards(img):
	#maximum uncertainty in location observed is 8
	#distance between adjacent digits (e.g. 12) is 15
	dic = analyseNumbers(img,0.5,11,big)
	return len(dic)

def analyseMinions(img):
	#maximum uncertainty in location observed is 5
	#distance between adjacent digits (e.g. 12) is 8
	#distance across minion is 50
	dic = analyseNumbers(img,0.53,9,small)
	final_keys = list(dic.keys())
	final_sorted_keys = sorted(final_keys, key=lambda tup: tup[0])
	abort = False
	grouped = []
	minions = []
	digits = []
	count = 1
	for i in range(len(final_sorted_keys)):
		#every digit in a row
		digits.append(dic[final_sorted_keys[i]][1])
		if i != 0:
			current_coord = final_sorted_keys[i]
			previous_coord = final_sorted_keys[i-1]
			if current_coord[0] - previous_coord[0] < 20:
				if i-2 in grouped:
					abort = True
					minions = []
					return abort, minions
				else:
					#lists places with double digits
					grouped.append(i-1)
	for i in range(len(digits)):
		#merge double digits together
		if i in grouped:
			ones = digits.pop(i+2-count)
			digits[i+1-count] = 10 * digits[i+1-count] + ones
			count += 1
	if len(digits) % 2 != 0:
		abort = True
		minions = []
		return abort,minions
	for i in range(len(digits) // 2):
		#finalise list of minions
		minions.append((digits[2 * i], digits[2 * i + 1]))
	return abort, minions

def analyseLife(img, armour=False):
	#maximum uncertainty in location observed is 6
	#distance between adjacent digits (e.g. 12) is 7
	dic = analyseNumbers(img,0.5,7,small_alt)
	final_keys = list(dic.keys())
	final_sorted_keys = sorted(final_keys, key=lambda tup: tup[0])
	abort = False
	health = 0
	no_of_digits = len(final_sorted_keys)
	if no_of_digits == 1:
		health = dic[final_sorted_keys[0]][1]
	elif no_of_digits == 2:
		health = 10 * dic[final_sorted_keys[0]][1] + dic[final_sorted_keys[1]][1]
	elif no_of_digits == 3 and armour:
		health = 100 * dic[final_sorted_keys[0][1]] + 10 * dic[final_sorted_keys[1][1]] + dic[final_sorted_keys[2]][1]
	elif no_of_digits == 0 and armour:
		health = 0
	else:
		abort = True
	return abort, health	

def analyseManaSelf(img):
	ret,img = cv.threshold(img,100,255,cv.THRESH_BINARY_INV)
	mana_self = img[717:734,136:182]
	top,bottom,left,right = getAllBoundingBox(mana_self)
	mana_self_final = mana_self[top-1:bottom+2,left-1:right+2]
	if np.shape(mana_self_final)[1] > 34:
		return (10,10)
	elif np.shape(mana_self_final)[1] > 28:
		left_digit = img[717:734,144:156]
		max_values = []
		for i in range(len(tiny)):
			result = cv.matchTemplate(left_digit,tiny[i],cv.TM_CCOEFF_NORMED)
			min_val, max_val, min_loc, max_loc = cv.minMaxLoc(result)
			max_values.append(max_val)
		digit = max_values.index(max(max_values))
		return (digit,10)
	else:
		left_digit = img[717:734,150:163]
		right_digit = img[717:734,168:181]
		max_values_left = []
		max_values_right = []
		for i in range(len(tiny)):
			result_left = cv.matchTemplate(left_digit,tiny[i],cv.TM_CCOEFF_NORMED)
			result_right = cv.matchTemplate(right_digit,tiny[i],cv.TM_CCOEFF_NORMED)
			min_val, max_val_left, min_loc, max_loc = cv.minMaxLoc(result_left)
			max_values_left.append(max_val_left)
			min_val, max_val_right, min_loc, max_loc = cv.minMaxLoc(result_right)
			max_values_right.append(max_val_right)
		left_digit_output = max_values_left.index(max(max_values_left))
		right_digit_output = max_values_right.index(max(max_values_right))
		return (left_digit_output,right_digit_output)

def checkWeapon(gamestate):
	if 255 in gamestate[68:89,170:229]:
		return True
	else:
		return False

def analyseGamestate(gamestate):
	#gamestate is initially coloured with frame (including white border) removed
	#change reds and greens to white, return grayscale image
	#[79 221 41] is green (buff), [0 0 221] is red (damaged)
	gamestate_HSV = cv.cvtColor(gamestate, cv.COLOR_BGR2HSV)
	reds = cv.inRange(gamestate_HSV, (0,238,128), (180,255,228))
	greens = cv.inRange(gamestate_HSV, (62,80,120), (68,255,255))
	#merge green and red numbers onto gamestate
	gamestate = cv.cvtColor(gamestate,cv.COLOR_BGR2GRAY)
	gamestate = np.bitwise_or(gamestate,reds)
	gamestate = np.bitwise_or(gamestate,greens)
	dic = {}
	minions_opp_region = gamestate[309:342,201:1100]
	ret1, dic['minions_opp']  = analyseMinions(minions_opp_region)
	#minions_opp is a list of minions
	minions_self_region = gamestate[483:510,200:1100]
	ret2, dic['minions_self'] = analyseMinions(minions_self_region)
	#minions_self is a list of minions
	cards_self_region = gamestate[560:606,228:1095]
	dic['cards_self'] = analyseCards(cards_self_region)
	armour_opp_region = gamestate[100:124,123:163]
	ret3, dic['armour_opp'] = analyseLife(armour_opp_region,armour = True)
	armour_self_region = gamestate[640:662,123:163]
	ret4, dic['armour_self'] = analyseLife(armour_self_region,armour = True)
	health_opp_region = gamestate[139:160,126:157]
	ret5, dic['health_opp'] = analyseLife(health_opp_region)
	health_self_region = gamestate[675:697,129:158]
	ret6, dic['health_self'] = analyseLife(health_self_region)
	dic['mana'] = analyseManaSelf(gamestate)
	dic['weapon'] = checkWeapon(gamestate)
	return dic

def analyseVideo(videoname):
	cap = cv.VideoCapture(videoname)
	threshold = 0.9
	gentest = np.genfromtxt('storage/zeph.txt',np.uint8)
	zephrys = gentest[570:730,960:1035]
	w, h = zephrys.shape[::-1]
	zephrys_in_hand = False 
	countdown = 11
	countup = 0
	gamestate = np.zeros(1)
	choices = np.zeros(1)
	discovered = False
	while(cap.isOpened()):
		ret, frame = cap.read()
		if not ret:
			break
		#get rid of junk
		frameOI = frame[213:1029,388:1499]
		#[205:1029,388:1499] for screenshots
		gray = cv.cvtColor(frameOI, cv.COLOR_BGR2GRAY)
		#observe only hand_self
		grayOI = gray[549:,:]
		#template match with zephrys
		result = cv.matchTemplate(grayOI,zephrys,cv.TM_CCOEFF_NORMED)
		min_val, max_val, min_loc, max_loc = cv.minMaxLoc(result) 
		#condition for once zephrys enters hand
		if max_val > threshold and not zephrys_in_hand:
			zephrys_in_hand = True
		#condition for once zephrys leaves hand
		if max_val <= threshold and zephrys_in_hand:
			if discovered:
				if np.array_equal(frameOI[546,635],np.array([103,79,27],np.uint8)):
					gamestate = frameOI
					break
			else:
				countdown -= 1
				countup += 1
				#if zephrys is not active: no discover
				if countup >= 40:
					break
				if countdown == 0:
					#check if a discover is occuring
					if np.array_equal(frameOI[546,635],np.array([103,79,27],np.uint8)):
						countdown = 10
					else:
						choices = frameOI
						discovered = True
						#print(countup)
	return gamestate, choices

def align(screenshot):
	#binarise screenshot
	screenshot = cv.cvtColor(screenshot,cv.COLOR_BGR2GRAY)
	ret,screenshot = cv.threshold(screenshot,245,255,cv.THRESH_BINARY_INV)
	base = np.genfromtxt(f'storage/base.txt',np.uint8)
	result = cv.matchTemplate(screenshot,base,cv.TM_CCOEFF_NORMED)
	min_val, max_val, min_loc, max_loc = cv.minMaxLoc(result)
	corner_0 = max_loc[0] + 379
	corner_1 = max_loc[1] + 65
	return (corner_0,corner_1)

def analyseScreenshot(filename):
	read = cv.imread(filename,1)
	corner = align(read)
	read_OI = read[corner[1]: corner[1] + 824, corner[0]: corner[0] + 1111]
	dic = analyseGamestate(read_OI)
	print(dic)
	checkImage(read)

#instantiate each template
small_zero = np.genfromtxt('storage/small_zero.txt',np.uint8)
small_one_alt = np.genfromtxt('storage/small_one.txt',np.uint8)
small_one = np.full((15,10),255,dtype = np.uint8)
small_one[:,3:] = small_one_alt
small_two = np.genfromtxt('storage/small_two.txt',np.uint8)
small_three = np.genfromtxt('storage/small_three.txt',np.uint8)
small_four = np.genfromtxt('storage/small_four.txt',np.uint8)
small_five = np.genfromtxt('storage/small_five.txt',np.uint8)
small_six = np.genfromtxt('storage/small_six.txt',np.uint8)
small_seven = np.genfromtxt('storage/small_seven.txt',np.uint8)
small_eight = np.genfromtxt('storage/small_eight.txt',np.uint8)
small_nine = np.genfromtxt('storage/small_nine.txt',np.uint8)
small_reversed = [small_nine,small_eight,small_seven,small_six,small_five,small_four,small_three,small_two,small_one,small_zero]
small = [small_zero,small_one,small_two,small_three,small_four,small_five,small_six,small_seven,small_eight,small_nine]
small_alt = [small_zero,small_one_alt,small_two,small_three,small_four,small_five,small_six,small_seven,small_eight,small_nine]

big_zero = np.genfromtxt('storage/big_zero.txt',np.uint8)
big_one = np.genfromtxt('storage/big_one.txt',np.uint8)
big_one_alt = np.full((17,13),255,dtype = np.uint8)
big_one_alt[:,5:] = big_one
big_two = np.genfromtxt('storage/big_two.txt',np.uint8)
big_three = np.genfromtxt('storage/big_three.txt',np.uint8)
big_four = np.genfromtxt('storage/big_four.txt',np.uint8)
big_five = np.genfromtxt('storage/big_five.txt',np.uint8)
big_six = np.genfromtxt('storage/big_six.txt',np.uint8)
big_seven = np.genfromtxt('storage/big_seven.txt',np.uint8)
big_eight = np.genfromtxt('storage/big_eight.txt',np.uint8)
big_nine = np.genfromtxt('storage/big_nine.txt',np.uint8)
big = [big_zero,big_one,big_two,big_three,big_four,big_five,big_six,big_seven,big_eight,big_nine]
big_alt = [big_zero,big_one_alt,big_two,big_three,big_four,big_five,big_six,big_seven,big_eight,big_nine]

tiny_zero = np.genfromtxt('storage/tiny_zero.txt',np.uint8)
tiny_one = np.genfromtxt('storage/tiny_one.txt',np.uint8)
tiny_two = np.genfromtxt('storage/tiny_two.txt',np.uint8)
tiny_three = np.genfromtxt('storage/tiny_three.txt',np.uint8)
tiny_four = np.genfromtxt('storage/tiny_four.txt',np.uint8)
tiny_five = np.genfromtxt('storage/tiny_five.txt',np.uint8)
tiny_six = np.genfromtxt('storage/tiny_six.txt',np.uint8)
tiny_seven = np.genfromtxt('storage/tiny_seven.txt',np.uint8)
tiny_eight = np.genfromtxt('storage/tiny_eight.txt',np.uint8)
tiny_nine = np.genfromtxt('storage/tiny_nine.txt',np.uint8)
tiny = [tiny_zero,tiny_one,tiny_two,tiny_three,tiny_four,tiny_five,tiny_six,tiny_seven,tiny_eight,tiny_nine]



#check algorithm
analyseScreenshot('test_screenshot.png')
