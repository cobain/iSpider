#coding:utf8
from selenium import webdriver
from time import sleep
from multiprocessing import Process
import SocketServer
import requests
import json
import re
import os


def fetch_all_page_url():
    #获取所有带gif链接的的主页面
    url_list = []
    print '开始获取所有带gif链接的主页面...'

    browser = webdriver.PhantomJS()
    browser.get('http://tu.duowan.com/m/bxgif')

    #获取所有的img元素
    li = browser.find_elements_by_xpath('//ul//em/a')

    print '.',

    li_old_sum = 0
    li_new_sum = 1

    while li_old_sum != li_new_sum:
        li_old_sum = len(li)

        #滚动条拉到底
        browser.execute_script("window.scrollBy(0,3000)","")
        sleep(1)

        #获取所有的img元素
        li = browser.find_elements_by_xpath('//ul/li/em/a')
        li_new_sum = len(li)

        print '.',

    #处理掉失效的url
    for element in li:
        url = element.get_attribute('href')
        num = re.search(r'\d+',url).group()
        if int(num) > 93181:
            url_list.append(url)

    browser.close()
    print '获取完成。'
    return url_list

def download_gif(gif_dir,url):
    num = 0
    while 1:
        try:
            s = requests.get(url,stream=True)
            name = os.path.basename(url)
            with open(os.path.join(gif_dir,name),'wb') as f:
                f.write(s.content)
            break
        except:
            if num > 3:
                break
            num += 1
            print '{0}下载失败,重试{1}'.format(url,num)
            continue

def multi_download_fig(gif_dir,url_list):
    process_list = []
    for i in url_list:
        process_list.append(Process(target=download_gif,args=(gif_dir,i,)))
    for i in process_list:
        i.start()

class MyTCPHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        print 'worker <{0}> 连接了过来:'.format(self.client_address[0])
        self.task_num = 0
        self.data = self.request.recv(1).strip()
        if self.data == '1':
            if all_task:
                task = all_task.pop()
                data_length = len(json.dumps(task))
                data_length = (5 - len(str(data_length))) * '0' + str(data_length)
                self.request.sendall(data_length)
                self.request.sendall(json.dumps(task))
                print '派发了一份任务给 worker <{0}>'.format(self.client_address[0])
            else:
                self.request.sendall('99999')
        elif self.data == '2':
            data = self.request.recv(8).strip()
            if data == 'start':
                print 'worker <{0}> 开始工作了'.format(self.client_address[0])
            elif data == 'finish':
                print 'worker <{0}> 工作完成了'.format(self.client_address[0])
        elif self.data == '3':
            self.task_num += 1
            data_length = self.request.recv(5).strip()
            data = json.loads(self.request.recv(int(data_length)).strip())
            print '从 worker <{0}> 得到了一份gif链接列表，开始下载...'.format(self.client_address[0])
            multi_download_fig(gif_dir,data)
            self.task_num -= 1
        else:
            if self.task_num == 0 and all_task == []:
                print '任务全部完成了'
                os.exit(0)

if __name__ == '__main__':
    all_task = fetch_all_page_url()
    # all_task = []
    gif_dir = 'e:/gif'
    HOST,PORT = "0.0.0.0",6666
    server = SocketServer.ThreadingTCPServer((HOST,PORT),MyTCPHandler)
    server.serve_forever()

