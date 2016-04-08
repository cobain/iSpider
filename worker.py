#!python
#coding:utf8
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from time import sleep
from multiprocessing import Process
from multiprocessing import Queue
import os
import json
import socket


def fetch_task_from_manager(host,port):
    #请求任务数据
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    while 1:
        try:
            s.connect((host,port))
            break
        except Exception:
            print '连接manager失败5秒后重试'
            sleep(5)
            continue
    print '连接manager成功'

    s.sendall('1')
    data_length = s.recv(5)
    if data_length == '99999':
        print '任务没了，等待任务提供'
        sleep(5)
        return fetch_task_from_manager(host,port)
    data = s.recv(int(data_length))
    return json.loads(data)

# def send_result_to_manager(url_list):


def fetch_gif_url(url,count,gif_url_list_q):
    try:
        print '任务 {0} 开始...'.format(count)
        browser1 = webdriver.PhantomJS()
        # print '{0}#p{1}'.format(gif_url,count)
        browser1.get('{0}#p{1}'.format(url,count))
        #智能等待
        WebDriverWait(browser1,7).until(lambda x:os.path.basename(x.find_element_by_xpath('//img[@alt]').get_attribute('src')) != 'qd.gif')
        url = browser1.find_element_by_xpath('//img[@alt]').get_attribute('src')
        print '任务 {0} 完成!!!'.format(count)
        gif_url_list_q.put(url)
        browser1.close()
    except Exception:
        pass

def send_status(host,port,status):
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    while 1:
        try:
            s.connect((host,port))
            break
        except Exception:
            print '连接manager失败5秒后重试'
            sleep(5)
            continue
    print '连接manager成功'

    s.sendall('2')
    s.sendall(status)
    s.close()

def send_result(host,port,data):
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    while 1:
        try:
            s.connect((host,port))
            break
        except Exception:
            print '连接manager失败5秒后重试'
            sleep(5)
            continue
    print '连接manager成功'

    s.sendall('3')
    data_length = len(json.dumps(data))
    data_length = (5 - len(str(data_length))) * '0' + str(data_length)
    s.sendall(data_length)
    s.sendall(json.dumps(data))
    print 'result发送给了manager'
    s.close()

def get_gif_url_list(timeout):
    gif_url_list_q = Queue()
    for i in range(1,6):
        process_list = []
        for j in range(1 + (i - 1) * 10,1 + i * 10):
            process_list.append(Process(target=fetch_gif_url,args=(data,j,gif_url_list_q)))
        for j in range(1 + (i - 1) * 10,1 + i * 10):
            process_list[j - (i - 1) * 10 - 1].start()
            # print '任务 {0} 开始...'.format(j)

        time_sum = 0
        while 1:
            for process in process_list:
                if not process.is_alive():
                    process_list.remove(process)
            if len(process_list) == 0:
                break

            elif time_sum == timeout:
                for process in process_list:
                    process.terminate()
                    print '{0} 假死被杀掉了...'.format(process.name)
                    process_list.remove(process)
                break
            else:
                time_sum += 1
                sleep(1)
                print str(time_sum) + '秒'
                continue
    print (gif_url_list_q.qsize()),'个结果'
    gif_url_list = []
    for i in range(gif_url_list_q.qsize()):
        gif_url_list.append(gif_url_list_q.get())
    return gif_url_list

if __name__ == '__main__':
    manager_host = '192.168.100.240'
    manager_port = 6666
    timeout = 40
    while 1:
        data = fetch_task_from_manager(manager_host,manager_port)
        send_status(manager_host,manager_port,'start')
        gif_url_list = get_gif_url_list(timeout)
        print gif_url_list
        send_status(manager_host,manager_port,'finish')
        send_result(manager_host,manager_port,gif_url_list)
        os.system('taskkill /im phantomjs.exe -f')
        sleep(10)





