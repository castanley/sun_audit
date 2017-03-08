#!/usr/local/bin/python2.7
import sys, os, string, threading
import paramiko
import psycopg2
import time
import logging

#getCPU = "/usr/sbin/psrinfo -p"
getCPU = "/usr/sbin/psrinfo | wc | awk '{print $1/8}'"
getMEM = "/usr/sbin/prtconf | grep \"Memory\" | awk '{ print $3 }'"
getHOST = "hostname"

class bcolors:
    MAGENTA = '\033[95m'
    YELLOW = '\033[93m'
    ENDC = '\033[0m'

def workon(host,conn,date):

    paramiko.util.log_to_file('paramiko.log')

    #Connect to each host
    ssh = paramiko.SSHClient()
    key = paramiko.RSAKey.from_private_key_file("/PATH/TO/KEY")
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username='cstanley', pkey=key)

    #Run Commands
    stdinHOST, stdoutHOST, stderrHOST = ssh.exec_command(getHOST)
    stdinCPU, stdoutCPU, stderrCPU = ssh.exec_command(getCPU)
    stdinMEM, stdoutMEM, stderrMEM = ssh.exec_command(getMEM)

    #with threadLock:
    sql = conn.cursor()
    resultHOST = stdoutHOST.readlines()
    resultHOST[0] = resultHOST[0].rstrip()

    #print "{0} {0} UX10 1".format(resultHOST[0].rstrip())
    cmd = "INSERT INTO obj_temp (rec_date, device, name, units, function_code) VALUES (%s, %s, %s, %s, %s);"
    data = (date, 'solaris-cdc', resultHOST[0], 1, 'UX10',)
    sql.execute(cmd, data)
    print "%s solaris-cdc %s 1 UX10" % (date, resultHOST[0])

    resultCPU = stdoutCPU.readlines()
    units = (int(resultCPU[0].rstrip()) - 1)
    if units != 0:
        #print "{0} {0} UX40 {1}".format(resultHOST[0].rstrip(),ux40)
        cmd = "INSERT INTO obj_temp (rec_date, device, name, units, function_code) VALUES (%s, %s, %s, %s, %s);"
        data = (date, 'solaris-cdc', resultHOST[0], units, "UX40",)
        sql.execute(cmd, data)
        print "%s solaris-cdc %s %s UX40" % (date, resultHOST[0], units)

    resultMEM = stdoutMEM.readlines()
    units = ((int(resultMEM[0].rstrip()) / 1024 - 2) / 2)
    #print "{0} {0} UX30 {1}".format(resultHOST[0].rstrip(),ux30)
    cmd = "INSERT INTO obj_temp (rec_date, device, name, units, function_code) VALUES (%s, %s, %s, %s, %s);"
    data = (date, "solaris-cdc", resultHOST[0], units, "UX30",)
    sql.execute(cmd, data)
    print "%s solaris-cdc %s %s UX30" % (date, resultHOST[0], units)

    sql.close()
    ssh.close()

def main():

    #Paramiko Logging
    logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename='paramiko.log',
                    filemode='w')

    date = (time.strftime("%m/%d/%Y"))

    #Define our connection string
    conn_string = "host='SQLSERVER' dbname='billing' user='REMOVED' password='REMOVED' connect_timeout=3"

    # print the connection string we will use to connect
    #print bcolors.MAGENTA + 'Connecting to database\n    ->%s' % (conn_string) + bcolors.ENDC + "\n"

    # get a connection, if a connect cannot be made an exception will be raised here
    conn = psycopg2.connect(conn_string)

    # conn.cursor will return a cursor object, you can use this cursor to perform queries
    #sql = conn.cursor()
    print bcolors.YELLOW + "Inserting Solaris information into table.\n" + bcolors.ENDC

    print " _________________________________________________ "
    print "|  DATE  |   DEVICE  |  NAME  | UNITS | FUNC_CODE |"
    print " _________________________________________________ "

    with open('/home/cstanley/scripts/vip/sun_ip') as ip:
        hosts = ip.read().splitlines()

    threads = []
    for h in hosts:
        t = threading.Thread(target=workon, args=(h,conn,date))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

    conn.commit()
    conn.close()

if __name__ == "__main__":
    main()
