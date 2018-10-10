#!/usr/bin/python -tt
# -*- coding:UTF-8 -*-
import urllib
import pyodbc
import datetime
from bs4 import BeautifulSoup
import cookielib
import time
import urllib2
import json
from random import randint
import time
#import requests

filecounter = 0

now = datetime.datetime.now()

TIME_BT_REQUESTS = 1.0


def get_url_content(url):
	text = ''
	try:
		ufile = urllib.urlopen(url)
		text = ufile.read()
		#print text
		
		ufile.close()
	except IOError:
		logException('Url okuma hatası: ' + url)
		#print 'Url okuma hatası:', url

	return text
	
def logException(message):
		with open("E:\\Python\\Project\\Strava\\Exception.txt", "a") as myfile:
			myfile.write(message + "\n")
			
def log_in():
	print("Logging in...")
	cj = cookielib.CookieJar()
	opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

	f = opener.open('https://www.strava.com/login')
	soup = BeautifulSoup(f.read(), "html.parser")

	time.sleep(TIME_BT_REQUESTS)

	utf8 = soup.findAll('input', {'name': 'utf8'})[0].get('value').encode('utf-8')
	token = soup.findAll('input', {'name': 'authenticity_token'})[0].get('value')

	values = {
		'utf8': utf8,
		'authenticity_token': token,
		'email': 'orhanmetin@gmail.com',
		'password': '235711',
	}

	data = urllib.urlencode(values)
	url = 'https://www.strava.com/session'
	response = opener.open(url, data)
	soup = BeautifulSoup(response.read(), "html.parser")
	
	# with open("E:\\Python\\Project\\Strava\\Login.txt", "a") as myfile:
		# myfile.write(response.read())	
	
	time.sleep(TIME_BT_REQUESTS)
	print("Logging in OK")
	return opener

def get_race_results(opener):
	# without these headers, the request doesn't return anything
	opener.addheaders = [
		('X-Requested-With', 'XMLHttpRequest'),
		('Accept', 
			('text/javascript, application/javascript, application/ecmascript,'
			' application/x-ecmascript')
		),
	]	
	
	page = 1
	while page <= 351:
		prin(str(page) + "/351\n")
		url = 'https://www.strava.com/running_races/2017-paris-marathon/results?page=' + str(page)

		try:
			response = opener.open(url)
		except(Exception, e:)
			print(e)
			return
		
		#with open("E:\\Python\\Project\\Strava\\2017-paris.txt", "a") as myfile:
		#	myfile.write(response.read())	
		
		soup = BeautifulSoup(response.read(), "html.parser")
		table = soup.find_all('table', id='results-table')
		rows = table[0].find_all('tr')
		
		#columns = rows[1].find_all("td")
		#print (columns[1].find_all('a'))[0]['href']
		
		for row in rows[1:]:
			activityId = row['data-activity_id']
			
			columns = row.find_all("td")
			
			rank = columns[0].text.strip()
			athleteId = (columns[1].find_all('a'))[1]['href'].strip().replace('/athletes/','')
			athletename = (columns[1].find_all('a'))[1].text.strip().replace("'","''")
			gender = columns[2].text.strip()
			age = columns[3].text.strip()
			finish = columns[4].text.strip()
			pace = columns[5].text.strip().replace('/km','')
			
			sqlstatement = "INSERT INTO [dbo].[StravaRaceResult]([Rank],[AthleteId],[AthleteName],[Gender],[Age],[Finish],[Pace],[ActivityId]) "
			sqlstatement += "VALUES (" + str(rank) + "," + str(athleteId) + ",'" + athletename.encode('utf-8','ignore') + "','" + str(gender) + "'," + (str(age) if age.isdigit() else "null") + ",'" + str(finish) + "','" + str(pace) + "'," + str(activityId) + ")"
		
			with open("E:\\Python\\Project\\Strava\\2017-paris-raceresult_sql.txt", "a") as myfile:
				myfile.write(sqlstatement + "\n")
				
		page += 1
		time.sleep(2.0)
		
def get_goals(goal_time):
	url = 'https://www.strava.com/running_races/801/training_details?goal_time=' + str(goal_time)
	
	response = urllib.urlopen(url)
	goals = json.loads(response.read())
	
	for active_athlete in goals["active_athletes"]:
		sqlstatement = "INSERT INTO [dbo].[StravaRaceGoal]([AthleteId],[GoalTime],[ResultTime]) "
		sqlstatement += "VALUES(" + str(active_athlete["athlete"]["id"]) + "," + str(active_athlete["goal_time"]) + "," + str(active_athlete["result_time"]) + ")"

		with open("E:\\Python\\Project\\Strava\\2017-paris-racegoals.txt", "a") as myfile:
			myfile.write(sqlstatement + "\n")
		
def get_lap_efforts(activityId):
	url = 'https://www.strava.com/activities/'  + str(activityId) + '/lap_efforts'
	
	response = urllib.urlopen(url)
	laps = json.loads(response.read())
	
	#print data[0]["id"]
	#print data[0]["abbr"]["distance"]["short"] + "\n" + data[0]["abbr"]["speed"]["short"]
	
	if laps[0]["abbr"]["distance"]["short"] != "km" or laps[0]["abbr"]["speed"]["short"] != "/km" or laps[0]["abbr"]["heartrate"]["short"] != "bpm":
		print(str(activityId) + " farkli birim\n")
	
	for lap in laps:
		sqlstatement = "INSERT INTO [dbo].[StravaActivityLapEffort]([ActivityId],[LapId],[LapIndex],[Distance],[StartIndex],[EndIndex],[ElevDifference],[AvgGrade],[AvgSpeed],[AvgMovingSpeed],[MaxSpeed],[AvgHr],[MaxHr],[AvgCadence],[MaxCadence],[ElapsedTime],[MovingTime]) "
		sqlstatement += "VALUES(" + str(activityId) + "," + str(lap["id"]) + "," + str(lap["index"]) + "," + str(lap["distance"]) + "," + str(lap["start_index"]) + "," + str(lap["end_index"]) + "," + str(lap["elev_difference"]) + "," + str(lap["avg_grade"]) + "," + str(lap["avg_speed"]) + "," + str(lap["avg_moving_speed"]) + "," + str(lap["max_speed"]) + "," + (str(lap["avg_hr"]) if lap["avg_hr"] is not None else "null") + "," + (str(lap["max_hr"]) if lap["max_hr"] is not None else "null") + "," + str(lap["avg_cadence"]) + "," + str(lap["max_cadence"]) + "," + str(lap["elapsed_time"]) + "," + str(lap["moving_time"]) + ")"
	
		with open("E:\\Python\\Project\\Strava\\2017-paris-lapefforts_sql_3.txt", "a") as myfile:
			myfile.write(sqlstatement + "\n")

	time.sleep(randint(1,3))

def get_all_goals():
	get_goals(1)	 #under 2:30 #1
	get_goals(9001)  #02:30-03:00 #122
	get_goals(10801) #03:00-03:30 #269
	get_goals(12601) #03:30-04:00 #338
	get_goals(14401) #04:00-04:30 #109
	get_goals(16201) #04:30-05:00 #24
	get_goals(18001) #over 05:00  #10 
	
def get_overview(opener, activityId):
	# without these headers, the request doesn't return anything
	opener.addheaders = [
		('X-Requested-With', 'XMLHttpRequest'),
		('Accept', 
			('text/javascript, application/javascript, application/ecmascript,'
			' application/x-ecmascript')
		),
	]	
	
	url = 'https://www.strava.com/activities/'  + str(activityId) + '/overview'
	
	try:
		response = opener.open(url)
	except Exception, e:
		print(e)
		return
	
	# with open("E:\\Python\\Project\\Strava\\2017-paris-overview.txt", "a") as myfile:
		# myfile.write(response.read())	
	
	watch, gear, distance, moving_time, pace, elevation, calories, elapsed_time = '','','','','','','',''
	achievements = list()
	
	soup = BeautifulSoup(response.read(), "html.parser")
	
	if (soup.find_all("ul", class_="inline-stats section")) is None or len(soup.find_all("ul", class_="inline-stats section")) == 0:
		print(str(activityId) + ' YOK')
		return
	
	divWatch = soup.find("div", class_="device spans8")
	if divWatch is not None:
		watch = divWatch.text.strip().encode('utf-8','ignore').replace("'","''")
		
	spanGear = soup.find("span", class_="gear-name")
	if spanGear is not None:
		gear = spanGear.text.strip().encode('utf-8','ignore').replace("'","''")
	
	ulStats = soup.find_all("ul", class_="inline-stats section") 
	if ulStats is not None and len(ulStats) > 0:
		liStats = ulStats[0].find_all('li')
		
		for liStat in liStats:
			if liStat.find("div",class_="label") is not None and liStat.find("strong") is not None:
				label_name = liStat.find("div",class_="label").text.strip()
				value = liStat.find("strong").text
				
				if label_name == 'Distance':
					distance = value.encode('utf-8').strip()
				elif label_name == 'Pace':
					pace = value.encode('utf-8').strip()
				elif label_name == 'Moving Time':
					moving_time = value.encode('utf-8').strip()
				elif label_name == 'Elapsed Time':
					elapsed_time = value.encode('utf-8').strip()				
				elif label_name <> 'Extreme Suffer Score' and label_name <> 'Epic Suffer Score' and label_name <> 'Epic Suffer Score Sufferfest':
					print(label_name)
	
	divMoreStats = soup.find("div", class_="section more-stats")
	if divMoreStats is not None and len(divMoreStats) > 0:
		moreStatsLabels = divMoreStats.find_all("div", class_="spans5")
		moreStatsValues = divMoreStats.find_all("div", class_="spans3")
		
		for i in range(len(moreStatsLabels)):
			if moreStatsLabels[i] is not None and moreStatsValues[i] is not None and moreStatsValues[i].find("strong") is not None:
				moreStatsLabel = moreStatsLabels[i].text.strip()
				moreStatsValue = moreStatsValues[i].find("strong").text.strip()
				
				if moreStatsLabel == 'Elevation':
					elevation = moreStatsValue.encode('utf-8').strip()
				elif moreStatsLabel == 'Calories':
					calories = moreStatsValue.encode('utf-8').strip()
				elif moreStatsLabel == 'Moving Time':
					moving_time = moreStatsValue.encode('utf-8').strip()				
				elif moreStatsLabel == 'Elapsed Time':
					elapsed_time = moreStatsValue.encode('utf-8').strip()	
				
	ulAchievements = soup.find_all("ul", class_="spans13 footer-achievements-list") 
	if ulAchievements is not None and len(ulAchievements) > 0:
		achievementNames = ulAchievements[0].find_all('strong')	
		achievementTimes = ulAchievements[0].find_all('time')	
		
		for i in range(len(achievementNames)):
			achievements.append((achievementNames[i].text.strip().replace("(","").replace(")","").replace("'","''").encode('utf-8'),achievementTimes[i].text.strip().replace("(","").replace(")","").replace("'","''").encode('utf-8')))
	
	# liGoalAccomplishment = soup.find("li", class_="goal-accomplishment")
	# if liGoalAccomplishment is not None:
		# goal_accomplished = liGoalAccomplishment.find("strong").text.strip()
	
	# print 'watch:' + watch
	# print 'gear:' + gear
	# print 'distance:' + distance
	# print 'moving_time:' + moving_time
	# print 'pace:' + pace
	# print 'elevation:' + elevation
	# print 'calories:' + calories
	# print 'elapsed_time:' + elapsed_time
	
	# for achievement in achievements:
		# print achievement[0] + ' - ' + achievement[1]
		
	sqlstatement = "INSERT INTO [dbo].[StravaRaceOverview] ([ActivityId],[Watch],[Gear],[Distance],[MovingTime],[ElapsedTime],[Pace],[Elevation]) "
	sqlstatement += "VALUES(" + str(activityId) + ",'" + watch + "','" + gear + "','" + distance + "','" + moving_time + "','" + elapsed_time + "','" + pace + "','" + elevation + "')"

	with open("E:\\Python\\Project\\Strava\\2017-paris-overview_3.txt", "a") as myfile:
		myfile.write(sqlstatement + "\n")

	for achievement in achievements:
		if achievement[0] <> 'PR' and achievement[0] <> 'CR' and "fastest time" not in achievement[0]:
			sqlstatement = "INSERT INTO [dbo].[StravaRaceAchievement]([ActivityId],[AchievementName],[AchievementTime]) "
			sqlstatement += "VALUES(" + str(activityId) + ",'" + achievement[0] + "','" + achievement[1] + "')"
			
			with open("E:\\Python\\Project\\Strava\\2017-paris-achievements_3.txt", "a") as myfile:
				myfile.write(sqlstatement + "\n")		

	time.sleep(1)		

	
def test():
	connection = pyodbc.connect('Driver={SQL Server};Server=.;Database=Xibalba;Integrated Security=true;') 
	cursor = connection.cursor() 
	cursor.execute("delete stravaactivity where athleteId = 15090805")
	#sql = "INSERT INTO [dbo].[StravaActivity]([Id],[AthleteId],[Name],[Type],[DateTimestamp],[Date],[UtcOffset],[WorkoutType],[Distance],[MovingTime],[ElapsedTime],[Speed],[ElevationGain],[Trainer],[Private],[EntityType]) VALUES(1542339687,15090805,'Burhan''la İlk Koşu','Run',1525156776,'2018/05/01 09:39:36',10800,3,3234.8,1370,1570,2.36116788321,109,0,0,'activity')"
	cursor.execute("INSERT INTO [dbo].[StravaActivity]([Id],[AthleteId],[Name],[Type],[DateTimestamp],[Date],[UtcOffset],[WorkoutType],[Distance],[MovingTime],[ElapsedTime],[Speed],[ElevationGain],[Trainer],[Private],[EntityType]) VALUES(1542339687,15090805,'Burhan''la İlk Koşu','Run',1525156776,'2018/05/01 09:39:36',10800,3,3234.8,1370,1570,2.36116788321,109,0,0,'activity')".decode('utf-8'))
	connection.commit()			
	
def get_training_log(opener, athleteId):
	global filecounter
	#https://www.strava.com/athletes/8063424/training/log/months?sport=Run&start_month=2018y12m&num_months=12
	#https://www.strava.com/athletes/8063424/training/log/weeks?sport=Run&start_week=2018y52w&num_weeks=52
	#https://www.strava.com/athletes/15090805/training/log/weeks?sport=Run&start_week=2018y16w&num_weeks=69
	url = 'https://www.strava.com/athletes/'  + str(athleteId) + '/training/log/weeks?sport=Run&start_week=2018y52w&num_weeks=100'	
							
	#try:
	response = opener.open(url)
	weeklyActivities = json.loads(response.read())
	
	conn_str = (
    "DRIVER={PostgreSQL Unicode(x64)};"
    "DATABASE=postgres;"
    "UID=postgres;"
    "PWD=235711;"
    "SERVER=127.0.0.1;"
    "PORT=3306;"
    )
	connection = pyodbc.connect(conn_str)
	#connection = pyodbc.connect('Driver={PostgreSQL Unicode};Server=127.0.0.1;PORT=3306;Database=strava;UID=postgres;PWD=235711;') 
	cursor = connection.cursor() 
	cursor.execute("delete from StravaActivity where AthleteId = " + str(athleteId))
	
	filecounter += 1
	#print str(athleteId)
	for weeklyActivity in weeklyActivities:
		if weeklyActivity["entry"] is not None and weeklyActivity["entry"]["activities"] is not None:
			for activity in weeklyActivity["entry"]["activities"]:
					sqlstatement = "INSERT INTO StravaActivity(Id,AthleteId,Name,Type,DateTimestamp,Date,UtcOffset,WorkoutType,Distance,MovingTime,ElapsedTime,Speed,ElevationGain,Trainer,Private,EntityType, Note) "
					sqlstatement += "VALUES(" + str(activity["id"]) + "," + str(athleteId) + ",'" + activity["name"].encode('utf-8','ignore').replace("'","''") + "','" + str(activity["type"]) + "'," + str(activity["start_date"]) + ",'" + time.strftime('%Y/%m/%d %H:%M:%S',  time.gmtime(activity["start_date"] + activity["utc_offset"]))  + "'," + str(activity["utc_offset"]) + "," +  (str(activity["workout_type"]) if activity["workout_type"] is not None else "null") + "," + str(activity["distance"]) + "," + str(activity["moving_time"]) + "," + str(activity["elapsed_time"]) + "," + str(activity["speed"]) + "," + str(activity["elev_gain"]) + "," + (str(activity["trainer"]) if activity["trainer"] is not None else "null") + "," + (str(activity["private"]) if activity["private"] is not None else "null") + ",'" + str(activity["entity_type"]) + "'," + ("'" + activity["description"].encode('utf-8','ignore').replace("'","''") + "'" if activity["description"] is not None else "null") + ")"
					
					cursor.execute(sqlstatement.decode('utf-8'))							
					#with open("C:\\MY\\Training_Log_3.txt", "a") as myfile:
					#	myfile.write(sqlstatement + "\n")	
	
	connection.commit()	
	connection.close()
	#except:
	#	return False


def main():
	opener = log_in()
	get_training_log(opener, 15090805)
	#get_training_log(opener, 30495016)
	return
	
	text_file = open("D:\Python\Project\Strava\Athletes.txt", "r")
	athleteIds = text_file.read().splitlines()
	
	for athleteId in athleteIds:
		get_training_log(opener, athleteId)
		
if __name__ == '__main__':
	main()
