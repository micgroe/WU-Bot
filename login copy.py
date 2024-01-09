from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import requests
import time
import tkinter as tk
import datetime

def calculate_time(Anmeldezeit):
    seconds_before = 5
    enroll_time = time.mktime(time.strptime(Anmeldezeit, '%Y-%m-%d %H:%M:%S'))
    enroll_time = datetime.datetime.fromtimestamp(enroll_time)

    start_time = enroll_time - datetime.timedelta(seconds=seconds_before)
    start_time = time.mktime(start_time.timetuple())
    
    now = time.time()

    time_difference = start_time - now
    print("Waiting")
    time.sleep(time_difference)
    print(f"Starting at time {datetime.datetime.now()}")

def send_login_post_request(s, username, password, LPIS_URL, cookies, headers, POST_URL):
    get_request = s.get(LPIS_URL, cookies=cookies)
    get_request = BeautifulSoup(get_request.text, "html.parser")

    form_element = get_request.find("table", class_="b3k-data")
    parameter_elements = form_element.find_all("input")

    payload = {}
    for parameter in parameter_elements:
        if parameter == parameter_elements[0]:
            payload[parameter["name"]] = username
        elif parameter == parameter_elements[1]:
            payload[parameter["name"]] = password
        elif parameter != parameter_elements[2]:
            payload[parameter["name"]] = parameter.get_attribute("value")


    r = s.post(POST_URL, data = payload, cookies = cookies, headers = headers)
    soup = BeautifulSoup(r.text, 'html.parser')
    
    return soup

def check_errors(s, soup, Vorlesungstitel, URL_ID, window, Vorlesungsnummer):
    global error_row
    table = soup.find("table", class_="b3k-data")
    try:
        target_tr = table.find('span', text=Vorlesungstitel).parent
        get_request_url_element = target_tr.find("a", title = "Lehrveranstaltungsanmeldung")
    except:
        found_label = tk.Label(window, text="LV-Titel nicht gefunden!", fg="red")
        found_label.grid(row=error_row, column=4)
        window.update()

    get_url = get_request_url_element['href']
    get_url = "https://lpis.wu.ac.at/kdcs/bach-"+URL_ID+"/"+get_url
    r = s.get(get_url)
    r = BeautifulSoup(r.text, "html.parser") 

    try:
        number_table = r.find("table", class_="b3k-data")
        number_target_tr = number_table.find("a", text=Vorlesungsnummer).parent.parent
        found_label = tk.Label(window, text="LV gefunden!", fg="green")
        found_label.grid(row=error_row, column=4)
        window.update()
    except:
        found_label = tk.Label(window, text="LV-Nummer nicht gefunden!", fg="red")
        found_label.grid(row=error_row, column=4)
        window.update()

    error_row += 1


def get_lecture_url(soup, Vorlesungstitel, URL_ID):

    table = BeautifulSoup(soup.text, "html.parser")
    table = soup.find("table", class_="b3k-data")
    target_tr = table.findAll('span', text=Vorlesungstitel)
    for element in target_tr:
        if not element.parent.find("span", string = "Fach"):
            get_request_url_element = element.parent.find("a", title = "Lehrveranstaltungsanmeldung")
            get_url = get_request_url_element['href']
            get_url = "https://lpis.wu.ac.at/kdcs/bach-"+URL_ID+"/"+get_url
            return get_url


def send_lecure_get_request(s, get_url, Vorlesungsnummer, URL_ID):
    r = s.get(get_url)
    r = BeautifulSoup(r.text, "html.parser")

    table = r.find("table", class_="b3k-data")
    target_tr = table.find("a", text=Vorlesungsnummer).parent.parent

    cookies = s.cookies
    payload = {}
    for parameter in target_tr.find_all("input"):
        payload[parameter["name"]] = parameter["value"]

    if "DISABLED" not in payload:
        print(f"Parameters found at {datetime.datetime.now()}")
        post_url = "https://lpis.wu.ac.at/kdcs/bach-"+URL_ID+"/SPAN"
        r = s.post(post_url, data=payload, cookies=cookies)
        r = BeautifulSoup(r.text, "html.parser")

        message = r.find("div", class_="b3k_alert_content")
        message = message.find("b").text
        print(message)
        print(f"Post response received at {datetime.datetime.now()}")
    else: 
        print("Parameters not found")


def run(username, password, Anmeldezeit):
    #window.grid(row=6, column=1).destroy()

    url = "https://www.wu.ac.at/studierende/tools-services/lpis/"

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    #options.add_argument("--auto-open-devtools-for-tabs")
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)

    driver.set_window_size(1200, 800)
    driver.get(url)

    cookie_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@class='form-btn form-btn-secondary save-all-cookie-settings']")))

    try:
        cookie_button.click()
        print("cookies clicked")
    except:
        print("not clickable")

    login_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//a[@class='form-btn form-btn-blue']")))

    try:
        login_button.click()
        print("login clicked")
    except:
        print("login not clickable")

    wait = WebDriverWait(driver, 10)
    wait.until(EC.number_of_windows_to_be(2))

    driver.switch_to.window(driver.window_handles[1])

    LPIS_URL = driver.current_url
    URL_ID = LPIS_URL[32:41]
    POST_URL = "https://lpis.wu.ac.at/kdcs/bach-"+URL_ID+"/CID"

    headers = {}

    cookieslist = driver.get_cookies()

    cookies = {cookie['name']: cookie['value'] for cookie in cookieslist}
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Content-Length": "114",
        "Content-Type": "application/x-www-form-urlencoded",
        "Host": "lpis.wu.ac.at",
        "Origin": "https://lpis.wu.ac.at",
        "Referer": LPIS_URL,
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "sec-ch-ua": "'Not.A/Brand';v='8', 'Chromium';v='114', 'Google Chrome';v='114'",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "'macOS'"
    }

    with requests.session() as s:
        r = send_login_post_request(s, username=username, password=password, LPIS_URL=LPIS_URL, cookies=cookies, headers=headers, POST_URL=POST_URL)

        calculate_time(Anmeldezeit=Anmeldezeit)
        executor = ThreadPoolExecutor(max_workers=6)
        futures = []

        while True:   
            current_time = time.time()
            desired_time = desired_time = time.mktime(time.strptime(Anmeldezeit, '%Y-%m-%d %H:%M:%S'))
            time_difference = desired_time - current_time
            if time_difference <= 0:
                print("Timeout reached.")
                break  

            for i in saved_lectures:
                lecture_url = get_lecture_url(soup=r, Vorlesungstitel=i[0], URL_ID=URL_ID)
            
                future = executor.submit(send_lecure_get_request(s=s, get_url=lecture_url, Vorlesungsnummer=i[1], URL_ID=URL_ID))
                futures.append(future)

            time.sleep(0.5)
        
    for future in futures:
        future.result()

    executor.shutdown()

    driver.quit()

window = tk.Tk()
window.title("WU Bot")
window.geometry("900x300")

error_row = 0

# Create and place the input fields
label_username = tk.Label(window, text = "Martrikelnummer:")
label_username.grid(row=0, column=0)
entry_username = tk.Entry(window)
entry_username.grid(row=0, column=1)

label_password = tk.Label(window, text = "Passwort:")
label_password.grid(row=1, column=0)
entry_password = tk.Entry(window)
entry_password.grid(row=1, column=1)

label_lecture_name = tk.Label(window, text="Vorlesungstitel:", )
label_lecture_name.grid(row=2, column=0)
entry_lecture_name = tk.Entry(window)
entry_lecture_name.grid(row=2, column=1)

label_lecture_number = tk.Label(window, text="Vorlesungsnummer:")
label_lecture_number.grid(row=3, column=0)
entry_lecture_number = tk.Entry(window)
entry_lecture_number.grid(row=3, column=1)

label_time = tk.Label(window, text = "Anmeldezeit (YYYY-MM-DD hh:mm:ss)")
label_time.grid(row=4, column=0)
entry_time = tk.Entry(window)
entry_time.grid(row=4, column=1)

saved_lectures = []
def add_lecture():
    lecture_name = entry_lecture_name.get()
    lecture_number = entry_lecture_number.get()
    lecture_time = entry_time.get()

    current_row = len(saved_lectures)
    saved_lectures.append([lecture_name, lecture_number, lecture_time])

    new_lecture_label = tk.Label(window, text=f"{lecture_number} {lecture_name} {lecture_time}")
    new_lecture_label.grid(row=current_row, column=2)

    delete_button = tk.Button(window, text="Löschen", command=lambda row=current_row: delete_lecture(row))
    delete_button.grid(row=current_row, column=3)

def delete_lecture(row):
    del saved_lectures[row]
    # Destroy widgets in the specified row
    for widget in window.grid_slaves():
        if int(widget.grid_info()["row"]) == row:
            if int(widget.grid_info()["column"]) == 2 or int(widget.grid_info()["column"]) == 3:
                widget.grid_forget()
    
    # Move widgets below the deleted row one row up
    for widget in window.grid_slaves():
        if int(widget.grid_info()["row"]) > row:
            if int(widget.grid_info()["column"]) == 2 or int(widget.grid_info()["column"]) == 3:
                if widget.cget("text") != "Anmelden":
                    print("true")
                    widget.grid(row=widget.grid_info()["row"] - 1, column=widget.grid_info()["column"])

    global row_count
    row_count -= 1

row_count = 0

# Create and place the submit button
button_add = tk.Button(window, text="Hinzufügen", command=add_lecture)
button_add.grid(row=5, column=1)

button_run = tk.Button(window, bg="blue", text="Anmelden", command=lambda: run(entry_username.get(), entry_password.get(), entry_time.get()))
button_run.grid(row=5, column=2)

window.mainloop()

#Accounting & Management Control III
#0541
#2023-09-17 22:00:00

#Betriebliche Informationssysteme II
#1356
