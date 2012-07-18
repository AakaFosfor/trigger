#!/usr/bin/python
# invoked at the start of RAMP when ACT option filling scheme is AUTO
# operation:
# filling/linux/fill2file
#   infoLogger error message
# lhc2ctp.py
#   - create $dbctp/fs_auto/fs_name.alice
#   - create $dbctp/VALID.BCMASKS
# set new coll. schedule -colschedule.bash (to be updated with new par: auto)
# error/info messages
import os,os.path,string,sys,shutil
import pylog

def main(action):
  rc=0
  #mylog= pylog.Pylog("",tty='yes')   # no info, only tty
  mylog= pylog.Pylog("getfsdip",info='yes')
  sys.path.append(os.path.join(os.environ['VMECFDIR'],"filling"))
  #print os.environ["PYTHONPATH"]
  os.chdir(os.path.join(os.environ["dbctp"], "fs_auto"))
  if action=="act":   # consult act (auto/bcmasks/notavailable)
    cmd= os.path.join(os.environ["VMECFDIR"], "ctp_proxy/linux/act.exe")
    cmd= cmd+" VALUE FillingScheme"
    line= string.split(pylog.iopipe(cmd, "VALUE "))
    #print "line:",line
    if len(line)==2:
      if line[1]=='bcmasks': action='bcmasks'
      elif line[1]=='auto': action='auto'
      else: action='test'
  if os.environ['VMESITE'] == 'ALICE':
    cmd= os.path.join(os.environ["VMECFDIR"], "filling/linux/fill2file")
    #mylog.infolog("reading filling scheme from DIP...")
    dipout= string.split(pylog.iopipe(cmd, "fs "))
  else:
    # 50ns_1374_1368_0_1262_144bpi12inj 1374/2748
    #dipout=string.split("fs 50ns_1374_1368_0_1262_144bpi12inj 1374 2748")
    dipout= string.split("fs fs_name")
  #print dipout
  if len(dipout) != 5:  # "fs fs_name FillNumber N_fromdip N_written
   mylog.infolog("DIP service not ready", level='w')
   rc=1 
  else:
    bcdip= int(dipout[3])
    bcwritten= int(dipout[4])
    mylog.infolog("DIP: %s %d/%d bunches"%(dipout[1], bcdip, bcwritten))
    if bcwritten<1:
       mylog.infolog("Trying to get filling scheme from DIP: no BCs published", level='i')
       rc=2
  if rc==0:
    schname= dipout[1]
    #cmd= os.path.join(os.environ["VMECFDIR"], "filling/lhc2ctp.py")
    import lhc2ctp
    reload(lhc2ctp)
    #schname="test"
    #mylog.infolog("preparing colission schedule and CTP masks (%d bcs)..."%bcwritten)
    lsf= open(schname+".dip"); ee=lsf.read(); lsf.close;
    alice= lhc2ctp.bu2bcstr(ee, schname, format="from dip")
    lsf= open(schname+".alice","w"); lsf.write(alice); lsf.close;
    mask= lhc2ctp.FilScheme("", alice); mask= mask.getMasks()
    lsf= open(schname+".mask","w"); lsf.write(mask); lsf.flush(); lsf.close;
    #os.fsync()
    #
    if action=="test":
      mylog.infolog("test: CTPRCFG/CS not updated. CS and masks left in fs_auto/")
      #shutil.copyfile(schname+".mask", "../VALID.BCMASKSauto")
      rc=10
    elif action=="bcmasks":
      mylog.infolog("CTPRCFG/CS not updated (not required in ACT). CS and masks left in fs_auto/")
    elif action=="auto":
      mylog.infolog("updating CTPRCFG/CS DIM service and BCMASK file...")
      #shutil.copyfile(schname+".mask", "../VALID.BCMASKS")
      cmd= "cp "+schname+".mask ../VALID.BCMASKS"
      mylog.infolog("cmd:"+cmd)
      os.system(cmd)
      rc= os.WEXITSTATUS(os.system("colschedule.bash update_auto >/dev/null"))
    else:
      rc=99
    mylog.infolog("colschedule.bash rc:%d"%rc)
  return rc

if __name__ == "__main__":
  if len(sys.argv) <2:
    print """

Usage:
getfsdip.py auto
            bcmasks
            act     consult act: bcmasks or auto
            test
rc:
 1: cannot get DIP data
10: test i.e. CS and masks not changed.
99: bad action, this message
"""
    rc= 99
  else:
    action= sys.argv[1]
    rc=main(action)
  sys.exit(rc)
