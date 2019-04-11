from subprocess import call
from os import system

def _substitue(filename, expr, val):
    regex = '"s#{old}#{new}#g"'.format(old=expr, new=val)
    system('sed -i \'\' %s %s' % (regex, filename))

def run_file(filename, subs):
    #run sql file and substitute <EXR> with VAL
    #assume filename end in sql
    filename_tmp = '_tmp.'.join(filename.split('.'))
    call(['cp', filename, filename_tmp])

    for i in subs:
        expr = i[0]
        val = i[1]
        _substitue(filename_tmp, expr, val)

    system('psql -d postgis_test -f %s' % (filename_tmp))


