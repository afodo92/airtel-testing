from parameters.global_parameters import Jira as JIRAPARAMS
from libs.libs_jira.JiraCore import JiraCore

if __name__ =="__main__":
    jira = JiraCore(JIRAPARAMS["host"], JIRAPARAMS["user"], JIRAPARAMS["pass"])
    #jira.attach_file(item_key="VELO-1",file_path="D:\\Workspaces\\spirent-project\\logs\\f_LogsSessions\\test.html")
    print(jira.get_item_details("VELO-1"))
    # print(jira.get_item_details("VELO-2"))
    # print(jira.get_item_details("VELO-3"))
    # print(jira.get_item_details("VELO-4"))
    # print(jira.get_item_details("VELO-5"))
    # print(jira.get_item_details("VELO-6"))
    # print(jira.get_project_details(project_key="VELO"))
    #print(jira.get_project_details("VELO"))