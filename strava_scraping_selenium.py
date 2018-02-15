from bs4 import BeautifulSoup
import datetime
import re
import json
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
import time
import pandas as pd


def make_soup(url, browser):
    browser.get(url)
    time.sleep(3)
    html_source = browser.execute_script("return document.documentElement.outerHTML;").encode("utf-8")
    soup = BeautifulSoup(html_source).body
    return soup


def page_url_generator(base_url, start_index=0000, sample_size=1000):
    page_url_list = []

    user_id = range(start_index, start_index + sample_size)

    for i in user_id:
        url = base_url + str(i)
        page_url_list.append(url)

    return page_url_list


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


def soc_stats_scraper(soup):
    output = {}
    try:
        soc_stats_soup = soup.find("div", {"class": "section connections"})
        stats = soc_stats_soup.find_all("li")
        following = int(stats[0].get_text().split("\n")[-2])
        followers = int(stats[1].get_text().split("\n")[-2])
        """
        May keep the href and scrape the social connections further
        """
    except AttributeError:
        following = 'na'
        followers = 'na'

    output = {
        "following": following,
        "followers": followers,
    }
    return output


def act_stats_scraper(soup):
    output = {}

    # Cycling
    try:
        cycling_soup = soup.find("div", {"class": "cycling hidden"})
        cycling_all_time = cycling_soup.find_all("tbody")[-1].find_all("tr")[1:]

        distance = cycling_all_time[0].find_all("td")[1].get_text()
        rides = cycling_all_time[1].find_all("td")[1].get_text()
        biggest_ride = cycling_all_time[2].find_all("td")[1].get_text()
        biggest_climb = cycling_all_time[3].find_all("td")[1].get_text()
    except AttributeError:
        distance = 'na'
        rides = 'na'
        biggest_ride = 'na'
        biggest_climb = 'na'
    cycling = {
        "distance": distance,
        "rides": rides,
        "biggest-ride": biggest_ride,
        "biggest-climb": biggest_climb,
    }

    # Running
    try:
        running_soup = soup.find("div", {"class": "running hidden"})
        # Need year tbody to locate "all the time" tbody
        running_year_soup = running_soup.find("tbody", {"id": "running-ytd"})
        running_all_time = running_year_soup.findNext("tbody").find_all("tr")[1:]

        distance = running_all_time[0].find_all("td")[1].get_text()
        runs = running_all_time[1].find_all("td")[1].get_text()
    except AttributeError:
        distance = 'na'
        runs = 'na'
    running = {
        "distance": distance,
        "runs": runs,
    }

    # Swimming
    try:
        swimming_soup = soup.find("div", {"class": "swimming hidden"})
        swimming_all_time = swimming_soup.find_all("tbody")[-1].find_all("tr")[1:]

        distance = swimming_all_time[0].find_all("td")[1].get_text()
        swims = swimming_all_time[1].find_all("td")[1].get_text()
    except AttributeError:
        distance = 'na'
        swims = 'na'
    swimming = {
        "distance": distance,
        "swims": swims,
    }

    # Output
    output = {
        "cycling": cycling,
        "running": running,
        "swimming": swimming,
    }

    return output


def month_url_generator(athlete_id, offset_num):
    month_url_ls = []
    now = datetime.datetime.now()
    current_month = now.month
    current_year = now.year

    for year_offset in range(0, offset_num + 1):
        year_str = str(current_year - year_offset)
        for month_int in range(current_month, 0, -1):
            month_str = str(month_int).zfill(2)

            ym_str = year_str + month_str

            month_url = "https://www.strava.com/athletes/" + str(
                athlete_id) + "#interval?interval=" + ym_str + "&interval_type=month&chart_type=miles&year_offset=" + str(
                year_offset)
            month_url_ls.append(month_url)

        year_str = str(current_year - year_offset - 1)
        for month_int in range(12, current_month, -1):
            month_str = str(month_int).zfill(2)

            ym_str = year_str + month_str

            month_url = "https://www.strava.com/athletes/" + str(
                athlete_id) + "#interval?interval=" + ym_str + "&interval_type=month&chart_type=miles&year_offset=" + str(
                year_offset)
            month_url_ls.append(month_url)
    return month_url_ls


def activities_scraper(soup, browser, athlete_id):
    output = {}

    activity_ls = []
    challenge_ls = []
    group_activity_ls = []

    try:
        offset_ls = soup.find("div", {"class": "drop-down-menu drop-down-sm enabled"}).find("ul", {
            "class": "options"}).find_all("li")

        month_url_ls = month_url_generator(athlete_id, len(offset_ls))

        # The example url below is just for debugging
        # month_url_ls = ["https://www.strava.com/athletes/7#interval?interval=201606&interval_type=month&chart_type=miles&year_offset=0"]

        for month_url in month_url_ls:
            month_soup = make_soup(month_url, browser)
            """
            The chunk below is to scrape individual activity records
            """
            try:
                activity_entries = month_soup.find_all("div", {"class": "activity entity-details feed-entry"})
                for act_entry in activity_entries:
                    act_a = act_entry.find("h3", {"class": "entry-title"}).find("a", {"class": "minimal"})
                    # act_name = act_a.get_text().encode('utf8')
                    act_url = act_a['href']
                    act_id = act_url.split("activities/")[-1]
                    # activity_ls.append({"name" : act_name, "id" : act_id}) # comment it out if no need to store activity names
                    activity_ls.append(act_id)
            except:
                pass
            """
                The chunk below is to scrape group activity records. Athletes can team up but post a group activity seperately.
                Strava currently provides feed of group activities displaying all involved users' versions of group activities.
            """
            try:
                group_activity_entries = month_soup.find_all("div", {"class": "feed-entry group-activity"})
                for group_act_entry in group_activity_entries:
                    list_athletes = group_act_entry.find("ul", {"class": "list-athletes"})
                    entity_details = list_athletes.find_all("li", {"class": "entity-details"})

                    group_activity = []
                    for entity in entity_details:
                        indi_activity_id = entity['id'].split("-")[-1]
                        indi_athlete_id = \
                            entity.find("a", {"class": "avatar avatar-athlete avatar-default"})['href'].split(
                                "athletes/")[
                                -1]

                        group_activity.append({"athlete_id": indi_athlete_id, "activity_id": indi_activity_id})
                    group_activity_ls.append(group_activity)
            except:
                pass
            """
                The chunk below is to scrape challenges accomplished by athletes.
            """
            try:
                challenge_entries = month_soup.find_all("div", {"class": "challenge feed-entry"})
                for cha_entry in challenge_entries:
                    cha_a = cha_entry.find("h3", {"class": "entry-title"}).find("a", {"class": "minimal"})
                    cha_name = cha_a.get_text().encode('utf8')
                    cha_url = cha_a['href']
                    challenge_ls.append({"name": cha_name, "url": cha_url})
            except:
                pass

    except AttributeError:
        pass

    output = {
        "individual_activity": activity_ls,
        "group_activity": group_activity_ls,
        "challenge": challenge_ls
    }
    return output


def followings_scraper(browser, athlete_id, type_str='following'):
    following_ath_id_ls = []
    privacy_setting = False
    try:
        url = "https://www.strava.com/athletes/" + str(athlete_id) + "/follows?type=" + type_str
        soup = make_soup(url, browser)
        # get how many pages
        try:
            page_soup_ls = soup.find("ul", {"class": "pagination"}).find_all("a")
            page_num = int(page_soup_ls[-2].get_text())
        except AttributeError:
            page_num = 1

        for i in range(1, page_num + 1):
            pagination_url = "https://www.strava.com/athletes/" + str(athlete_id) + "/follows?page=" \
                             + str(i) + "&type=" + type_str
            soup = make_soup(pagination_url, browser)
            followings = soup.find("ul", {"class": "following list-athletes with-menu show-actions"}).find_all("li")
            following_ath_id_ls = [following.attrs['data-athlete-id'] for following in followings]
    except AttributeError:
        privacy_setting = True

    return following_ath_id_ls, privacy_setting


def write_data_to_file(data, filepath):
    print('Writing to file ' + filepath)
    print(data)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def main():
    # Could set PhantomJS as the browswer:browser = webdriver.PhantomJS()

    # for mac location
    # browser = webdriver.Firefox(executable_path='/usr/local/bin/geckodriver')

    # for windows location
    browser = webdriver.Firefox(executable_path=r"C:\Users\Aman\geckodriver.exe")

    browser.get('https://www.strava.com/login')

    username = browser.find_element_by_id("email")
    password = browser.find_element_by_id("password")

    username.send_keys("aman.arya524@gmail.com")
    password.send_keys("Kumar2150")
    login_attempt = browser.find_element_by_xpath("//*[@type='submit']")
    login_attempt.submit()
    time.sleep(3)

    # Now, able to get to the data and start to scrape
    BASE_URL = "http://www.strava.com/athletes/"

    # # The id and size below is just for testing
    start_athlete_id = 4182387
    sample_size = 1
    user_ids = range(start_athlete_id, start_athlete_id + sample_size)

    # activity = pd.read_csv('activity.csv')
    # user_ids = list(activity['athlete.id'])

    user_data = []
    count = 1

    for user_id in user_ids:
        print(user_id, count)
        page = BASE_URL + str(user_id)
        soup = make_soup(page, browser)
        try:
            alert = soup.find("div", {"class": "messages"}).get_text().replace('\n', '')
            if alert == "The requested athlete could not be found":
                user_one = {
                    "athlete-profile": 'null',
                    "social-stats": 'null',
                    "activity-stats": 'null',
                    "activity": 'null',
                    "followings": 'null',
                    "followers": 'null',
                    "privacy_setting": 'null'
                }
                user_data.append(user_one)
                continue
        except:
            pass

        # 1. Scrape the athlete's brief profile
        ath_profile_one, flag = profile_scraper(soup, user_id)
        if flag == True:
            continue
        # 2. Scrape the athlete's social stats
        social_stats_one = soc_stats_scraper(soup)
        # 3. Scrape the athlete's activity stats
        activity_stats_one = act_stats_scraper(soup)
        # 4. Scrape activity entries
        activities_one = activities_scraper(soup, browser, user_id)
        # 5. Scrape who the user is following
        following_one, privacy_setting = followings_scraper(browser, user_id, 'following')
        # 6. Scrape who is following the user
        follower_one = followings_scraper(browser, user_id, 'followers')

        user_one = {
            "athlete-profile": ath_profile_one,
            "social-stats": social_stats_one,
            "activity-stats": activity_stats_one,
            "activity": activities_one,
            "followings": following_one,
            "followers": follower_one,
            "privacy_setting": privacy_setting
        }

        user_data.append(user_one)
        if count % 10 == 0:
            write_data_to_file(user_data, "strava_scraped_data.json")

        count += 1



    write_data_to_file(user_data, "strava_scraped_data.json")


if __name__ == '__main__':
    main()
