from bs4 import BeautifulSoup
import mechanize
import cookielib
#import html2text
from urllib2 import urlopen
import datetime
import re
import csv

BASE_URL = "http://www.strava.com/athletes/"

def make_soup(url, browser):
    soup = BeautifulSoup(browser.open(url).read())
    return soup

# def athlete_scraper(soup):
# 	athlete_profile = soup.find("div", {"class": "spans6 athlete-profile"})
# 	athlete_name = athlete_profile.find("h1", {"class": "bottomless"}).get_text()
# 	athlete_location = athlete_profile.find("div", {"class": "location"}).get_text()
# 	athlete_descrip = athlete_profile.find("div", {"class": "athlete-description section"}).p.get_text()
# 	print(athlete_name)
# 	print(athlete_location)
# 	print(athlete_descrip.encode('utf8'))
#
# 	athlete_social = athlete_profile.find("div", {"class": "social section"}).find_all("h2")
# 	athlete_following_cnt = athlete_social[0].find("span", {"class": "count"}).get_text().split(" ")[1]
# 	athlete_follower_cnt = athlete_social[1].find("span", {"class": "count"}).get_text().split(" ")[1]
# 	print("Following count: ", athlete_following_cnt)
# 	print("Follower count: ", athlete_follower_cnt)
#
# 	athlete_stats = soup.find("ul", {"class": "inline-stats"}).find_all("li")
# 	athlete_distance = athlete_stats[0].strong.get_text()
# 	athlete_time = athlete_stats[1].strong.get_text()
# 	athlete_elevation = athlete_stats[2].strong.get_text()
# 	print("Current month:")
# 	print("Distance: ", athlete_distance)
# 	print("Time: ", athlete_time)
# 	print("Elevation: ", athlete_elevation)
#
# 	athlete_achiev = soup.find("section", {"class": "athlete-achievements"}).find("ul").find_all("li")
# 	for i in range(len(athlete_achiev)):
# 		print athlete_achiev[i].get_text()
#
# 	athlete_table = soup.find("section", {"class": "row athlete-records"}).find_all("div", {"class": "spans8"})
# 	y_2_d = athlete_table[0].find("tbody").find_all("tr")
# 	y_2_d_stats = dict()
# 	for i in range(len(y_2_d)):
# 		key = y_2_d[i].th.get_text()
# 		value = y_2_d[i].td.get_text()
# 		y_2_d_stats[key] = value
# 	print y_2_d_stats
#
# 	all_time = athlete_table[1].find("tbody").find_all("tr")
# 	all_time_stats = dict()
# 	for i in range(len(all_time)):
# 		key = all_time[i].th.get_text()
# 		value = all_time[i].td.get_text()
# 		all_time_stats[key] = value
# 	print all_time_stats




def profile_scraper(soup, user_id):
	output = {}
	error_flag = False
	profile_soup = soup.find("div", {"class": "profile-heading profile section"})

	name_h2 = profile_soup.find("h2", {"class": "h1"})
	name = name_h2.get_text().encode('utf8')

	try:
		athlete_title = profile_soup.find("div", {"class": "athlete-title"}).get_text()
		athlete_title = re.sub(r"^\W+|\W+$", "", athlete_title).encode('utf8')
	except AttributeError:
		athlete_title = "null"

	try:
		title_date = name_h2['title']
		title_date = re.sub(r"Member Since: ", "", title_date).encode('utf8')
	except AttributeError:
		title_date = "null"

	try:
		location = profile_soup.find("div", {"class": "location"}).get_text()
		location = re.sub(r"^\W+|\W+$", "", location).encode('utf8')
	except AttributeError:
		location = "null"

	try:
		description = profile_soup.find("div", {"class": "description-content"}).get_text()
		# May keep the utf8 encoding, but give up the regex
		description = re.sub(r"^\W+|\W+$", "", description).encode('utf8')
	except AttributeError:
		description = "null"

	output = {
		"athlete-id": str(user_id),
		"name": str(name),
		"athlete-title": str(athlete_title),
		"title-start-date": str(title_date),
		"location": str(location),
		"description": str(description)
	}

	return output, error_flag
	
def main():
	br = mechanize.Browser()
	cj = cookielib.LWPCookieJar()
	br.set_cookiejar(cj)

	# Browser options
	br.set_handle_equiv(True)
	br.set_handle_gzip(True)
	br.set_handle_redirect(True)
	br.set_handle_referer(True)
	br.set_handle_robots(False)
	br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
	br.addheaders = [('User-agent', 'Chrome')]


	# The site we will navigate into, handling it's session
	br.open('https://www.strava.com/login')
	# In case of the need to note identifiers for the form
	#for f in br.forms():
	#    print f

	br.select_form(nr=0)

	# User credentials
	br.form['email'] = 'aman.arya524@gmail.com'
	br.form['password'] = 'Kumar2150'

	# Login
	br.submit()

	#br.open("http://www.strava.com/athletes/5866").read()

	soup = make_soup("http://www.strava.com/athletes/5866", br)
	#soup = BeautifulSoup(br.open("http://www.strava.com/athletes/5866").read())
	#soup = BeautifulSoup(br.response().read())
	print(profile_scraper(soup, user_id=5866))
	#main_body = soup.find('div', {'class': 'main_body'})
	#print main_body
"""
	sample_size = 1000

	user_id = range(1000, 1000 + sample_size)
	test_id1 = "5866"
	test_id2 = "1015"
	soup = page_url_generator(BASE_URL + test_id1)
	athlete_scraper(soup)
"""

if __name__ == '__main__':
	main()


"""
Client ID: 10565
Client Secret: 16c971f8460936a07379c354b98f34cd64d6c218 
Your Access Token: 828919bc5e86f94d9e10fdda30db0fd4d78848ee 
Authorization Code: 6dea7ab45a709cffa4ea5d0d43284b2d9f915124
"""
