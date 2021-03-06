#!/usr/bin/python
'''
29.12.2002 -tear off menus now working (class FunStart)
           -funcs without pars are started directly 
 3.12.2003
- bubble help added for single function buttons
17.12.
vmeread modified (now a[-3])
9.1. started: new MywEntry (old is saved in myw.py.old)
13.1. Stdfuncs corrected (now correct width according to defaults)
 5.3. class MywBits 
 8.3. os.path.join used for paths creation (platform independent)
17.3. MywxMenu -if choosen option is the same as before, action
      is not invoked (nothing changed)
23.6. MywVMEEntry added
 3.10. "vmecrate nbi ..." -> don't initialise boards
27.1.2005 getCrate -adjusted so myw.py can be to be used with 'non vmecrate'
      modules
24.4. MywxMenu slightly modified (cmd added, bug 'only string not
      possible in items' fixed
17.5. NPARDESCTYPE/ID/NAME added, default for char * parameter is " "
11.9. MywEntry.getEntryBin() added
      MywBits -now possibility not to show some bits
21.9. MywHelp modified (now can be used as non inherite class)
11.11. NewToplevel() added
14.11. MywxMenu modified: now if cmd callback defined, it gets
       ix as integer (not string as before)
'''
import sys, os, os.path, string, types, time
from Tkinter import *

COLOR_RUNNING="#ff6666"
COLOR_VALCHANGED="#ff00ff"
COLOR_VALNORMAL="#99cc99"
COLOR_WARNING="#ff99cc"
COLOR_BGDEFAULT="#d9d9d9"
COLOR_DECIMAL="#d9d9ff"

def RiseToplevel(tlw):
    tlw.lift(); tlw.bell()
def NewToplevel(title='???', whenDestroyed=None):
    tlw=Toplevel(); 
    tlw.title(title)
    tlm= getCrate()
    if tlm!=None:
      tlw.transient(tlm.master)
    #tlw.transient(vbexec.vbinst.master)
    tlw.bind("<Destroy>", whenDestroyed)
    return tlw

def dbgprint(o, *pars):
  #dbgclss={"MultRegs":1,"VmeBoard":1}
  #dbgclss={"MultRegs":1}
  dbgclss={}
  cnam=o.__class__.__name__
  if dbgclss.has_key(cnam):
    print o.__class__.__name__,":",pars
def errorprint(o, *pars):
  print "ERROR in ", o.__class__.__name__,":",pars
  #print "sys:",sys._getframe(1).f_code.co_name    see inspect
def gt(x,y):
  if(x>y):
    return(x)
  else:
    return(y)

class curry:
  '''
  def __init__(self, fun, *args, **kwargs):
    self.fun = fun
    self.pending = args[:]
    self.kwargs = kwargs.copy()
  def __call__(self, *args, **kwargs):
    if kwargs and self.kwargs:
      kw = self.kwargs.copy()
      kw.update(kwargs)
    else:
      kw = kwargs or self.kwargs
    return self.fun(*(self.pending + args), **kw)
  '''
  def __init__(self, callback, *args, **kwargs):
    self.callback = callback
    self.args = args
    self.kwargs = kwargs
  def __call__(self):
    return apply(self.callback, self.args, self.kwargs)

class MywError:
 """Usage:
 myw.MywError("error message")
 """
 def __init__(self,errmsg="Unknown error",iow=None, fw=None):
   self.fw=fw
   self.tlm=Toplevel(bg="blue")
   cr= getCrate()
   if cr: self.tlm.transient(cr.master)
   #print ":",iow,":"
   self.tlm.title("Error message")
   #self.tlm.lift()   # not very useful (the same with and without)
   if iow==None: # let error message overlap the 'crate' widget
     if cr:
       iow=cr.crframe.winfo_rootx(),cr.crframe.winfo_rooty()
     else: iow=(1,1)
   xystr= "+"+str(iow[0])+"+"+str(iow[1])
   self.tlm.geometry(xystr)
   self.tlm.bind("<Destroy>", self.cancel)
   l=MywLabel(self.tlm,errmsg)
   l.configure(background="red")
   MywButton(self.tlm, 'Cancel', bg="red",cmd=self.cancel)
   #self.tlm.focus_set()   #seems not to have sense with grab_set
   #self.tlm.grab_set()
   self.reps=0
   self.repeatErrorfocus()
 def repeatErrorfocus(self,cancel=None):
    if self.reps >= 100 or cancel:
      self.tlm.after_cancel(self.afterid)
      self.reps=0
    else:
      if self.fw:
        #von self.fw.lift(); 
        self.fw.event_generate("<Button-1>"); 
        self.fw.focus_set(); 
      else:
        self.tlm.focus_set(); 
      self.tlm.lift(); #self.tlm.bell()
      self.afterid=self.tlm.after(100, self.repeatErrorfocus)
      self.reps= self.reps+1
 def cancel(self, ev=None):
   self.repeatErrorfocus(cancel='yes')
   self.tlm.destroy()

class MultRegs:
  def __init__(self, board):
    self.mrmaster=Toplevel()
    cr= getCrate()
    if cr: self.mrmaster.transient(cr.master)
    self.mrmaster.title("multireg "+ board.boardName)
    self.regsframe= MywFrame(self.mrmaster)
    self.board=board; self.perrep=0
    self.regs=[]
    self.rgitems=[]
    self.addrgitems=[]
    for rg in self.board.vmeregs:
      #print 'MultRegs:',rg
      #htext=htext+ rg[0] + " = " + rg[1] + "\n"
      if rg[2]=='':   # take only 32 bit registers
        self.rgitems.append((rg[0],rg[1]))
        self.addrgitems.append((rg[0],rg[1],self.addReg))
    self.rgitems.append(("remove me","removevalue"))
    #self.cr= MywxMenu(self.mrmaster, items=self.rgitems)
    #readbut= MywButton(self.mrmaster, label='read', 
    #  cmd=self.allread, side='left')
    #writebut= MywButton(self.mrmaster, label='write', cmd=self.vmewrite, side='left')
    #okbut= MywButton(self.mrmaster, label='quit', 
    #  cmd=self.mrmaster.destroy, side='bottom')
    self.butsframe= MywFrame(self.mrmaster)
    self.addqframe= MywFrame(self.mrmaster)
    self.butts=MywHButtons(self.butsframe, 
      [("read", self.allread),
       ("periodic read", self.perRead),
       ("quit", self.mrmaster.destroy)])
    self.addr= MywxMenu(self.addqframe, items=self.addrgitems, 
      helptext="Choose reisters to be read",
      label='Addreg:',side=LEFT)   #, cmdlabel=self.chooseReg)
  def addReg(self, inx=None):
    #print "addReg:", self.rgitems
    #self.addr.printEntry('MultRegaddReg:')
    if inx==None: inx= self.addr.getIndex()
    r= MywEntry(self.regsframe, label=self.rgitems, 
      delaction=self.destroyReg, defaultinx=inx,
      side=TOP)   #, cmdlabel=self.chooseReg)
    dbgprint(self, "MultRegs.addReg:",r)
    #r.label.bind("<Enter>", self.cr.popup)
    #blika self.mrmaster.bind("<Leave>", self.cr.unpopup)
    self.regs.append(r)
  def destroyReg(self, entrywidget):
    dbgprint(self, "destroyReg:",self.regs,entrywidget)
    #delete the item from self.regs
    toremove=-1
    for i in range(len(self.regs)):
      if self.regs[i] is entrywidget:
        #print "destroyReg2:", self.regs[i]
        #print "          =:", entrywidget
        toremove=i
    if toremove!= -1:
      del self.regs[toremove]
    else:
      errorprint(self,"bad remove",self.regs)
    entrywidget.destroy()
  def doout(self,allvals):
    #print "allread3:",allvals,':'
    vlist=string.split(allvals); vll= len(vlist)
    if vll != len(self.regs):
      errorprint(self, "%d != %d"%(vll,len(self.regs)))
    #dbgprint(self,"allread2:",vlist)
    for i in range(vll):
      prevval= self.regs[i].getEntryHex()
      #print "allread:",prevval,vlist[i]
      if prevval != vlist[i]:
        self.regs[i].entry.configure(bg=COLOR_VALCHANGED)
      else:
        #self.regs[i].entry.configure(bg=COLOR_VALNORMAL)
        self.regs[i].setColor()
      self.regs[i].setEntry(vlist[i])
  def allread(self):
    addrs=[]
    cmd2=""
    for i in range(len(self.regs)):
      addrs.append(self.regs[i].label.posval.get())
      #self.regs[i].setEntry(addrs[i])
      cmd2=cmd2+','+str(addrs[i])
    #print 'allread  :', addrs
    if self.board.io==None: self.board.openCmd()
    #cmd="vmeopmr32("+ str(len(self.regs))+cmd2+')'
    cmd="vmeopmr32("+ str(len(self.regs))+')'
    # 1 line: 0x12 0xabcd ... expected
    #allvals=string.split(self.board.io.execute(cmd),'\n')[-2]
    thdrn=self.board.io.execute(cmd,ff=self.doout)
    #print 'thrdn:',thdrn
    self.board.io.thds[thdrn].waitcmdw()
    for i in range(len(self.regs)):
      addrs.append(self.regs[i].label.posval.get())
      #self.regs[i].setEntry(addrs[i])
      self.board.io.thds[thdrn].pwrite(str(addrs[i])+"\n")
    #
  def repeatRead(self, cancel=None):
    if self.perrep >= 100 or cancel:
      self.mrmaster.after_cancel(self.afterid)
      self.butts.buttons[1].configure(bg=self.normalcolor[0],
        activebackground=self.normalcolor[1])
      self.perrep=0
    else:
      self.allread()
      self.afterid=self.mrmaster.after(1500, self.repeatRead)
      self.perrep= self.perrep+1
  def perRead(self):
    #print 'perRead.perrep:',self.perrep
    #self.allread()
    if self.perrep == 0:   #just starting
      self.normalcolor=self.butts.buttons[1].cget('bg'),\
        self.butts.buttons[1].cget('activebackground')
      #print 'perRead.normalcolor:',self.normalcolor
      self.butts.buttons[1].configure(bg=COLOR_RUNNING,
        activebackground=COLOR_RUNNING)
      self.repeatRead()
    else:                  # request to stop periodic read
      self.repeatRead(cancel='yes')

class VmeRW:
  def __init__(self,vboard):
    #print "here VmeRW"
    self.vboard=vboard
    rwf=Toplevel(vboard.vmebf)
    cr= getCrate()
    if cr: rwf.transient(cr.master)
    rwf.title("r/w "+ vboard.boardName+' '+vboard.baseAddr)
    #
    adrframe=MywFrame(rwf)
    valframe=MywFrame(rwf)
    htext='base:%s\nVME regs:\n'%vboard.baseAddr
    items=[]
    for rg in vboard.vmeregs:
      #print 'VmeRW:',rg
      htext=htext+ rg[0] + " = " + rg[1] + "\n"
      items.append( (rg[0],rg[1]) )
    if len(items)>0:
      rt= vboard.findvmeregtyp(items[0][0])
      defx={"w8":0, "w16":1,"w32":2}[rt]
      self.adrmenu=MywMenu81632(adrframe, items=items,side='right')
      self.adrmenu.boardmod=self
      self.addrent= MywEntry(master=adrframe,label='addr:', side='left',\
        helptext=htext, textvariable=self.adrmenu.posval,width=8)
    else:
      # no registers defined:
      #print 'VmeRW:',items[0],self.findvmeregtyp(items[0][0])
      defx={"w8":0, "w16":1,"w32":2}['w32']
      self.addrent= MywEntry(master=adrframe,label='addr:', side='left',\
        helptext=htext, width=8)
    #
    self.v81632menu=MywxMenu(valframe,defaultinx=defx, 
      items=(("8b","8"),("16b","16"),("32b","32")),side='right')
    self.valent= MywEntry(master=valframe,label='value:', side='left',
      width=10)
    #
    readbut= MywButton(rwf, label='read', cmd=self.vmeread, side='left')
    writebut= MywButton(rwf, label='write', cmd=self.vmewrite, side='left')
    okbut= MywButton(rwf, label='quit', cmd=rwf.destroy, side='left')
  def vmeread(self):
    #print "wmeread from:",self.vboard.addrent.getEntry()
    #if self.vboard.adrmenu.posval.get()==self.addrent.getEntry():
    bits= self.v81632menu.posval.get()
    cmd= "vmeopr"+bits+"("+self.addrent.getEntry()+")" 
    if self.vboard.io==None: self.vboard.openCmd()
    alllines=string.split(self.vboard.io.execute(cmd),'\n')
    #print 'alllines:',alllines,'---'
    if len(alllines)>=2:
      a=alllines[-2]
      self.valent.setEntry(a)
    #print "vmeread:",a,"aa vmeread: ['0xf96f', ':', ''] aa"
  def vmewrite(self):
    bits= self.v81632menu.posval.get()
    cmd= "vmeopw"+bits+"("+self.addrent.getEntry()+", "+\
      self.valent.getEntry()+")" 
    if self.vboard.io==None: self.vboard.openCmd()
    self.vboard.io.execute(cmd)
  def modexit(self):
    #print "here modexit"
    if self.adrmenu.posval.get()==self.addrent.getEntry():
      #print "modexit:",self.adrmenu.radiobut['text']
      tx= self.vboard.findvmeregtyp(self.adrmenu.radiobut['text'])
      self.v81632menu.posval.set(tx[1:])
      self.v81632menu.radiobut['text']= tx

class MywHelp:
  """Usage:
  For classes inheriting MywHelp (see MywButton for example):
  myw.MywHelp(self.topfr,"help text")
  For classes not inheriting MywHelp:
  myw.MywHelp(self.topfr,"help text", canvas)
  canvas -widget to which Button-3 is bound
  """
  maxheight=80
  def __init__(self,master,helptext,hlpwidget=None):
    self.fmaster=master
    self.newhelp(helptext)
    self.hw=None
    if hlpwidget!=None:
      sbnd= hlpwidget
    else:
      sbnd= self
    c= getCrate()
    if c and c.autohelps:
      sbnd.bind("<Enter>", self.entercb)
      sbnd.bind("<Leave>", self.leavecb)
    else:
      sbnd.bind("<Button-3>",self.help)
  def help(self, event=None):
    if self.hw: return
    self.hw=Toplevel(self.fmaster, width=0, height=0)
    cr= getCrate()
    if cr: 
      self.hw.transient(cr.master)
      #print 'lower' -nohelp
      #self.hw.lower(cr.master)
    self.hw.config(bg="green")
    #main widget (crate) left top corner in pixels:
    cratex=self.fmaster.winfo_rootx(); cratey=self.fmaster.winfo_rooty()
    cratew=self.fmaster.winfo_width()
    self.hw.bind("<Destroy>",self.dest)
    scrollbar = Scrollbar(self.hw)
    wi,self.he= self.finwh(self.helptext)
    if self.he>self.maxheight:
      text=Text(self.hw, bg=self.hw.cget('bg'),width=wi, height=self.maxheight,
         yscrollcommand=scrollbar.set ); 
    else:
      text=Text(self.hw, bg=self.hw.cget('bg'),width=wi, height=self.he)
    #print self.hw.config()
    text.insert(END, self.helptext);
    text.config(state=DISABLED);
    text.pack(side=LEFT,expand='yes', fill='x');
    self.hw.update_idletasks()
    helpheight= self.hw.winfo_height() + 40
    helpwidth= self.hw.winfo_width()
    #print "cratex,y:",type(cratex),cratex,cratey
    #print "helpheight,Width:", helpheight, helpwidth,type(helpwidth)
    screenheight= self.hw.winfo_screenheight()
    screenwidth= self.hw.winfo_screenwidth()
    #print "screen height,width:",screenheight,screenwidth
    #x
    if cratex<screenwidth/2: x= cratex+cratew
    else: x= cratex-helpwidth
    if x<0 or x>screenwidth: x=0
    #y
    if (cratey+helpheight)<screenheight: y= cratey
    else: y= screenheight-helpheight
    if y<0: y= 0
    xy= '+%d+%d'%(x,y)
    #print "xy:",x,y
    self.hw.geometry(xy)
    if self.he>self.maxheight:
      scrollbar.config(command=text.yview)
      scrollbar.pack(side=RIGHT, fill='y')
    #okbut.pack(side=BOTTOM,expand='yes', fill='x') 
  def newhelp(self,helptext):
    self.helptext=helptext
  def finwh(self,s):
    #print "finwh:",s
    ss=string.split(s,'\n')
    h=len(ss)
    return(reduce(gt,map(len, ss)),h)
  def entercb(self,event):
    #print "entercb", event.x, event.y 
    self.afterid=self.after(2000, self.help)
  def leavecb(self,event):
    #print "leave", event.x, event.y 
    if self.hw:
      #self.MywHelp.hw.destroy() -nedobre
      if self.he<=self.maxheight:
        self.hw.destroy()
        self.hw=None
    else:
      self.after_cancel( self.afterid)
  def dest(self,event):
    #print "dest here"
    self.hw=None

class MywRadio:
  """
  Creates more Radiobuttons in 1 frame, together with a common Label
  button describing their purpose.
  cmdlabel: action started when Label button is pressed
  """
  def __init__(self, master=None,label="radio button",
    helptext=None, cmdlabel=None,
    items=(("text1","1"),("text2","2"))):
    self.posval= StringVar(); self.posval.set(items[0][1])
    self.radf=Frame(master, borderwidth=1,relief=RAISED)
    self.radf.pack(expand=YES,fill='x')
    self.label=MywEntry(self.radf,label=label, defvalue='',
      helptext=helptext,cmdlabel=cmdlabel)
    self.choices=[]
    for ch in items:
      self.choices.append( Radiobutton(self.radf,
        text=ch[0], variable=self.posval, value=ch[1]))
      self.choices[-1].pack()
  def getEntry(self):
    #print "radio:", self.posval.get()
    return(self.posval.get()) 
#  def config(self, state=NORMAL):
  def printEntry(self, text='printEntry:'):
    print text,self.getEntry()
#
"""
class MywEntry(Frame, MywHelp):
  def __init__(self, master=None, text='butlabel', cmd=None, 
    bg=None,side=None,anchor=None,funchelp=None,relief=RAISED):
    # zda sa ze nemusi byt self.but:
    #but= Button(master, text=text, command=cmd, bg=bg, activebackground=bg)
    #but.pack(side=side, expand='yes', fill='x')
    Button.__init__(self,master, text=text, command=cmd, bg=bg, activebackground=bg, relief=relief)
    Button.pack(self,side=side, expand='yes', fill='x', anchor=anchor)
    #if funcdescr and funcdescr[VmeBoard.NFUSAGE]:
    #  MywHelp.__init__(self,master,funcdescr[VmeBoard.NFUSAGE])
    if funchelp: MywHelp.__init__(self,master,funchelp)
"""
class MywEntry(Frame):
  """
  label: string -presented together with the Entry (on the left side)
         list   -see MywxMenu. In this case, delaction can be supplied
                 too, and defaultinx parameter for 'initial' item
  bind:  lr or r -cmdlabel is activated when cursor leaves entry (l)
                  or 'return' is pressed (r)
  cmdlabel: command to be executed when label pressed
            or (Enter key pressed when entry field is active -to be done)
  defvalue: if '', Entry part is not shown
  vme32: string representing VME32 address (symbolic name or
         constant)
  external methods:
  setEntry()
  getEntry(), getEntryBin(), getEntryHex()
  """
  def __init__(self, master, label='label', defvalue=' ',bind=None,
    side='left', helptext="", cmdlabel=None, width=None, bg=None,
    textvariable=None, delaction=None,defaultinx=0,name=None,
    relief=SUNKEN, expandentry='yes'):
    self.cmdlabel=cmdlabel
    self.nointcheck= 1   # to do: as parameter + updateentry + self.value 
    Frame.__init__(self,master, bg=bg)
    #if bind=='lr': 
    #  Frame.bind(self,"<Leave>", cmdlabel)
    #  Frame.bind(self,"<Key-Return>", cmdlabel)
    #if bind=='r': 
    #  Frame.bind(self,"<Key-Return>", cmdlabel)
    #self.master=master         # for MywxMenu -destroyReg()
    Frame.pack(self,side=side, expand='yes', fill='x')
    self.helptext=helptext
    if label!='':
      if type(label) is types.ListType:
        self.label= MywxMenu(self, items=label,side=LEFT,
        helptext=helptext, delaction=delaction,defaultinx=defaultinx)
      if type(label) is types.StringType:
        if self.cmdlabel and bind==None:
          self.label=MywButton(self,label=label,helptext=helptext, 
            side='left', relief=FLAT, cmd=self.updateentry, bg=bg)
        else:
          self.label=MywLabel(self,label=label,helptext=helptext, 
            side='left', relief=FLAT, bg=bg)
    #else:
    self.normalcolor= COLOR_BGDEFAULT
    if defvalue:
      self.conv2dec=2   #0: dec2hex  1: hex2dec   2: no conversion
      self.entry=Entry(self, width=width,textvariable=textvariable,
        name=name, relief=relief,bg=bg)
      self.entry.insert('end',defvalue)
      self.entry.pack(side='left', expand=expandentry, fill='x')
      self.entry.bind("<Button-3>",self.convertStart)
      if bind=='lr': 
        self.entry.bind("<Leave>", self.updateentry)
        self.entry.bind("<Key-Return>", self.updateentry)
      if bind=='r': 
        self.entry.bind("<Key-Return>", self.updateentry)
    else:
      self.entry=None
    #print "MywEntry: label, defavalue:",label, defvalue
  def updateentry(self, event=None):
    """event is None in case of activation by button..."""
    ne= self.entry.get()
    if self.nointcheck:
      self.cmdlabel(ne)
      return
    try:
      ne_b= eval(ne)
    except:
      MywError("bad value (int or hex expected):"+ne, fw=self.entry)
    else:
      self.cmdlabel(ne)
  def setEntry(self, text):
    self.entry.delete(0, 'end')
    if self.conv2dec==1:
      text= self.hex2dec(text)
    else:
      if self.conv2dec==0:
        text= self.dec2hex(text)
    self.entry.insert(0, text)
    #print 'Here setEntry:',text
  def getEntry(self):
    tx= self.entry.get()
    return(tx)
  def getEntryBin(self):
    tx= eval(self.entry.get())
    return(tx)
  def getEntryHex(self):
    tx= self.entry.get()
    if tx[0:2]!='0x':
      try:
        tx= int(tx)
        tx= "0x%x"%(tx)
      except:
        pass
    return(tx)
  def setColor(self, color=None):
    if color==None:
      color= self.normalcolor
    self.entry.configure(bg=color)
    #self.label.configure(bg=color)
  def convertStart(self,event=None):
    # make this entry visible as decimal number:
    #print "convertStart:",
    if self.conv2dec==0 or self.conv2dec==2:
      self.conv2dec=1
      self.setColor(COLOR_DECIMAL)
      t=self.getEntry(); self.setEntry(self.hex2dec(t))
    else:
      self.conv2dec=0
      self.setColor(COLOR_BGDEFAULT)
      t=self.getEntry(); self.setEntry(t)
  def hex2dec(self,text):
    #print "hex2dec:",text, range(len(text)-1,1,-1)
    #text=int(text,16)    -in python 2.2.2
    """
    hexdig={'0':0,'1':1,'2':2,'3':3,'4':4,'5':5,'6':6,'7':7,
            '8':8,'9':9,'a':10,'b':11,'c':12,'d':13,'e':14,'f':15,
            'A':10,'B':11,'C':12,'D':13,'E':14,'F':15}
    d=0L; exp=1
    if text[0:2]=="0x":
      for i in range(len(text)-1,1,-1):
        c= text[i]
        d= d+ hexdig[c]*exp
        print "hex2dec:",c,d
        exp=exp*16
    """
    try:
      d=eval(text)
      if d<0:
        text=text+'L'
        d= eval(text)
        text= str(d)[:-1]
      else:
        text= str(d)
    except:
      pass
    return text
  def dec2hex(self,text):
    #print "dec2hex:",text
    if text=="" or text==" ":
      return text
    try:
      if text > "2147483647":
        text= text+'L'
        #print "big n:",text
        d= eval(text)
        text= hex(d)[:-1]
      else:
        d=eval(text)
        text= "0x%x"%(d)
    except:
      print 'except'
      pass
    return text
  def printEntry(self, text='MywEntry.printEntry:'):
    print text,self.getEntry()

class MywVMEEntry(MywEntry):
  """ See MywEntry. This class in addition to MywEntry:
  - is initialised by VME value (VME read in __init__)
  - when entry field modified, VME register vmeaddr is updated 
    when: mouse cursor leaves the entry, ENTER is pressed 
    or when label button pressed
  - userupdate(oldval,newval) method: converts the string given by user to
    hex/dec number to be written into vme
  """
  def __init__(self, master, label='label',vmeaddr='VMEADDR',vb=None,
    side='left', helptext="", width=None, userupdate=None):
    self.vb= vb
    self.userupdate= userupdate
    self.vmeaddr= vmeaddr
    self.getvme()
    MywEntry.__init__(self, master, label=label, defvalue=self.vmeval,
    side=side, helptext=helptext, cmdlabel=self.updateentry, width=width,
    textvariable=None, delaction=None,defaultinx=0,name=None)
    self.entry.bind("<Leave>", self.updateentry)
    self.entry.bind("<Key-Return>", self.updateentry)
  def getvme(self):
    if self.vb:
      self.vmeval= self.vb.io.execute("vmeopr32("+self.vmeaddr+")")[:-1]
    else:
      print "MywVMEEntry.getvme(): vb not supplied, returning 0x55aa"
      self.vmeval="0x55aa"
  def updateentry(self, event=None):
    newentry= self.getEntry()
    #print "MywVMEreg:",newentry
    if newentry == self.vmeval: return
    if self.userupdate:
      strforvme= self.userupdate(self.vmeval, newentry)
    else:
      strfotvme= str(self.vmeval)
    self.vmeval= newentry
    #print "MywVMEreg:updating",newentry
    if self.vb:
      self.vb.io.execute("vmeopw32("+self.vmeaddr+", "+
        strforvme+")")
    else:
      print "MywVMEEntry.updateentry(): vb not supplied, writing ", self.vmeval
    
class MywButton(Button, MywHelp):
  """
  If cmd is not supplied, the button appearance resembles Label
  widget. See MywLabel for 'true' label widget.
  label -used as positional parameter sometimes (2nd one)
  state:
  """
  def __init__(self, master, label='butlabel', cmd=None, state=None,
    bg=None,side=None,anchor=None,helptext=None,relief=RAISED):
    # zda sa ze nemusi byt self.but:
    #but= Button(master, text=label, command=cmd, bg=bg, activebackground=bg)
    #but.pack(side=side, expand='yes', fill='x')
    Button.__init__(self,master,text=label, command=cmd, bg=bg, 
      relief=relief,state=state)
    self.normalcolor= Button.cget(self,'background'),\
      Button.cget(self,'activebackground')
    #print "MywButton:",abg,pbg
    if cmd == None:
      Button.configure(self,activebackground=self.normalcolor[0],takefocus=0)
    Button.pack(self,side=side, expand='yes', fill='x', anchor=anchor)
    #if funcdescr and funcdescr[VmeBoard.NFUSAGE]:
    #  MywHelp.__init__(self,master,funcdescr[VmeBoard.NFUSAGE])
    if helptext: MywHelp.__init__(self,master, helptext)
    #print "MywButton:",self.helptext
  def disable(self):
    self.config(state=DISABLED)
  def enable(self):
    self.config(state=NORMAL)
  def setBackground(self, color):
    Button.configure(self,background=color)
    #Button.configure(self,activebackground=color)
  def setColor(self, color):
    self.setBackground(color)
  def resetColor(self):
    #self.checkbut.config(bg=self.normalcolor[0])
    Button.configure(self,bg=self.normalcolor[0])
  def getLabel(self):
    return(self.cget('text'))
  def setLabel(self,name):
    self.configure(text=name)
class MywFrame(Frame):
  def __init__(self, master=None, borderwidth=1, relief=RAISED, side=None,
      bg=None,name=None):
    Frame.__init__(self,master, borderwidth=borderwidth, relief=relief,
      bg=bg,name=name);
    Frame.pack(self,side=side, expand='yes', fill='x')
    #if helptext: MywHelp.__init__(self,master, helptext)

class MywHButtons(MywFrame):
  """
  Creates more buttons in 1 line. Parameters:
  buttons: list of [label, command, arg] items where:
    label:   the button label
    command: command to be executed after the button press
    arg:     parameter supplied to command (optional).
  """
  def __init__(self, master, buttons, side=BOTTOM,helptext=None):
    MywFrame.__init__(self,master);
    self.buttons=[]
    for i in range(len(buttons)):
      but=buttons[i]
      #self.buttons.append(MywButton(master, label=but[0], cmd=but[1], side=LEFT))
      if len(but)>2:
        self.buttons.append(MywButton(master, label=but[0], 
          cmd=curry(but[1],but[2]), side=LEFT, helptext=helptext))
      else:
        self.buttons.append(MywButton(master, label=but[0], 
          cmd=but[1], side=LEFT, helptext=helptext))
    MywFrame.pack(self,side=side, expand='yes', fill='x')
    #addregbut= MywButton(self.mrmaster, label='add reg.', 
    #  cmd=self.addReg, side='bottom')
  def destroy(self):
    for b in self.buttons:
      b.destroy()

class MywMenubutton(Menubutton, MywHelp):
  def __init__(self, master=None, label='noname',helptext=None,side=TOP,
    state=None, bg=None, expand='yes', fill='x',relief=RAISED):
    Menubutton.__init__(self,master,text=label,state=state,
      relief=relief, bg=bg)
    Menubutton.pack(self,side=side, expand=expand, fill=fill)
    if helptext: MywHelp.__init__(self,master,helptext)

class MywMenu(Menu, MywHelp):
  def __init__(self,master=None,helptext=None,cmd=None):
    Menu.__init__(self, master, postcommand=cmd, relief=RAISED)
    if helptext: MywHelp.__init__(self,self,helptext)
    #self.master=master
    self.ccs=[]
    self.ixchoosen=None
  def addcascade(self,cname):
    self.ccs.append(MywMenu())
    self.add_cascade(label=cname, menu=self.ccs[-1])
    return self.ccs[-1]
  def addcommand(self,cname, cmd,disabled=None):
    self.ccs.append([cname,cmd])
    ix= len(self.ccs)
    self.add_command(label=cname, command=curry(cmd,self,ix))
    if disabled:
      self.disable(ix)
  def setcommand(self,cname, cmd,disabled=None):
    ix= self.findLabel(cname)
    #print "setcommand:",cname,ix
    self.entryconfigure(ix, command=curry(cmd,self,ix))
    #self.entryconfigure(ix, command=cmd)
    if disabled:
      self.disable(ix)
  def findLabel(self, label):
    for i in range(1,self.index(END)+1):
       l= self.entrycget(i, "label")
       #print "MywMenu.findLabel:",l
       if label== l:
         return i
    return None
  def disable(self, iix):
    self.enabdisa(iix, DISABLED)
  def enable(self, iix):
    self.enabdisa(iix, NORMAL)
  def enabdisa(self, iix, state):
    if type(iix) is types.IntType:
      self.entryconfigure(iix,state=state)
    elif type(iix) is types.ListType:
      for x in iix:
        if type(x) is types.IntType:
          indx= x
        elif type(x) is types.StringType:
          indx= self.findLabel(x)
        else: continue
        if indx: self.entryconfigure(indx,state=state)

#class MywMBar(Menu, MywHelp):
#  def __init__(self, master=None

class MywBits:
  """
  bits[] -array of items corresponding to bits 0,1,2,...,31
          1 item is:
          -simple string (label naming the corresponding bit) or
          -tuple ("label",0)   ->corresponding bit is DISABLED i.e. 
             GUI-read/only, but allowed to be changed from program
          -tuple ("label",1)   ->corresponding bit is not shown
          -tuple (("l1","l2",...),X) X-see above
           ("l1",...) 2,4,8,16,... labels naming following 1,2,3,4,... 
           bits
  cmd    -callback activated after any modification by mouse
  defval -default value. If changed programmably, call setEntry() to
          upgrade the menu
  """
  def __init__(self, master=None, helptext=None, defval=0,
    side=TOP, label="?", cmd=None, relief=RAISED, bg=None,
    bits=["PP Pre-pulse", "L0", "L1", "L1m L1 message"]):
    self.ilabel=label
    self.cmd=cmd
    self.bits=bits
    self.value= defval
    self.mb= MywMenubutton(master, label=self.ilabel,side=side,
      helptext=helptext, relief=relief, bg=bg);
    self.menu= MywMenu(self.mb,   #cmd=self.hereiam,
      helptext=helptext)
    #self.menu.config(tearoff=0)
    self.cv=[]
    skipuntil=None
    self.rbatr={}
    for bitn in range(0,len(self.bits)):
      self.cv.append(IntVar())
      if skipuntil:
        if bitn<=skipuntil: 
          self.rbatr[bitn]= None   # skipped
          # add next radio button here
          continue
      skipuntil=None
      chb= self.bits[bitn]
      endistate= None; shown=1
      if type(chb) is types.TupleType:
        if chb[1]==0: endistate= DISABLED
        if chb[1]==1: shown=None
        chb= chb[0]
      if self.value & (1<<bitn): self.cv[bitn].set(1)
      if shown:
        if type(chb) is types.TupleType:
          rbits= len(chb)
          if rbits==8: msk= 7<<bitn; lng=3
          if rbits==4: msk= 3<<bitn; lng=2
          if rbits==2: msk= 1<<bitn; lng=1
          self.rbatr[bitn]= [msk,lng]
          self.cv[bitn].set(0)
          for ixrb in range(rbits):
            self.cv[bitn].set((self.value&msk)>>bitn)
          self.menu.add_radiobutton(textvariable=self.cv[bitn],\
            state=endistate, command=self.mcmd)
          skipuntil=bitn+lng-1
        else:
          self.rbatr[bitn]= []
          self.menu.add_checkbutton(label=chb, command=self.mcmd,
            variable=self.cv[bitn], state=endistate)  
    self.mb.config(menu=self.menu)
    self.dolabel()
  #def hereiam(self):
  #  print "hereiam:",self.bits
  def mcmd(self):
    aix= self.menu.index(ACTIVE)
    print "MywBits mcmd:",aix
    if aix!= None:
      #print "active:",aix,self.menu.entrycget(aix,'label')
      msk= 1<<(aix-1)
      c= self.value&msk
      if c:
        self.value= self.value & ~msk
      else:
        self.value= self.value | msk
    else:
      # teared off menu (ACTIVE doesn't work):
      self.value=0
      for ix in range(1, self.menu.index(END)+1):
        cv= self.cv[ix-1].get()
        #print ix,":",self.menu.entrycget(ix,'label'),cv
        if cv==1: self.value= self.value | (1<<(ix-1))
    #print "END:",self.menu.index(END)
    self.dolabel()
    # activate user callback (if present)
    if self.cmd: self.cmd()
  def dolabel(self):
    lbl=self.ilabel+':'
    for bitn in range(0,len(self.bits)):
      if self.rbatr[bitn]== None:   # skipped
        continue
      if len(self.rbatr[bitn])==2:
        lbl= lbl+' '+'RR'
      else:
        chb= self.bits[bitn]
        #endistate= None
        if type(chb) is types.TupleType:
          #if chb[1]==0: endistate= DISABLED
          chb= chb[0]
        #if self.value & (1<<bitn):
        if  self.cv[bitn].get():
          lbl= lbl+' '+string.split(chb,None,2)[0]
        #print "dolabel:",bitn,self.cv[bitn].get(),lbl
    self.mb.config(text=lbl)
  def setEntry(self, val):
    #print "setEntry:",val
    self.value= val
    for bitn in range(0,len(self.cv)):
      chb= self.bits[bitn]
      if self.value & (1<<bitn):
        self.cv[bitn].set(1)
      else:
        self.cv[bitn].set(0)
    self.dolabel()
  def getEntry(self):
    #print "MywBits value:%x"%(self.value)
    return self.value
  def destroy(self):
    self.mb.destroy()
    self.menu.destroy()

class MywMenuList:
  '''
  Button expanding to checkbutton list of buttons.
  label: optional. The label of this menu. If showactive==1, label
         is automatically modified with activating checkbutton:
          label:active1 active2 ...
  items: list of items. 1 item is a string 
         or list of 2 (0,1) items:
    0   -text label (to be displayed), 
    1   -optional. Function to be called, when this entry choosen,
         i.e. set/unset (not implemented for tear off menus)
         This function is activated before cmd (if both present)
  defaults: list of 0/1 for default items to be set
  cmd: function called when any entry changed. 2 parameters
       are passed: self pointer to current MywMenuList instance and
                   index to items pointing to item which was just
                   modified (set/reset)
  '''
  def __init__(self, master=None,label=None, cmd=None,
    helptext=None, defaults=None, side= 'bottom', state=None,
    bg=None,
    showactive=None, items=("text1","text2")):
    self.showactive=showactive
    self.items=items
    self.master= master
    self.cmd=cmd
    self.onoff=[]
    if defaults and len(defaults)== len(self.items):
        self.onoff= defaults
    else:
      for i in range(len(self.items)):
        self.onoff.append(0)
    self.posval=[]
    for i in range(len(self.onoff)):
      self.posval.append(IntVar()); 
      self.posval[i].set(self.onoff[i])
    #
    if label != None:
      labeltxt=label
    else:
      labeltxt=self.items[0]
    self.name=labeltxt
    self.checkbut= MywMenubutton(self.master, helptext=helptext,
      label=labeltxt, state=state, side=side, bg=bg)
    self.normalcolor=self.checkbut.cget('bg'),\
      self.checkbut.cget('activebackground')
    self.rbm= Menu(self.checkbut)
    ixitem=0
    for ch in self.items:
      ixitem= ixitem+1
      if ixitem%20 == 0 and ixitem>0:
        cbreak=1
      else:
        cbreak=None
      #print 'onoff:',self.onoff,ixitem
      if type(ch) is types.StringType:
        chname=ch
      else:
        chname=ch[0]
      self.rbm.add_checkbutton(label=chname,
        variable=self.posval[ixitem-1], command=self.modifname, 
        columnbreak=cbreak)
    self.checkbut['menu']= self.rbm
    if self.showactive: self.dolabel()
    #
    #bad self.rbm.entryconfigure(defaultinx+1, "ACTIVE")
    #self.rbm.invoke(defaultinx+1)
  def modifname(self):
    #print "ACTIVE:",self.rbm.index(ACTIVE)
    inx= self.rbm.index(ACTIVE)
    if inx:
      #print "act. label:",self.rbm.entrycget(self.rbm.index(ACTIVE),'label')
      inx=inx-1
    else:
      # teared off menu (ACTIVE doesn't work -is None for teared-off menu):
      raise NameError, "tearoff not implemented for MywMenuList"
      inx=None; 
      #curv= self.getEntry()
      for ix in range(1, self.rbm.index(END)+1):
        print 'curv:',curv,ix,":",self.rbm.entrycget(ix,'label')
        #if curv==self.items[ix-1][1]: inx=ix-1
        if curv==self.items[ix-1]: inx=ix-1
    #if self.getEntry(inx)==1:
    #  self.setColor("RED")
    #else:
    #  self.resetColor()
    txt="internal error"
    pvg= self.posval[inx].get()
    #print 'pvg:',pvg
    #self.checkbut['text']= self.items[inx][0]
    if type(self.items[inx]) is types.StringType:
      pass
    else:
      #print "calling action for ",self.items[inx][0]
      self.items[inx][1]()
    if self.cmd:
      #print "calling global action for ",self.items[inx]
      self.cmd(self, inx)
    if self.showactive: self.dolabel()
    return
  def dolabel(self):
    lbl= self.name+':'
    for ich in range(len(self.items)) :
      if self.posval[ich].get():
        if type(self.items[ich]) is types.StringType:
          chname=self.items[ich]
        else:
          chname=self.items[ich][0]
        lbl= lbl+' '+chname
    self.checkbut.config(text=lbl)
  def ons(self):
    """
    return number of check buttons switched ON
    """
    non=0
    for index in range(len(self.items)):
      if self.posval[index].get()==1: non=non+1
    return non 
  def enable(self):
    self.checkbut.config(state=NORMAL)
  def disable(self):
    self.checkbut.config(state=DISABLED)
  def setColor(self, color):
    self.color=color
    self.checkbut.config(bg=self.color)
    #self.ButConnect.setBackground(color=self.color)
  def resetColor(self):
    self.checkbut.config(bg=self.normalcolor[0])
  def getEntry(self, index):
    #print "butm:", self.posval.get()
    return(self.posval[index].get()) 
  def setEntry(self, index, val):
    #print "MywMenuList.setEntry",index,":", self.posval[index].get(),'->',val
    return(self.posval[index].set(val)) 
  #def printEntry(self, text='MywMenuList.printEntry:'):
  #  print text,'ix:',self.index,'Entry:',self.getEntry()
  #def popup(self, event):
  #  self.rbm.post(event.x_root, event.y_root)
  #def unpopup(self, event):
  #  self.rbm.unpost()
  def destroy(self):
    self.checkbut.destroy()   # garbage collector does the rest...

class MywxMenu:
  '''
  Button expanding to radio-type menu.
  label: optional. The label of this menu
  delaction(): to be supplied only if one of the items[] contains
    item with value "removevalue" -action to be done, when 
    this item is selected
  items: list of items. 1 item is a string 
         or list of 2 or 3 values (0,1,2):
    0   -text label (to be displayed), 
    1   -text value (can be obtained by getEntry(), 'removevalue' has
                     special meaning)
    2   -optional. Function to be called, when this entry choosen.
         This parameter is ignored, if cmd supplied
  cmd: function to be called when modification done (activated
       before items[2] functions if any)
  defaultinx: index of item in items[] to be taken as default
  '''
  def __init__(self, master=None,label=None, delaction=None,
    helptext=None, defaultinx=0, side= 'bottom', state=None, cmd=None,
    items=[("text1","1"),("text2","2")]):
    self.items=[]
    for itm in items:
      if type(itm) is types.StringType:
        self.items.append((itm,itm))
      else:
        self.items.append(itm)
    self.master= master
    self.cmd= cmd
    self.delaction= delaction
    if defaultinx>=len(items):
      print "myw.MywxMenu: deafaultinx too high:",defaultinx, "setting 0"
      defaultinx=0
    self.index=defaultinx
    #print "MywxMenu:items:", items, defaultinx
    self.posval= StringVar(); self.posval.set(self.items[defaultinx][1])
    self.posvalbefore= self.posval.get()
    self.posinx= defaultinx
    #
    self.radf=Frame(master, borderwidth=1)
    self.radf.pack(side=side)
    if label != None:
      self.label=MywEntry(self.radf,label=label, defvalue='',
        helptext=helptext,side=LEFT)
    #self.radiobut= Menubutton(self.radf, text=self.items[defaultinx][0])
    self.radiobut= MywMenubutton(self.radf, helptext=helptext,
      label=self.items[defaultinx][0], state=state)
    #self.radiobut.pack(side=RIGHT)
    self.rbm= Menu(self.radiobut)
    ixitem=0
    for ch in self.items:
      ixitem= ixitem+1
      if ixitem%20 == 0 and ixitem>0:
        cbreak=1
      else:
        cbreak=None
      self.rbm.add_radiobutton(label=ch[0], value=ch[1],
        variable=self.posval, command=self.modifname, columnbreak=cbreak)
    self.radiobut['menu']= self.rbm
    #
    #bad self.rbm.entryconfigure(defaultinx+1, "ACTIVE")
    #self.rbm.invoke(defaultinx+1)
  def modifname(self):
    #print "ACTIVE:",self.rbm.index(ACTIVE),"posval:",self.posval #or END
    inx= self.rbm.index(ACTIVE)
    if inx:
      #print "act. label:",self.rbm.entrycget(self.rbm.index(ACTIVE),'label')
      inx=inx-1
    else:
      # teared off menu (ACTIVE doesn't work -is None for teared-off menu):
      inx=None; curv= self.getEntry()
      for ix in range(1, self.rbm.index(END)+1):
        #print 'curv:',curv,ix,":",self.rbm.entrycget(ix,'label')
        if curv==self.items[ix-1][1]: inx=ix-1
    self.index= inx   # keep it for getIndex()
    txt="internal error"
    pvg= self.posval.get()
    if pvg == "removevalue":
      #print "MywxMenu: remove me",self.master
      #bavi (iba label) self.radf.destroy()
      #bavi (aj entry removne) self.master.destroy()
      #bavi (aj frame o vsetkymy regs emovne) self.master.master.destroy()
      #?bad idea
      self.master.after_idle(self.delaction, self.master)
    #elif pvg != self.posvalbefore:
    else:
      self.posvalbefore= pvg
      self.posinx= inx
      self.radiobut['text']= self.items[inx][0]
      if self.cmd:
        self.cmd(self, inx)
      elif len(self.items[inx])>2:
        #print "calling action for ",self.items[inx][0]
        self.items[inx][2]()
    return
  def backEntry(self):
    self.posval.set(self.posvalbefore)
    print "backEntry:",self.posval.get(), self.posinx
    self.radiobut['text']= self.items[self.posinx][0]
    #still makeactive:
  def enable(self):
    self.radiobut.config(state=NORMAL)
  def disable(self):
    self.radiobut.config(state=DISABLED)
  def getEntry(self):
    #print "butm:", self.posval.get()
    return(self.posval.get()) 
  def getIndex(self):
    """ returns index of active item (0,1,...) in supplied items
    """
    return(self.index)
  def printEntry(self, text='MywxMenu.printEntry:'):
    print text,'ix:',self.index,'Entry:',self.getEntry()
  #def popup(self, event):
  #  self.rbm.post(event.x_root, event.y_root)
  #def unpopup(self, event):
  #  self.rbm.unpost()
  def destroy(self):
    self.radf.destroy()   # garbage collector does the rest...
  def setColor(self, color):
    #self.color=color
    self.radiobut.config(bg=color)
    #self.ButConnect.setBackground(color=self.color)
  def resetColor(self):
    #self.normalcolor= COLOR_BGDEFAULT
    #self.normalcolor= Button.cget(self,'background'),\
    #  Button.cget(self,'activebackground')
    self.radiobut.config(bg=COLOR_BGDEFAULT)
class MywLabel(Label,MywHelp):
  def __init__(self, master=None, label=None, helptext=None,
      borderwidth=0, width=None, relief=RAISED, 
      side=None, bg=None, expand='yes'):
    Label.__init__(self,master, text=label,borderwidth=borderwidth, 
      width=width,relief=relief,bg=bg);
    Label.pack(self,side=side, expand=expand, fill='x')
    if helptext: MywHelp.__init__(self,master, helptext)
  def label(self, newlabel):
    self.configure(text=newlabel)

class FunStart:
  def fcallstart(self):
    cmdline=self.fn+"("
    #print "fcallstart:"
    if len(self.ient)>0:
      for e1 in self.ient:
        #print 'FunStart.cmdline:',cmdline
        cmdline=cmdline+e1.getEntry()+","
    else:
      cmdline=cmdline+" "
    #if len(self.ient)>0:
    cmdline=cmdline[:-1]+")"
    #else:
    #  cmdline=cmdline+")"
    if self.vb.io == None: self.vb.openCmd()
    #self.vb.io.cmd.setEntry(cmdline); 
    self.vb.io.execute(cmdline)
  def fcallstop(self):
    if self.inxMenu:
      self.inxMenu.entryconfigure(self.ginx, state='normal')
    else:
      self.inx.configure(state='normal')
    self.rwf.destroy()
  def __init__(self, vb, fnix):
    """
    vb    -VmeBoard instance
    fnix  - index info vb.funcs
    """ 
    #print "FunStart:", fnix," ",vb.funcs[fnix], vb.funcsm[fnix]
    # vb.funcs[fnix]: [GroupName,HelpText,FunType,FunName,
    #                   [[ParName1,ParType1,IdirectFlag],...]]
    #print "FunStart.vb:", vb.boardName,vb.funcsm
    self.fn= vb.funcs[fnix][VmeBoard.NFNAME]
    self.vb= vb
    self.ient= []
    #inx   - index (1..) in corresponding Menu, or pointer to Button:
    if vb.funcs[fnix][0] == None:   #button (no group func)
      self.inxMenu= None
      self.inx= vb.ngf[vb.funcsm[fnix][0]]
    else:
      #print "entrycget:",vb.gmbs[vb.funcsm[fnix][0]]
      self.inx= vb.funcsm[fnix][0]
      self.ginx= vb.funcsm[fnix][1]
      self.inxMenu= vb.gmbs[self.inx*2+1]
      # following returns None if menu was torn off:
      #self.inx= self.inxMenu.index(ACTIVE)
      #print "entrycget ",self.inx," ",self.inxMenu.entrycget(self.inx,"label")
      #print "entrycget ACTIVE ",self.inxMenu.entrycget(ACTIVE,"label")
    #print "FunStart...",self.inx, self.inxMenu
    if len(vb.funcs[fnix][VmeBoard.NPARDESC])==0:
      #self.ient.append(MywEntry(master=self.rwf,label='help', defvalue='',
      #  side='left', helptext=vb.funcs[fnix][VmeBoard.NFUSAGE]))
      self.fcallstart()   
    else:
      self.rwf=Toplevel(vb.vmebf)
      cr= getCrate()
      if cr: self.rwf.transient(cr.master)
      self.rwf.title(self.vb.boardName+'.'+self.fn)
      # following not OK if menu was torn off:
      #self.inxMenu.entryconfigure(ACTIVE, state='disabled')
      if self.inxMenu:
        self.inxMenu.entryconfigure(self.ginx, state='disabled')
      else:
        self.inx.configure(state='disabled')
      for ip in vb.funcs[fnix][VmeBoard.NPARDESC]:
        #print "PAR",ip
        pname=ip[VmeBoard.NPARDESCNAME]
        dflval=" "
        if ip[VmeBoard.NPARDESCTYPE]=='char' and ip[VmeBoard.NPARDESCIND]=="*":dflval="\" \""
        self.ient.append(MywEntry(master=self.rwf,label=pname, 
          side='top', defvalue=dflval,
          helptext=vb.funcs[fnix][VmeBoard.NFUSAGE]))
      startbut= MywButton(self.rwf, label='start', cmd=self.fcallstart, side='left')
      okbut= MywButton(self.rwf, label='quit', cmd=self.fcallstop, side='left')

# this can be used only through VmeBoard (boardmod)
class MywMenu81632(MywxMenu):
  def modifname(self):
    MywxMenu.modifname(self)
    #print "ACTIVE:",self.rbm.index(ACTIVE)       #or END
    self.boardmod.modexit()
    #self.radiobut['text']= self.rbm.entrycget(
    #  self.rbm.index(ACTIVE),'label')

class VmeBoard:
  NGUINAME=5
  NPARDESC=4
  NFNAME=3
  NFTYPE=2
  NFUSAGE=1
  NFGROUP=0
  NPARDESCNAME=0
  NPARDESCTYPE=1
  NPARDESCIND=2
  def ZNCdestroybf(self, event):
    #try:
    #  print "destroybf ", event.widget, ":",self.io.f, ":", self.io.tp
    #except:
    #  print "exception ", sys.exc_info()[0]
    #if event.widget == self.io.f:
    #  print "OK, cmdlin2 widget destroyed"
    del self.io; self.io= None; self.ButConnect.configure(fg="black")
  def delio(self):
    self.io= None; 
    if self.ButConnect:
      self.ButConnect.configure(fg="black")
  def openCmd(self):
    """ Start 'board interface'
    - popen2
    - create top level window for stdin/stdout
    """
    import cmdlin2
    #print "here openCmd ",self.boardName
    #self.ButConnect.configure(state="disabled")
    if self.io==None:
      cm= os.path.join(self.boardName, self.boardName)
      cm= cm+'.exe '+self.baseAddr
      #print ":",cm,":"
      self.io= cmdlin2.cmdlint(cmd=cm, board=self)
      #self.io.tp.bind("<Destroy>", self.destroybf)
      self.ButConnect.configure(fg="red")
    else:
      #self.io.stop()
      #del self.io; self.io= None; self.ButConnect.configure(fg="black")
      self.io.execute("nop",ff= self.emptyfun)
  def emptyfun(self,txt):
    pass
    #print 'emptyfun:',txt,'---'
  def funvmerw(self):
    multregs= VmeRW(self)
  def multreg(self):
    multregs= MultRegs(self)
  def findvmeregtyp(self, reg):
    tx="badregtype"
    for rg in self.vmeregs:
      if reg==rg[0]:
        if rg[2] == '': tx="w32"
        if rg[2] == '0x04000000': tx="w16"
        if rg[2] == '0x02000000': tx="w8"
        break
    return(tx)
  def startFun(self, fnix):
    fn= self.funcs[fnix][VmeBoard.NFNAME]
    #print "here startFun F:", fn, "fnix:", fnix
    if self.funcs[fnix][VmeBoard.NFTYPE]=='GUI':
      modname= self.boardName+"_u"
      #print modname
      #__import__(modname)
      exec('import '+modname)
      #print 'cmdeval:',modname,':',fn
      # let self.io is always defined for user graphics:
      if self.io== None: self.openCmd()                 
      exec('rc='+modname+'.'+fn+'(self)')
      #print "startFun:rc:",rc
      #rc.hereiam()
    else:
      #znc self.fust.append(FunStart(self, fnix))
      FunStart(self, fnix)
  def funbuts(self):
    #print "here funbuts"
    #self.funcs= [[None, '','w32', 'init', [['preg2', 'w32', '']]], [None, 'usagehelp','void', 'Doit', []], ['MBcard','usghlp', 'void', 'setGlobalReg', [['reg', 'int', ''], ['val', 'w32', '*']]]]
    self.groups=[]
    for f in self.funcs:
      gn=f[VmeBoard.NFGROUP]
      if gn in self.groups or gn==None:
        continue
      self.groups.append(gn)
    # order numbers of the func in ngf (N,0) or gmbsi (N,I) I->order number
    # in correponding menu:
    self.funcsm={}
    #--------------------- TOP (or no GROUPsfuncs):
    self.ngf=[]
    for ix in range(len(self.funcs)):
      if self.funcs[ix][VmeBoard.NFGROUP] == None:   # TOP fun
        if len(self.funcs[ix])>=(VmeBoard.NGUINAME+1):
          fn= self.funcs[ix][VmeBoard.NGUINAME]
        else:
          fn= self.funcs[ix][VmeBoard.NFNAME]
        cmdh= lambda s=self,x=ix:s.startFun(x)
        self.ngf.append(MywButton(self.vmebf, label=fn,
          # funchelp -help for just this function
          cmd= cmdh, side='top', helptext=self.funcs[ix][VmeBoard.NFUSAGE]))
        # order number (0,...) in correspondig/top group
        self.funcsm[ix]= (len(self.ngf)-1,0)
        #print "funbuts1:",fn,"self.funcm[",ix,"]=",self.funcsm[ix]
    #---------------------- GROUP functions:
    self.gmbs=[]
    for gn in self.groups:
      if string.find(self.hiddenfuncs," "+gn)!=-1: continue
      # funchelp -for just this group (see comp.py, self.groups)
      self.grouphelp={}
      self.grouphelp[gn]=''
      for ix in range(len(self.funcs)):
        if gn == self.funcs[ix][VmeBoard.NFGROUP]:
          self.grouphelp[gn]= self.grouphelp[gn]+\
            '========== '+\
            self.funcs[ix][VmeBoard.NFNAME]+'\012'+\
            self.funcs[ix][VmeBoard.NFUSAGE]
        if self.grouphelp[gn] and (self.grouphelp[gn][-1] != '\012'):
           self.grouphelp[gn]= self.grouphelp[gn] + '\012'
      self.gmbs.append(MywMenubutton(self.vmebf, label=gn,\
        helptext=self.grouphelp[gn]))
      #
      #prepare help from all the helps in the group:
      self.gmbs.append( MywMenu(self.gmbs[-1],
        helptext=self.grouphelp[gn]))
      self.gmbs[-1].config(tearoff=1)
      #self.gmbs[-2]["menu"]= self.gmbs[-1]    alebo:
      self.gmbs[-2].config(menu= self.gmbs[-1])
      gix=0   # func. number in corresponding group (for disable/normal state)
      # not working properly?
      # named groups (not TOP):
      for ix in range(len(self.funcs)):
        if gn == self.funcs[ix][VmeBoard.NFGROUP]:
          #print "funbuts1:",gn
          if len(self.funcs[ix])>=(VmeBoard.NGUINAME+1):
            labname= self.funcs[ix][VmeBoard.NGUINAME]
          else:
            labname= self.funcs[ix][VmeBoard.NFNAME]
          #print "funbuts2:",self.funcs[ix],labname
          # lambda isn't correct for tear off menu
          cmdh= lambda s=self,x=ix:s.startFun(x)
          self.gmbs[-1].add_command(label=labname, command=cmdh)
          gix=gix+1
          self.funcsm[ix]= (len(self.gmbs)/2-1, gix)
          #print "funbuts3:",fn,"self.funcm[",ix,"]=",self.funcsm[ix]
  def getcf(self):
    self.funcs=[]
    try:
      bdir= os.path.join( os.environ['VMECFDIR'],
        self.boardName, self.boardName)
      cff= bdir+'_cf.py'
      execfile(cff)
      # self.baseAddr,spaceLength,vmeregs,funcs,hiddenfuncs
    except:
      print self.boardName+'_cf.py'+" doesn't exist or incorrect"
    else:
      #cff.close()
      pass
  def delBoard(self):
    if self.io:
      self.io.stop()
    self.vmebf.destroy()
    self.ButConnect=None
  def setColor(self, color):
    if color=="original": color=self.color
    self.vmebf.configure(bg=color)
    self.ButConnect.setBackground(color=color)
  def __init__(self, crate=None, boardName="abc", baseAddr="",color=None,
    initboard="yes"):
    #Frame.__init__(self, master, borderwidth=3)
    self.crate= crate
    self.master=crate.crframe;
    self.boardName= boardName
    self.initboard= initboard
    self.vmeregs=None; 
    self.getcf()   # self.(vmeregs[],baseAddr,spaceLength,funcs[])
    if baseAddr != "": self.baseAddr= baseAddr   # has to be after getcf()
    self.fungrps=[]
    if color==None:
      if boardName=='ltu': color="green"
      elif boardName=='ttcvi': color="#66cc00"
      elif boardName=='fo': color="#00ccff"
      elif boardName=='busy': color="#33ccff"
      elif boardName=='l0': color="#66ccff"
      elif boardName=='l1': color="#99ccff"
      elif boardName=='l2': color="#ccccff"
      elif boardName=='int': color="#ffccff"
      else: color="#ff9900"
      
    self.color= color
    self.io= None   #user interace not opened
    # create work directory if not existing:
    if self.baseAddr[0:6]=='VXI0::':
      self.workdir= os.path.join( os.environ['VMEWORKDIR'],"WORK", self.boardName+self.baseAddr[6:])
    else:
      self.workdir= os.path.join( os.environ['VMEWORKDIR'],"WORK", self.boardName+self.baseAddr)
    if os.access(self.workdir, os.W_OK)!=1:
      try:
        os.mkdir(self.workdir) 
      except:
        print "Cannot create work directory:", self.workdir
        print "exception:", sys.exc_info()[0]
    #self.vmefuns= {}
    self.vmebf= Frame(self.master, borderwidth=4, relief="raised",bg=color)
    self.vmebf.pack(side="left", expand='yes', fill='y')
    self.ButConnect= MywButton(self.vmebf, bg=color, \
      label=boardName+' '+self.baseAddr, \
      cmd= self.openCmd, side="top", helptext="Base addr: "+self.baseAddr+"""
This button starts main log/cmd window 
if it is not started yet.
Main log/cmd window is started by itself if necessary.
""") 
    # standard funcs:
    self.ButFunctions= MywMenubutton(self.vmebf, label="Stdfuncs",
      helptext="access to VME registers") 
    self.FunMenu= Menu(self.ButFunctions)
    #self.ButFunctions.config(menu= self.FunMenu)
    self.ButFunctions['menu']= self.FunMenu
    self.FunMenu.add_command(label="VME r/w", command=self.funvmerw)
    self.FunMenu.add_command(label="multiregs", command=self.multreg)
    """ attempt to solve problem in cygwin by replacing with MywxMenu:
        which didn't rectify the behaviour after opening ioWindow
    self.ButFunctions= MywxMenu(self.vmebf, label="Stdfuncs",
      items=[["VME rw", "0", self.funvmerw],
        ["Multiregs", "1", self.multreg]],
      helptext="access to VME registers") 
    """
    #
    # user funcs:
    self.funbuts()
    if self.initboard=='nbi' and self.boardName=='ltu':
      self.openCmd()
      #print ":", self.io.execute("getsgmode()",applout='<>')[0], ":"
      if self.io.execute("getsgmode()",applout='<>')[0] == '0':
         self.setColor(COLOR_WARNING)
    #
    """ from 23.6. init.mac is called directly from cmdbase.c
    initmac= os.path.join( os.environ['VMEWORKDIR'],"CFG",
      self.boardName, "init.mac")
    if os.access(initmac, os.R_OK):
      self.openCmd()
      #ToDo: execute(init() only:
      # if /tmp/BoardName_busy.PID == self.io.thds[0].pidexe OR
      #    /tmp/boardName_busy doesn't exist
      # OR (seems better) do it in cmdbase (modify macro processing)
      self.io.execute("init()")
    """

class VmeCrate:
  _instance= None
  def __init__(self, master=None):
    self.boards=[]
    self.autohelps=None
    if self.autohelps==None:
      print "Use right mouse button to get help"
    self.master=master
    self.crframe= Frame(master)
    self.crframe.pack(side="top")
    self.crbuts= Frame(master)
    self.crbuts.pack(side="bottom", expand='yes', fill='x')
    okbut= MywButton(self.crbuts, label='quit', cmd= self.quit,side="bottom") 
    self._instance= self
  def addBoard(self, board):
    self.boards.append(board)
  def findBoard(self, boardname):
    for b in self.boards:
      if b.boardName==boardname:return(b)
    return(None)
  def quit(self):
    for b in self.boards:
      b.delBoard()
    self.master.destroy()

def getCrate(f=None):
  if VmeCrate._instance==None:
    if f==None:
      #there has to be VmeCrate._instance for vmeboards software
      # i.e. this is the call when used outside of 'vmecrate' sw
      return None
    else:
      # first (and only call with f!=None) from crate.py
      VmeCrate._instance= VmeCrate(f)
  return VmeCrate._instance

def checklabel():
  print "here checklabel"
def checklabel2():
  print "here checklabel2"
  #print event,b
def prerror():
  global butsFrame
  xy=butsFrame.winfo_rootx(),butsFrame.winfo_rooty()
  MywError("this error message\n overlaps button Frame",xy)
def main():
  global butsFrame
  f = Tk()
  #f.config("Myw examples")
  #----------------------------------------------------entry:
  #f.option_add("bLUEcolor*background","LimeGreen")
  # seems not to work with the equal name for more instances
  # (look for bLUEcolor)
  #entriesFrame=MywFrame(f, side=LEFT,name="bLUEcolor"); 
  entriesFrame=MywFrame(f, side=LEFT); 
  entriesFrame.config(bg="blue")
  lb=MywEntry(entriesFrame,label="MywEntry with help/cmd:",
    side=TOP, defvalue='abc',cmdlabel=checklabel,helptext="abc\n\
  2 riadok\ntreti\n\
  stvrty\n\
piaty")
  lb3=MywEntry(entriesFrame,label="MywEntry with help/nocmd:",
    side=TOP, defvalue='abc',helptext="abc help")
  lb2=MywEntry(entriesFrame,label="MywLUT", 
    defvalue='a|b&c',side='top', bind='r',cmdlabel=checklabel2)
  #lb4=MywVMEEntry(entriesFrame, label="VMEreg", helptext="automatic update of VME register", vmeaddr="0x88")
  lb.getEntry()
  #but=Button(entriesFrame, text="print entry", command=lb.printEntry) 
  #but.pack(side=TOP, expand='yes', fill='x')
  #----------------------------------------------------buttons:
  butsFrame=MywFrame(f, side=LEFT); 
  butsFrame.config(bg="yellow")
  #
  doerrbut=MywButton(butsFrame,label="Make error",cmd=prerror)
  radiob=MywRadio(butsFrame,label='MywRadio\nbutton')
  #
  #passing parameter to callback function (lambda):
  prent= lambda i=radiob,x='callback printEntry': i.printEntry(x)
  prent(i=radiob,x='direct printEntry')
  but=MywButton(butsFrame, label="MywButton-print radio", 
    cmd=prent) 
  #another approach to callback with parameters (positional par is OK too):
  ccbpe='curry callback printEntry'
  but=MywButton(butsFrame, label="MywButton-print radio\ncurry", 
    cmd=curry(radiob.printEntry,text=ccbpe)) 
  butExit=MywButton(butsFrame, label="exit", cmd=f.destroy)
  #-----------------------------------------------------menus:
  ##f.mainloop(); return
  #menusFrame=MywFrame(f, side=LEFT,name="bLUEcolor"); 
  menusFrame=MywFrame(f, side=LEFT); 
  menusFrame.config(bg="pink")
  #wid= menusFrame.winfo_id(); widp=menusFrame.winfo_pathname(wid)
  #print "wid:",wid,"widp:",widp,"winfo_name:",menusFrame.winfo_name()
  menub=MywxMenu(menusFrame,label="MywxMenu", items=(("txt1","b1"),
    ("txt2","b2"), ("txt3","b2")))
  menubl=MywMenuList(menusFrame,label="MywMenuList", 
    items=("txt1","b1", "txt3"), defaults=[0,1,1])
  #menubl.disable()
  simplebut= MywButton(menusFrame, label="MywButton", 
    cmd=menub.printEntry,
    helptext="print MywxMenu value") 
  bitsmenu= MywBits(menusFrame,label="MywBits demo", 
    bits=["L0","PP Pre-pulse", (("r1","r2","r3","r4"),None), 
      "L1", "L1m L1 message"],
    helptext="MywBits demonstration")
  #-------------------------------------------- Error messages
  xy=butsFrame.winfo_rootx(),butsFrame.winfo_rooty()
  #MywError("butsFrame is not overlaped (mainloop?)\nby this window",xy)
  #--------------------------------------------BitsPlay:
  biplFrame=MywFrame(entriesFrame,bg="pink");
  #mask: 0x3
  b1=MywxMenu(biplFrame, items=(("bit0","0x1"),("bit1","0x2")),
    side=LEFT,helptext="bits 0x3")
  b1.radiobut.configure(relief=FLAT)
  #mask: 0xc
  b2=MywxMenu(biplFrame, items=(("bit2","0x4"),("bit23","0xc"),("bit23=0","0")),
    side=LEFT,helptext="bits 0xc")
  b2.radiobut.configure(relief=FLAT)
  b1b2e=MywEntry(biplFrame,label="bits:", 
    defvalue=' ',side='top')
  lb.getEntry()
  #
  #for n in range(1,20):
  #  but.flash()
  f.mainloop()

if __name__ == "__main__":
    main()

