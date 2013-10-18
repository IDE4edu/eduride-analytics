'''
Created on Sep 1, 2013
@author: nate

requires local mysql with
  dbname->eduride
  tablename->log_ccsf_sp2013

'''
import base64
import os
import mysql.connector
import difflib

dbuser = "eduride"
dbpass = "eduride"
dbname = "eduride"
# table-> "log_ccsf_sp2013"
#  colums->id, subject, verb, object, time



if __name__ == '__main__':
    pass

####
def getNameFromNav(msg):
    "get the name out of stupid log message"
    msg=msg[5:]
    msg=msg[:msg.find(" (")]
    msg=msg.replace("(",'').replace(")",'')   # I hate regular expressions, so see what happens...
    msg=msg.replace(" ",'-')
    return msg


def getNameFromSC(msg):
    "get the name out of a diff stupid log message"
    msg=msg[6:msg.find(" (")]
    msg=msg.replace("(",'').replace(")",'')   # I hate regular expressions, so see what happens...
    msg=msg.replace(" ",'-')
    return msg



def openFileAndGotoEnd(name):
    fp = open(name, 'w')
    fp.seek(0,2)
    return fp

#         if (curdifffile is not None):
#             curdifffile.close()
#         curdifffile = open(curbasedir + "/" + "diff.log", 'w')
#         curdifffile.seek(0,2)    #goto end



cnx = mysql.connector.connect(user=dbuser, password=dbpass, host='127.0.0.1', database=dbname)
cur = cnx.cursor()

# # get students
# cur.execute('SELECT DISTINCT subject as student FROM log_ccsf_sp2013 ORDER BY student;')
# for (wsid) in cur:
#     print("wsid is {}".format(wsid))



# get all files
cur.execute('''
SELECT subject as student, verb, object as obj, id as sid, time
FROM eduride.log_ccsf_sp2013
WHERE verb = 'File' OR verb='stepChanged' OR verb='navInvokeTest' OR verb='openISA'
ORDER BY student, id
''')
curstudent = ""
curbasedir = ""
studentbasedir = ""
curISA = "xxxISA-"
curjavafilename  =  ""
curlogfp = None
lastfile = ""
cleaned_lastfile  =  ""
leave_test = "xxx"

for(student, verb, obj, sid, time) in cur:
    if (student != curstudent):
        # starting a new student
        curstudent = student
        curbasedir = "ccsf_sp13/" + student
        studentbasedir = curbasedir
        os.makedirs(curbasedir)

    if (verb == 'openISA'):
        curISA=obj.split(')')[0].split('(')[1]
        curbasedir = studentbasedir + "/" + curISA[10:]
        # make if doesn't exist
        try:
            os.makedirs(curbasedir)
        except Exception as e:
            print e
    elif (verb == 'navInvokeTest'):
        leave_test = 'test'
        curjavafilename = getNameFromNav(obj)
    elif (verb == 'stepChanged'):
        leave_test = 'leave'
        curjavafilename = getNameFromSC(obj)
    elif (verb == 'File'):
        curlogfp = open(curbasedir + '/' + curjavafilename + '--DIFF.log', 'a')
        curlogfp.write('\n---\n')

        curfile = base64.b64decode(obj)

        if (curfile != lastfile):

            # do some cleaning up, inserting \n in places for instance.
            cleaned_curfile = curfile.replace('//', '\n//')
            cleaned_curfile = cleaned_curfile.replace('{', '{\n')
            cleaned_curfile = cleaned_curfile.replace('}', '\n}\n')
            cleaned_curfile = cleaned_curfile.replace(';', ';\n')

            # construct the file name
            curfilename = curjavafilename + '--'+ time.strftime('%H.%M.%S') + '--' + leave_test + '.java'

            # write out the dirty version and clean version
            fp = open(curbasedir + '/' + curfilename + '--ORIG', 'w')
            fp.write(curfile)
            fp.close()
            fp = open(curbasedir + '/' + curfilename, 'w')
            fp.write(curfile)
            fp.close()

            # write out the diff compared to the last file
            diff = difflib.ndiff(b=cleaned_curfile.splitlines(), a=cleaned_lastfile.splitlines())
            # open the log file for the current java file for appending the new diff
            curlogfp.write('Logging file: ' + curfilename + '\n')
            for change in diff:
                curlogfp.write('\t\t\t\t\t')
                curlogfp.write(change)
                curlogfp.write('\n')

            # update the lastfile and cleaned_lastfile to prepare for the next iteration
            lastfile = curfile
            cleaned_lastfile = cleaned_curfile

        else:
            curlogfp.write(leave_test + ' but file unchanged (row id ' + str(sid) + '\n')
            #if (leave_test == 'test'):
                # maybe we should write test results in log file?  Yeah, but they are inconsistent doh
            print('row id ' + str(sid) + ' same file as before (isa = '+ curISA +', leave/test = ' + leave_test + ').')
        curlogfp.close()
    else:
        print 'ERROR - dropped out of if on verb=' + verb


cur.close();
cnx.close();





