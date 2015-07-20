#!/bin/bash
#Usage:
# . vmebse.bash [swonly] [vdir]
# swonly: change only VMEBDIR,VMECFDIR,PYTHONPATH + ALIASES!
# vdir:
# 1. v                       relative (rdir= ult/vdir )
# 2. vnew                    relative (rdir= ult/vdir )
# 3. /usr/local/trigger/v    absolute (rdir= vdir )
# Usefull for trigger@altri1:   production (/mnt) -> development (/usr):
# . vmebse.bash swonly /usr/local/trigger/v 
function echoint() {
if [ -n "$PS1" ] ;then
  echo $1
fi
}
vdir=`pwd`/v     # before git: vdir='v'
hname=`hostname -s`
export HOSTNAME=$hname
if [ -n "$1" ] ;then
  if [ "$1" = 'swonly' ] ;then
    if [ -n "$2" ] ;then
      vdir=$2
    fi
  else
    vdir=$1
  fi
fi
#defaults:
export VMESITE=SERVER
export OS=Linux
export DIMDIR=/opt/dim
export SMIDIR=/opt/smi
export VMEGCC=g++ #export VMEGCC=gcc
# let's abandon ult -i.e. not used below! Use insted: 
# cd trgdist (where v is) ; . bin/vmebse.bash ; cd
if [ "$hname" = 'pcalicebhm10' ] ;then
  ult=/home/dl6/local/trigger
elif [ "$hname" = 'avmes' ] ;then
  ult=/home/dl6/local/trigger
elif [ "$hname" = 'alidcscom188' ] ;then
  ult=/data/dl/root/usr/local/trigger
elif [ "$hname" = 'alidcscom835' ] ;then
  ult=/home/dl6/local/trigger
else
  ult=/usr/local/trigger
fi

export VMEBDIR=$vdir/vmeb
export VMECFDIR=$vdir/vme
export VMEWORKDIR=~/v/vme
export dbctp=$VMECFDIR/CFG/ctp/DB
if [ -z "$DATE_DAQLOGBOOK_DIR" -a -d /opt/libDAQlogbook ] ;then
  export DATE_DAQLOGBOOK_DIR=/opt/libDAQlogbook
fi
if [[ $PATH != *$vdir/bin* ]] ;then
  export PATH="$vdir/bin:$PATH"
fi
export PYTHONPATH=$VMEBDIR
if [ -e /opt/infoLogger/infoLoggerStandalone.sh ] ;then
  . /opt/infoLogger/infoLoggerStandalone.sh
  export DATE_INFOLOGGER_DIR=/opt/infoLogger
  export DATE_INFOLOGGER_SYSTEM=TRG
fi
#
#first=`echo $vdir |cut -b 1`
if [ -e /dev/vme_rcc ] ;then           #------------------------ VME CPU
  export VMEDRIVER=VMERCC     # VMERCC, SIMVME
  if [[ -z $VMELIBS ]] ;then
    export VMELIBS=/lib/modules/daq
    export VMEINCS=/usr/local/include
  fi
  DIPLIB=/opt/dip/lib
  if [[ $LD_LIBRARY_PATH != *:$DIMDIR:* ]] ;then
    export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$VMELIBS:$DIMDIR/linux:$SMIDIR/linux:$DIPLIB
  fi
  ix=`expr match "$hname" 'alidcs'`
  if [ "$ix" = '6' ] ;then   #pit
    export VMESITE=ALICE
    export SMAQ_C=alidcscom707
    export DIM_DNS_NODE=aldaqecs
    #export DIM_DNS_NODE=alidcscom188
  elif [ "$hname" = "altri1" ] ;then   # development
    export SMAQ_C=avmes
    export VMESITE=SERVER
    #export DIM_DNS_NODE=pcald30
    unset DATE_INFOLOGGER_DIR
    export DIM_DNS_NODE=avmes
  elif [ "$hname" = "altri2" -o "$hname" = "altrip2" ] ;then   # stable (daqecs)
    export SMAQ_C=pcalicebhm10
    export VMESITE=SERVER2
    #export DIM_DNS_NODE=pcald30
    export DIM_DNS_NODE=pcalicebhm10
  else
    export VMESITE=PRIVATE
    export DIM_DNS_NODE=pcald30
  fi
else               #------------------------------ server
  export VMEDRIVER=SIMVME
  DIPLIB=/opt/dip/lib64
  if [[ $LD_LIBRARY_PATH != *:$DIMDIR:* ]] ;then
    export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$DIMDIR/linux:$SMIDIR/linux:$DIPLIB
  fi
  if [ "$hname" = "avmes" ] ;then   # development ? 13.7. : as in p2
    export SMAQ_C=avmes
    export VMESITE=SERVER
    export DIM_DNS_NODE=avmes
    unset DATE_INFOLOGGER_DIR
    if [ -d /opt/act ] ;then
      export ACT_DB=daq:daq@pcald30/ACT
    fi
  elif [ "$hname" = 'alidcscom188' ] ;then
    export VMESITE=ALICE
    export SMAQ_C=alidcscom707
    export DIM_DNS_NODE=aldaqecs
  elif [ "$hname" = 'alidcscom835' ] ;then
    export VMESITE=ALICE
    export SMAQ_C=alidcscom707
    export DIM_DNS_NODE=aldaqecs
    if [ -d /opt/act ] ;then   # needed only on server
      export ACT_DB=acttrg:dppDFFIO@aldaqdb/ACT   # was CBNRR@be in run1
    fi
  elif [ "$hname" = "pcalicebhm10" ] ;then   # 13.7. development
    export SMAQ_C=avmes
    export VMESITE=SERVER2
    export DIM_DNS_NODE=pcalicebhm10
    if [ -d /opt/act ] ;then
      export ACT_DB=daq:daq@pcald30/ACT
    fi
    unset DATE_DAQLOGBOOK_DIR
    unset ACT_DB
  else
    export VMESITE=PRIVATE
  fi
fi
#if [ "$VMESITE" != ALICE ] ;then
#  unset DATE_INFOLOGGER_DIR
#fi
#
#aliases:
alias ssh="ssh -2"
alias vmecomp=$VMEBDIR/comp.py
alias vmecrate=$VMEBDIR/crate.py
alias vmedirs='echo   VMEDRIVER:$VMEDRIVER   VMESITE:$VMESITE   VMEGCC:$VMEGCC   SMAQ_C:$SMAQ_C; echo   VMEBDIR:$VMEBDIR;echo   VMECFDIR:$VMECFDIR; echo VMEWORKDIR:$VMEWORKDIR; echo DATE_INFOLOGGER_DIR:$DATE_INFOLOGGER_DIR   DATE_DAQLOGBOOK_DIR:$DATE_DAQLOGBOOK_DIR; echo ACT_DB:$ACT_DB; echo DIM_DNS_NODE:$DIM_DNS_NODE'
if [ "$hname" = 'alidcscom835' -o "$hname" = 'avmes' ] ;then
  echoint "Server cpu: $hname, alias defs in bin/setenv"
elif [ "$hname" = 'altri1' -o "$hname" = 'alidcsvme001' ] ;then
  #ctp vme cpu:
  alias "ctp=vmecrate nbi ctp"
  alias ctpdims=$vdir/bin/ctpdims.sh
else
  # ltu vme cpu
  #alias ltuserver=/usr/local/trigger/bin/ltuserver.bash
  alias ltuproxy=$VMECFDIR/../bin/ltuproxy.sh
 fi
shopt -s expand_aliases
#
#alias slmshow=$VMECFDIR/ltu/slmcomp.py
#alias slmedit='cd $VMECFDIR/CFG/ltu/SLM;$VMECFDIR/ltu/ltu6'
#alias initttc='$VMEBDIR/../scripts/ttcvi'
#alias vmeshow='/local/trigger/ECS/vmeshow'
#echoint "LD_LIBRARY_PATH:$LD_LIBRARY_PATH"
#echoint 'useful aliases: vmedirs, vmecomp, vmecrate, slmshow, slmedit'
#vmedirs
