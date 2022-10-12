

###
# connecting to the iRats and navigating the website (iRats) automatically to load needed data
# e.g. Mice, Projects, Licences
# 
###

from csv import reader
from flaskr.tables import *
from sqlalchemy import desc
from sqlalchemy import engine
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager
import getpass, os, time, json
from pathlib import Path
from datetime import datetime, timedelta
from sys import platform
if platform == "linux":
    from pyvirtualdisplay import Display

# irats_username = 'mfabre'
# irats_pw = 'M199701'  

# irats_username = 'roman'
# irats_pw = 'megu0210'

# irats_username = 'durnovv'
# irats_pw = 'qQ1234567'


## ??? ##
def interprete(entry, display_mode=False, type=None):
    if not entry or entry.content=="":
        return None
    if not type:
        type =  entry.entry_format      
    if type=="float" or type=="number":
        return(float(entry.content))
    elif type=="int":
        return(int(entry.content))
    elif type=="datetime-local":
        time = datetime.strptime(entry.content, "%Y-%m-%dT%H:%M") 
        if display_mode:
            time = time.strftime("%A, %d. %B %Y %I:%M%p")
        return(time)
    elif type=="date":
        time = datetime.strptime(entry.content, "%Y-%m-%d") 
        if display_mode:
            time = time.strftime("%A, %d. %B %Y")
        return(time)
    elif type=="datehour":
        time = datetime.strptime(entry.content, "%Y-%m-%dT%H") 
        if display_mode:
            time = time.strftime("%A, %d. %B %Y %I%p")
        return(time)
    elif type=="bool":
        if "true" in entry.content.lower():
            return(True)
        elif "false" in entry.content.lower():
            return(False)
        else:
            return(entry.content)
    else:
        return(entry.content)

def check_irats_credentials(username, password):
    print("FUNCTION: check_irats_credentials")
    run_headless = False # do not show the browser window

    if platform == "linux":
        display = Display(visible=0, size=(800, 800))  
        display.start()
        # driver = webdriver.Chrome()         
    # below parameters probably need not be changed
    irats_url = "https://irats.uzh.ch/irats/lab/" # the login URL for iRats


    chrome_options = Options()
    chrome_options.add_argument("--disable-extensions") # disables extensions
    chrome_options.add_argument("--disable-gpu") # disable GPU support
    if platform == "linux": 
        chrome_options.add_argument("--no-sandbox") # linux only
    if run_headless:
        chrome_options.add_argument("--headless") # run in headless mode (no window)

    # start webdriver
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)

    driver.get(irats_url)
    assert "Tierverwaltung" in driver.title

    log_attempts=0
    connected = False
    while not connected and log_attempts<2:
        username_entry = driver.find_element_by_name("userName")
        password_entry = driver.find_element_by_name("passwd")

        username_entry.send_keys(username)
        password_entry.send_keys(password)

        driver.find_element_by_name("loginButton").click()

        wait = 0
        while not "Animal Interface" in driver.title and wait<20:
            time.sleep(0.1)
            wait +=1
        
        if "Animal Interface" in driver.title:
            connected = True
        else:
            connected = False

        log_attempts+=1
        
    if connected:

        time.sleep(2)
        driver.find_element_by_link_text("Personal information").click()
        first_name = driver.find_element_by_xpath("//*[.='First name: ']/following-sibling::td").text
        last_name = driver.find_element_by_xpath("//*[.='Family name: ']/following-sibling::td").text
        driver.find_element_by_link_text("Log out").click()
        time.sleep(0.1)
        driver.close()
        return [first_name, last_name]
    else:
        time.sleep(0.1)
        driver.close()
        return None

def goto_iratsmain(username = 'roman', password = 'megu0210', chrome_options=None):
    print("FUNCTION: goto_iratsmain")
    run_headless = False # do not show the browser window

    if platform == "linux":
        display = Display(visible=0, size=(800, 800))  
        display.start()
        # driver = webdriver.Chrome()         
    # below parameters probably need not be changed
    irats_url = "https://irats.uzh.ch/irats/lab/" # the login URL for iRats

    if not chrome_options:
        chrome_options = Options()
    chrome_options.add_argument("--disable-extensions") # disables extensions
    chrome_options.add_argument("--disable-gpu") # disable GPU support
    if platform == "linux": 
        chrome_options.add_argument("--no-sandbox") # linux only
    if run_headless:
        chrome_options.add_argument("--headless") # run in headless mode (no window)

    # start webdriver
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)

    driver.get(irats_url)
    assert "Tierverwaltung" in driver.title

    username_field = driver.find_element_by_name("userName")
    password_field = driver.find_element_by_name("passwd")

    username_field.send_keys(username)
    password_field.send_keys(password)

    driver.find_element_by_name("loginButton").click()

    while not "Animal Interface" in driver.title:
        time.sleep(0.1)

    time.sleep(2)

    return(driver)

def irats_fetch():
    # print("FUNCTION: irats_fetch()")
    chrome_options = Options()
    if platform=="win32":
        download_dir = Path().resolve().parents[0]
    else:
        download_dir = "/var/www/mfabre/webapp"

    #'C:\\Users\\maxim\\Documents\\ETH\\Micebook'
    if platform == "win32": 
        download_dir = str(download_dir).replace("/", "\\")
    else:
        download_dir = str(download_dir)


    

    # experimental options
    prefs = {'download.default_directory' : download_dir}
    chrome_options.add_experimental_option('prefs', prefs)

    driver = goto_iratsmain(chrome_options=chrome_options)

    search_config = "all_columns" # search config to be loaded in Animal search interface

    csv_filename = 'configurableAnimal.csv'

    driver.find_element_by_link_text("Animals").click()
    config_select = Select(driver.find_element_by_name("configId"))
    config_select.select_by_visible_text(search_config)

    search_button = driver.find_element_by_id("animalSearchButton")
    search_button.click()

    # now wait until the search has completed
    while search_button.is_enabled() is False:
        time.sleep(0.1)

    path = os.path.join(download_dir, csv_filename)

    # check if a file exists already and delete it
    if os.path.exists(path):
        os.remove(os.path.join(download_dir, csv_filename))
        # print('Deleted existing file %s' % (os.path.join(download_dir, csv_filename)))

    # download CSV file
    driver.execute_script("createConfigurableAnimalCSVReportFunc('/irats/report/configurableAnimal.csv');")
    # wait for download to complete
    while not os.path.exists(path):
        time.sleep(0.1)

    # # add date / time to the downloaded file
    # date_time = datetime.datetime.now().strftime("__%Y-%m-%d__%H-%M-%S")
    # csv_file = os.path.join(download_dir, csv_filename)
    # csv_file_rename = csv_file.replace('.csv', date_time + '.csv')
    # os.rename(csv_file, csv_file_rename)

    # print("Downloaded search results file %s" % (csv_file_rename))

    # log out of irats
    driver.find_element_by_link_text("Log out").click()

    # close the driver
    driver.close()

def find_mouse_pda(id):
    print("FUNCTION: find_mouse_pda")
    mouse = Mice.query.filter(Mice.id==id).first()
    irats_id = mouse.irats_id
    cage = mouse.cage

    driver = goto_iratsmain()

    driver.find_element_by_link_text("PDA interface").click()
    time.sleep(2)

    cage_search = driver.find_element_by_name("cageId")
    cage_search.send_keys(cage)
    cage_form = driver.find_element_by_name("cageForm")
    cage_form.submit()
    time.sleep(1)


    
    try:
        animal = driver.find_element_by_xpath("//td[contains(.,'"+irats_id+"')]/input")
        animal.click()
    except:
        return None
        # i=0
        # rows = len(driver.find_elements_by_xpath('test'+"/tr"))
        # animal_details = driver.find_element_by_xpath("//form[@name='animalForm']/table/tr[2]/td[2]/table/tr/td")
        # while (not animal) and animal_details:
        #     animal_details.click()
        #     time.sleep(1)
        #     system_id = driver.find_element_by_xpath("//*[.='System ID:']/following-sibling::td").text
        #     driver.back()
        #     time.sleep(1)

        #     if system_id==irats_id:
        #         animal = driver.find_element_by_xpath("//form[@name='animalForm']/table/tr["+str(i+2)+"]/td")
        #     else:
        #         i+=1
        #         animal_details = driver.find_element_by_xpath("//form[@name='animalForm']/table/tr["+str(i+2)+"]/td[2]/table/tr/td")

        # if not animal:
        #     return None
        # else:
        #     animal.click()


    return driver

def read_severity(id):
    print("FUNCTION: read_severity")
    driver = find_mouse_pda(id)

    if not driver:
        return None

    new_task_select = Select(driver.find_element_by_name("orderType"))
    new_task_select.select_by_visible_text("Advanced Transfer")

    animal_form = driver.find_element_by_name("animalForm")
    animal_form.submit()
    time.sleep(1)    

    severity_select = Select(driver.find_element_by_name("newSeverity"))
    severity = severity_select.first_selected_option.text

    driver.find_element_by_name("mainForm").submit()
    time.sleep(0.5)
    driver.find_element_by_name("logoutForm").submit()
    # close the driver
    driver.close()

    return severity

def write_advance_transfer(id, licence=None, project=None, severity=None, status=None, complete=True):
    print("FUNCTION: write_advance_transfer")
    if complete:
        driver = find_mouse_pda(id)

        if not driver:
            return None
        

        new_task_select = Select(driver.find_element_by_name("orderType"))
        new_task_select.select_by_visible_text("Advanced Transfer")

        animal_form = driver.find_element_by_name("animalForm")
        animal_form.submit()
        time.sleep(1)

        if licence:
            licence_select = Select(driver.find_element_by_name("newLicenceId"))
            licence_select.select_by_visible_text(licence)
            time.sleep(0.5)
        if project:
            project_select = Select(driver.find_element_by_name("newResearchId"))
            project_select.select_by_visible_text(project) 
            time.sleep(0.5)       
        if severity:
            severity_select = Select(driver.find_element_by_name("newSeverity"))
            severity_select.select_by_visible_text(severity)
            time.sleep(0.5)
        if status:
            status_select = Select(driver.find_element_by_name("newAnimalStatus"))
            status_select.select_by_visible_text(status) 
            time.sleep(0.5)

        transfer_form = driver.find_element_by_name("workForm")

    
        transfer_form.submit()
        time.sleep(1)

        driver.find_element_by_name("mainForm").submit()
        time.sleep(0.5)
        driver.find_element_by_name("logoutForm").submit()

        # close the driver
        driver.close()


    return True


def note_euthanasia(id, sever):
    print("FUNCTION: note_euthanasia")
    return None

def download_licences():
    print("FUNCTION: download_licences")
    driver = goto_iratsmain()

    driver.find_element_by_link_text("Licences").click()
    time.sleep(2)

    licence_search_form = driver.find_element_by_name("searchForm")
    licence_search_form.submit()
    time.sleep(1)

    # result_table_path = "//table/tbody/tr[3]/td[1]/table/tbody/tr/td[1]/table/tbody/tr/td/table/tbody"
    result_table_path = "//table[@class='taulu']/tbody"

    line = driver.find_element_by_xpath(result_table_path+"/tr[2]")
    Licences_list = []
    i=2
    rows = len(driver.find_elements_by_xpath(result_table_path+"/tr"))
    for i in range(2,rows+1):
        licence_dict={}
        licence_dict['number']=driver.find_element_by_xpath(result_table_path+"/tr["+str(i)+"]/td[2]").text
        licence_dict['name']=driver.find_element_by_xpath(result_table_path+"/tr["+str(i)+"]/td[3]").text
        licence_dict['holder']=driver.find_element_by_xpath(result_table_path+"/tr["+str(i)+"]/td[4]").text
        licence_dict['valid_through']=driver.find_element_by_xpath(result_table_path+"/tr["+str(i)+"]/td[7]").text
        Licences_list.append(Licences(**licence_dict))
        # i+=1
        # line = driver.find_element_by_xpath(result_table_path+"/tr["+str(i)+"]")

    for licence in Licences_list:
        if not Licences.query.filter(Licences.number==licence.number).first():
            db.session.add(licence)
        else:
            old_licence = Licences.query.filter(Licences.number==licence.number).first()
            old_licence.name = licence.name
            old_licence.holder = licence.holder
            old_licence.valid_through = licence.valid_through

    db.session.commit()

    driver.find_element_by_link_text("Log out").click()

    # close the driver
    driver.close()

def download_user_projects(user_id):
    print("FUNCTION: download_user_projects")
    driver = goto_iratsmain()

    driver.find_element_by_link_text("Licences").click()
    time.sleep(2)
    driver.find_element_by_link_text("Projects").click()
    time.sleep(2)

    user = Users.query.filter(Users.id==user_id).first()

    user_search = driver.find_element_by_xpath("//*[.='User: ']/following-sibling::td/div[@class='searchable-select']/div[@class='searchable-select-holder']")
    user_search.click()
    user_input = driver.find_element_by_xpath("//*[.='User: ']/following-sibling::td/div[@class='searchable-select']/div[@class='searchable-select-dropdown']/input") #[@class='searchable-select-input')
    user_input.send_keys(user.full_name.split(" ")[0])
    time.sleep(2)
    # user_select = Select(driver.find_element_by_id("selectedInvId"))
    # select_options = user_select.options
    	
    split_user_name = user.full_name.split(" ")
    # for option in select_options:
    #     investigator = option.get_attribute('text').lower()
    #     if all([(split_user_name[i] in investigator) for i in range(len(split_user_name))]):
    #     
    #         value = option.get_attribute('value')
    #         break
    # 
    # user_select.select_by_value(value)

    select_path = "//div[contains(@class,'searchable-select-item')"
    full_select_path = select_path + "".join([" and contains(text(),'"+name_part+"')" for name_part in split_user_name]) + "]"
    user_select = driver.find_element_by_xpath(full_select_path)
    user_select.click()
    # user_select.select_by_visible_text(user_option)


    licence_search_form = driver.find_element_by_name("searchForm")
    licence_search_form.submit()
    time.sleep(1)

    result_table_path = "//table[@class='taulu']/tbody"
    Projects_list = []
    rows = len(driver.find_elements_by_xpath(result_table_path+"/tr"))
    project_dict={'user_id':user_id}
    for i in range(2,rows+1):
        licence_number = driver.find_element_by_xpath(result_table_path+"/tr["+str(i)+"]/td[1]").text
        licence = Licences.query.filter(Licences.number==licence_number).first()
        if licence:
            project_dict['licence_id'] = licence.id
            project_dict['name']=driver.find_element_by_xpath(result_table_path+"/tr["+str(i)+"]/td[3]").text
            project_dict['description']=driver.find_element_by_xpath(result_table_path+"/tr["+str(i)+"]/td[5]").text
            Projects_list.append(Projects(**project_dict))

    for project in Projects_list:
        if not Projects.query.filter(Projects.name==project.name, Projects.user_id==project.user_id).first():
            db.session.add(project)
        else:
            old_project = Projects.query.filter(Projects.name==project.name, Projects.user_id==project.user_id).first()
            old_project.description = project.description
            old_project.licence_id = project.licence_id

    db.session.commit()

    driver.find_element_by_link_text("Log out").click()

    # close the driver
    driver.close()

def download_licences_and_projects(user_id):
    print("FUNCTION: download_licences_and_projects")
    driver = goto_iratsmain()

    driver.find_element_by_link_text("Licences").click()
    time.sleep(2)

    licence_search_form = driver.find_element_by_name("searchForm")
    licence_search_form.submit()
    time.sleep(1)

    # result_table_path = "//table/tbody/tr[3]/td[1]/table/tbody/tr/td[1]/table/tbody/tr/td/table/tbody"
    result_table_path = "//table[@class='taulu']/tbody"

    line = driver.find_element_by_xpath(result_table_path+"/tr[2]")
    Licences_list = []
    i=2
   
    rows = len(driver.find_elements_by_xpath(result_table_path+"/tr"))
    for i in range(2,rows+1):
        licence_dict={}
        licence_dict['number']=driver.find_element_by_xpath(result_table_path+"/tr["+str(i)+"]/td[2]").text
        licence_dict['name']=driver.find_element_by_xpath(result_table_path+"/tr["+str(i)+"]/td[3]").text
        licence_dict['holder']=driver.find_element_by_xpath(result_table_path+"/tr["+str(i)+"]/td[4]").text
        licence_dict['valid_through']=driver.find_element_by_xpath(result_table_path+"/tr["+str(i)+"]/td[7]").text
        Licences_list.append(Licences(**licence_dict))
        # i+=1
        # line = driver.find_element_by_xpath(result_table_path+"/tr["+str(i)+"]")

    for licence in Licences_list:
        if not Licences.query.filter(Licences.number==licence.number).first():
            db.session.add(licence)
        else:
            old_licence = Licences.query.filter(Licences.number==licence.number).first()
            old_licence.name = licence.name
            old_licence.holder = licence.holder
            old_licence.valid_through = licence.valid_through

    db.session.commit()


    

  
    driver.find_element_by_link_text("Projects").click()
    time.sleep(2)
    
  
    user = Users.query.filter(Users.id==user_id).first()


    user_search = driver.find_element_by_xpath("//*[.='User: ']/following-sibling::td/div[@class='searchable-select']/div[@class='searchable-select-holder']")
 
    user_search.click()
    user_input = driver.find_element_by_xpath("//*[.='User: ']/following-sibling::td/div[@class='searchable-select']/div[@class='searchable-select-dropdown']/input") #[@class='searchable-select-input')
    user_input.send_keys(user.full_name.split(" ")[0])
    time.sleep(2)
  
    	
    split_user_name = user.full_name.split(" ")

    #split_user_name = ['Boehringer Roman']

    #select_path = "//div[contains(@class,'searchable-select-item')"
    select_path = "//*[.='User: ']/following-sibling::td/div[@class='searchable-select']/div[@class='searchable-select-dropdown']/div[@class='searchable-scroll']/div[@class='searchable-select-items']/div[contains(@class,'searchable-select-item')"

    full_select_path = select_path + "".join([" and contains(text(),'"+name_part+"')" for name_part in split_user_name]) + "]"

    user_select = driver.find_element_by_xpath(full_select_path)

    time.sleep(1)

    user_select.click()


    licence_search_form = driver.find_element_by_name("searchForm")
    licence_search_form.submit()
    time.sleep(1)

   

    result_table_path = "//table[@class='taulu']/tbody"
    Projects_list = []
    rows = len(driver.find_elements_by_xpath(result_table_path+"/tr"))
    project_dict={'user_id':user_id}
    for i in range(2,rows+1):
        licence_number = driver.find_element_by_xpath(result_table_path+"/tr["+str(i)+"]/td[1]").text
        licence = Licences.query.filter(Licences.number==licence_number).first()
        if licence:
            project_dict['licence_id'] = licence.id
            project_dict['name']=driver.find_element_by_xpath(result_table_path+"/tr["+str(i)+"]/td[3]").text
            project_dict['description']=driver.find_element_by_xpath(result_table_path+"/tr["+str(i)+"]/td[5]").text
            Projects_list.append(Projects(**project_dict))

    for project in Projects_list:
        if not Projects.query.filter(Projects.name==project.name, Projects.user_id==project.user_id).first():
            db.session.add(project)
        else:
            old_project = Projects.query.filter(Projects.name==project.name, Projects.user_id==project.user_id).first()
            old_project.description = project.description
            old_project.licence_id = project.licence_id

 
    db.session.commit()

    driver.find_element_by_link_text("Log out").click()

    driver.close()
   


def Load_Viruses(file_name, db, Viruses, update=False):
    print("FUNCTION: load_viruses")
    with open(file_name) as csv_file:
        data = reader(csv_file, delimiter=';')

        initial_row = 0
        columns = [['ID', 'name'], ['Container','container'], ['Producer','producer'], ['Virus construct','construct'], ['Serotype','serotype'], ['Promoter','promoter'], ['Dependency','dependency'], ['Expressing Protein','expressing_protein'], ['Fluorophob','fluorophob'], ['Titer','titer'], ['Dilution','dilution']]
        present_columns = []
        for row in data:
            initial_row += 1
            if 'ID' in row:
                for column in columns:
                    if column[0] in row:
                        present_columns.append(column + [row.index(column[0])])
                break


        for row in data:
            virus = Viruses.query.filter(Viruses.name == row[present_columns[0][2]]).first()
            if not virus:
                args = {}
                for column in present_columns:
                    args[column[1]] = row[column[2]]
                new_virus = Viruses(**args)
                db.session.add(new_virus)
            elif update:
                args = {}
                for column in present_columns:
                    args[column[1]] = row[column[2]]
                #Viruses.update().filter(Viruses.id==virus.id).values(**args)
                db.session.query(Viruses).filter(Viruses.name == row[present_columns[0][2]]).update(args)

        db.session.commit()

def hasNumber(inputString):
    # print("FUNCTION: hasNumber")
    return any(char.isdigit() for char in inputString)

def hasLetter(inputString):
    # print("FUNCTION: hasLetter")
    return any(char.isalpha() for char in inputString)

def hasNumberANDLetter(inputString):
    # print("FUNCTION: hasNumberANDLetter")
    return hasNumber(inputString) and hasLetter(inputString)


def Load_Mice(file_name, db, Mice, update=True):
    print("FUNCTION: Load_Mice")
    
    # print(pd.read_csv(file_name))
    with open(file_name, encoding='latin-1') as csv_file:
        # print(csv_file)
        data = reader(csv_file, delimiter=';')

        columns = [['System ID','system_id'], ['Animal ID', 'irats_id'], ['Project','licence'], ['Cage','cage'], ['Strain','strain'], ['Genotype','genotype'], ['Gender','gender'], ['Date of birth','birthdate'], ['Status','status'], ['Investigator','investigator'], ['Room','room_id']]
        present_columns = []
        for row in data:
            if 'Animal ID' in row:
                for column in columns:
                    if column[0] in row:
                        present_columns.append(column + [row.index(column[0])])
                break
        print(present_columns)
        i = 0
        for row in data:
            i+=1
            mouse = Mice.query.filter(Mice.system_id == row[present_columns[0][2]]).first()
            
            if not mouse:
            
                args = {}
                for column in present_columns:
            
                    args[column[1]] = row[column[2]]
                if args['irats_id'] =="" or not hasNumberANDLetter(args['irats_id']):
                    args['irats_id'] = args['system_id']
                new_mouse = Mice(**args)
                db.session.add(new_mouse)
            elif update:
                args = {}
                for column in present_columns:
                    args[column[1]] = row[column[2]]
                if args['irats_id'] =="" or not hasNumberANDLetter(args['irats_id']):
                    args['irats_id'] = args['system_id']
                #mouse.update(args)
                print(args)
                db.session.query(Mice).filter(Mice.system_id == row[present_columns[0][2]]).update(args)
        db.session.commit()




# def email_notification():


# if __name__ == "__main__":

