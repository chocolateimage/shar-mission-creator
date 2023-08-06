import wx
import wx.aui
import wx.adv
import wx.lib.scrolledpanel as scrolled
from collections import OrderedDict
import configparser
import os, sys
import json
import pydub
import zlib
import traceback
import struct
import pyperclip
import math

program_version = "0.0.1"
file_wildcard = "SHAR Mission Creator files (*.smc)|*.smc"

def load_data_json(filename):
    with open("data/" + filename,"r") as f:
        return json.loads(f.read())


def modpath(root,path):
    return os.path.join(root,path)
def createfolder(root,path=""):
    if path == "":
        fullpath = root
    else:
        fullpath = modpath(root,path)
    if not os.path.exists(fullpath):
        os.makedirs(fullpath)
def addzero(number):
    return ("0" + str(number))[-2:]
def get_level_folder(levelnumber):
    return "level" + addzero(levelnumber)
def write_to_file(filepath,contents):
    folderpath = os.path.dirname(filepath)
    if not os.path.exists(folderpath):
        os.makedirs(folderpath)
    with open(filepath,"w+") as f:
        f.write(contents)

def ask(parent=None, message='', default_value=''):
    dlg = wx.TextEntryDialog(parent, message, value=default_value)
    if dlg.ShowModal() == wx.ID_OK:
        result = dlg.GetValue()
        dlg.Destroy()
        return result
    else:
        dlg.Destroy()
        return None


class MyClassCompleterSimple(wx.TextCompleterSimple):
    def __init__(self, choices=[]):
        wx.TextCompleterSimple.__init__(self)
        self.choices = choices

    def GetCompletions(self, prefix):
        if len(prefix) < 0:
            return []
        res = []
        prfx = prefix.lower()
        for item in self.choices:
            if item.lower().startswith(prfx):
                res.append(item)

        return res

class TemplateGroupBox(wx.StaticBox):
    def __init__(self,parent,title):
        super().__init__(parent,-1,title)
        self.sizer = wx.StaticBoxSizer(self, wx.VERTICAL)

class LocationListEditor(wx.Frame):
    def __init__(self,ll,btn):
        super().__init__(mw,title="Locator Type "+str(ll.locatortype)+" List Editor",size=(400,400),style=wx.DEFAULT_FRAME_STYLE | wx.FRAME_FLOAT_ON_PARENT)
        self.CenterOnParent()
        self.SetMinSize((370,200))
        self.ll = ll
        toolbar = self.CreateToolBar(wx.TB_HORZ_TEXT)
        toolbar_newlocator = toolbar.AddTool(wx.ID_ADD,"New Locator",wx.ArtProvider.GetBitmap(wx.ART_PLUS))
        self.Bind(wx.EVT_MENU,self.addnew,toolbar_newlocator)
        toolbar_refresh = toolbar.AddTool(wx.ID_REFRESH,"Refresh",wx.ArtProvider.GetBitmap(wx.ART_REDO))
        self.Bind(wx.EVT_MENU,self.reload,toolbar_refresh)
        self.scrollpanel = scrolled.ScrolledPanel(self)
        self.bs = wx.BoxSizer(wx.VERTICAL)
        self.scrollpanel.SetSizer(self.bs)
        self.copytimer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER,self.ontimertick,self.copytimer)
        self.copytimer.Start(20)
        self.lastclipboard = pyperclip.paste()
        self.reload()
    def ontimertick(self,event=None):
        newclip = pyperclip.paste()
        if newclip == self.lastclipboard:
            return
        self.lastclipboard = newclip
        lines = str(newclip).splitlines()
        if not lines[0].startswith("Debug mode: position"):
            return
        posx = -1
        posy = -1
        posz = -1
        for i in lines:
            if i.startswith("Pos X:"):
                posx = float(i.removeprefix("Pos X:").strip())
            if i.startswith("Pos Y:"):
                posy = float(i.removeprefix("Pos Y:").strip())
            if i.startswith("Pos Z:"):
                posz = float(i.removeprefix("Pos Z:").strip())
        if posx == -1 or posy == -1 or posz == -1:
            return
        self.ll.thelist.append({"x":posx,"y":posy,"z":posz})
        self.reload()
    def addnew(self,event=None):
        self.ll.thelist.append({"x":0,"y":0,"z":0})
        self.reload()
    def reload(self,event=None):
        self.scrollpanel.DestroyChildren()
        self.bs.Add(wx.StaticText(self.scrollpanel,label="Format: X Y Z"),0,wx.EXPAND | wx.ALL,8)
        attributes = ["x","y","z"]
        for i,v in enumerate(self.ll.thelist):
            p = wx.Panel(self.scrollpanel)
            p.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE))
            bs = wx.BoxSizer()
            for j in attributes:
                self.add_item(p,bs,i,v,j)
            deletebtn = wx.BitmapButton(p,id=wx.ID_DELETE,bitmap=wx.ArtProvider.GetBitmap(wx.ART_DELETE))
            deletebtn.Bind(wx.EVT_BUTTON,lambda event,i=i:self.delete_item(i))
            bs.Add(deletebtn,flag=wx.ALL,border=8)
            p.SetSizerAndFit(bs)
            p.Layout()
            p.Fit()
            self.bs.Add(p,0,wx.EXPAND | wx.ALL)
        self.bs.Layout()
        self.scrollpanel.FitInside()
        #self.bs.FitInside(self.scrollpanel)
        self.scrollpanel.SetupScrolling(False,True)
        print(self.GetSize(),self.bs.GetSize(),self.scrollpanel.GetSize())
    def delete_item(self,index):
        self.ll.thelist.pop(index)
        self.reload()
    def add_item(self,p,bs,i,v,j):
        ctrl = wx.TextCtrl(p,value=str(v[j]))
        ctrl.Bind(wx.EVT_TEXT,lambda eve: self.ll.set_value(i,j,float(ctrl.GetValue())))
        bs.Add(ctrl,1,flag=wx.EXPAND | wx.ALL,border=8)
    def onClose(self,event):
        self.copytimer.Stop()

class LocationList():
    def __init__(self,locatortype):
        self.thelist = []
        self.locatortype = locatortype
    def show_editor(self,btn):
        editor = LocationListEditor(self,btn)
        editor.Show(True)
    def set_value(self,index,key,value):
        print(index,key,value)
        self.thelist[index][key] = value

class FreeSelectionList():
    def __init__(self,thelist,value=""):
        self.thelist = thelist
        self.value = value
    def set_value(self,value):
        self.value = value

class StrictSelectionList():
    def __init__(self,thelist,value=""):
        self.thelist = thelist
        self.value = value
    def set_value(self,value):
        self.value = value
        if value == "pickupitem":
            wx.MessageBox("Use \"goto\" instead of \"pickupitem\".")
            self.value = "goto"
            mw.pnl3.loadstage(mw.pnl3.stage)

class ConversationEditor(wx.Frame): # in 1 week i don't know what this does anymore
    class ConversationList(wx.StaticBox):
        def __init__(self,parent,title,custom):
            super().__init__(parent,-1,title)
            self.custom = custom
            self.generated_list = []
            self.sbs = wx.StaticBoxSizer(self, wx.VERTICAL)

            self.topthing = wx.BoxSizer()

            self.searchinput = wx.TextCtrl(self)
            if custom:
                self.searchinput.SetHint("Add/search")
            else:
                self.searchinput.SetHint("Search by conversation name")
            self.searchinput.Bind(wx.EVT_TEXT,self.reload)
            self.topthing.Add(self.searchinput,1,flag=wx.EXPAND)

            if custom:
                self.addbtn = wx.BitmapButton(self,bitmap=wx.ArtProvider.GetBitmap(wx.ART_PLUS))
                self.addbtn.Bind(wx.EVT_BUTTON,self.add_custom)
                self.topthing.Add(self.addbtn,0,flag=wx.LEFT,border=4)
            
            self.sbs.Add(self.topthing,flag=wx.EXPAND | wx.ALL,border=8)

            self.listbox = wx.ListBox(self)
            self.listbox.Bind(wx.EVT_LISTBOX_DCLICK,parent.select_item)
            self.sbs.Add(self.listbox,1,flag=wx.EXPAND | wx.BOTTOM | wx.LEFT | wx.RIGHT,border=8)

            self.Layout()
            self.FitInside()

            self.reload()
        def add_custom(self,event=None):
            try:
                self.add_custom_(event)
            except Exception:
                wx.MessageBox("Error converting. Make sure you installed ffmpeg and added it to PATH.\nIf you have questions or experience more problems, contact \"chocolateimage\" on Discord.\n\n" + traceback.format_exc())
        def add_custom_(self,event=None):
            convname = self.searchinput.Value
            if convname == "":
                return wx.MessageBox("Enter the name of the conversation (all in one word, no underscores)\ninto the search bar.")
            selectedstage = mw.get_curstage()
            if selectedstage == None or selectedstage.objectivetype.value != "dialogue":
                return wx.MessageBox("Select the dialogue stage")
            mission = None
            for i in mw.save.missions:
                if selectedstage in i.stages:
                    mission = i
            dlg = wx.FileDialog(self.Parent,"Select your audio files (will be added in alphabetical order)",style=wx.FD_DEFAULT_STYLE | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE)
            if dlg.ShowModal() == wx.ID_OK:
                filenames = dlg.GetPaths()
                if len(filenames) > 9:
                    return wx.MessageBox("You can't have more than 9 lines.")
                filenames.sort()
                print("doing conversion: " + str(filenames))
                needto_dialogscript = False
                dialogscript = modpath(mw.save.modpath,"CustomFiles/sound/scripts/dialog.spt")
                if not os.path.exists(dialogscript):
                    needto_dialogscript = True
                progressnow = 0
                progressmax = len(filenames)
                if needto_dialogscript:
                    progressmax += 1
                progressbar = wx.ProgressDialog("Converting conversations...","Initializing...",progressmax,self.Parent,style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE)
                progressbar.Show(True)
                if needto_dialogscript:
                    print("dialog.spt")
                    progressbar.Update(progressnow,"Creating dialog.spt")
                    progressnow += 1
                    createfolder(os.path.dirname(dialogscript))
                    with open("data/dialog.dat","rb") as f:
                        with open(dialogscript,"wb+") as f2:
                            f2.write(zlib.decompress(f.read()))
                npcnamelist = []
                for i in range(len(filenames)):
                    npcnamelist.append(selectedstage.o_dialogue_npc.value)
                    npcnamelist.append(selectedstage.o_dialogue_pc.value)
                if selectedstage.o_dialogue_startwith.value == "PC":
                    npcnamelist.pop(0)
                for i,v in enumerate(filenames):
                    filename = os.path.basename(v)
                    print(filename)
                    createfolder(os.path.dirname(dialogscript))
                    progressbar.Update(progressnow,"Converting " + filename)
                    progressnow += 1
                    audio_segment = pydub.AudioSegment.from_file(v)
                    left_channel = audio_segment.split_to_mono()[0]
                    dialoguecode = dialoguecodes[npcnamelist[i]]
                    filename_inner = "C_" + convname + "_" + str(i + 1) + "_convinit_"+dialoguecode+"_" + mission.get_lm(False)
                    print(filename_inner)
                    final_path = modpath(mw.save.modpath,"CustomFiles/conversations/" + filename_inner + ".ogg")
                    createfolder(os.path.dirname(final_path))
                    left_channel.export(final_path,format="ogg",parameters=["-ar","24000"])
                    dialogscript_contents = ""
                    with open(dialogscript,"r") as f:
                        dialogscript_contents = f.read()
                    if filename_inner not in dialogscript_contents:
                        print("need to add " + filename_inner + " to dialog.spt")
                        dialogscript_contents += "\n\n"
                        dialogscript_contents += "create daSoundResourceData named " + filename_inner + "\n"
                        dialogscript_contents += "{\n"
                        dialogscript_contents += "    AddFilename ( \"conversations/"+filename_inner+".rsd\" 1.000000 )\n"
                        dialogscript_contents += "    SetStreaming ( true )\n"
                        dialogscript_contents += "}\n"
                        with open(dialogscript,"w+") as f:
                            f.write(dialogscript_contents)
                    else:
                        print("don't need to add " + filename_inner + " to dialog.spt")
                print("done converting")
                progressbar.Update(progressnow,"Done. Close this window to continue.")
                self.reload()
        def reload(self,event=None):
            self.listbox.Clear()
            thelist = []
            if self.custom:
                conversationspath = modpath(mw.save.modpath,"CustomFiles/conversations")
                if os.path.exists(conversationspath):
                    for i in os.listdir(conversationspath):
                        if i.lower().startswith("c_"):
                            convname = i.split("_")[1]
                            if convname not in thelist:
                                thelist.append(convname)
            else:
                if len(self.generated_list) == 0:
                    self.generated_list = load_data_json("convnames.json")
                thelist = self.generated_list
            for i in thelist:
                if self.searchinput.Value in i:
                    self.listbox.Append(i)
    def __init__(self,cv,btn):
        super().__init__(mw,title="Conversation editor",size=(500,400),style=wx.DEFAULT_FRAME_STYLE | wx.FRAME_FLOAT_ON_PARENT)
        self.CenterOnParent()
        self.parentbtn = btn
        self.cv = cv
        self.hbox = wx.BoxSizer()
        self.builtin = ConversationEditor.ConversationList(self,"Built-in",False)
        if mw.save.modpath != "":
            self.customlist = ConversationEditor.ConversationList(self,"Custom",True)
            self.hbox.Add(self.customlist.sbs,1,wx.EXPAND | wx.ALL,border=12)
        else:
            self.hbox.Add(wx.StaticText(self,label="Select a modpath to\nuse custom conversations",style=wx.ALIGN_CENTER),1,wx.EXPAND | wx.ALL,border=12)
        self.hbox.Add(self.builtin.sbs,1,wx.EXPAND | wx.ALL,border=12)
        self.SetSizer(self.hbox)
        self.SetAutoLayout(1)
    def select_item(self,event):
        txt = event.GetString()
        if self.parentbtn != None:
            self.parentbtn.SetLabelText(txt)
        self.cv.set_value(txt)
        self.Close()
class ConversationValue():
    def __init__(self,value=""):
        self.value = value
    def show_editor(self,btn=None):
        editor = ConversationEditor(self,btn)
        editor.Show(True)
    def set_value(self,value):
        self.value = value

class EmptyType():
    pass

class Bool3():
    def __init__(self,state=wx.CHK_UNDETERMINED):
        self.state = state

class DynaLoad():
    def __init__(self,dictionary={}):
        self.dict = dictionary
    def convert_to_text(self):
        levelloads = ""
        for i,v in self.dict.items():
            levelloads += i
            levelloads += ".p3d"
            if v:
                levelloads += ";"
            else:
                levelloads += ":"
        return levelloads

class DynaLoadEditor(scrolled.ScrolledPanel):
    def __init__(self,parent,dynaload=DynaLoad()):
        super().__init__(parent)
        self.bs = wx.BoxSizer(wx.VERTICAL)
        self.addnewinput = wx.TextCtrl(self,style=wx.TE_PROCESS_ENTER)
        self.addnewinput.SetHint("Enter level region name (like l1z1) and press enter")
        self.addnewinput.Bind(wx.EVT_TEXT_ENTER,self.add_new)
        #self.SetMinSize(wx.Size(300,16))
        self.SetSizer(self.bs)
        self.dynaload = dynaload
        self.checkboxes = []
        self.reload()
    def reload(self):
        for i in self.checkboxes:
            i.Destroy()
        self.checkboxes.clear()
        self.bs.Clear()
        for i,v in self.dynaload.dict.items():
            self.add_check(i,v)
        self.bs.Add(self.addnewinput,flag=wx.EXPAND)
        self.Layout()
        self.FitInside()
        self.Parent.FitInside()
    def add_check(self,i,v):
        control = wx.CheckBox(self,label=i)
        control.SetValue(v)
        control.Bind(wx.EVT_CHECKBOX,lambda eve: self.change_check(i,control.IsChecked()))
        self.bs.Add(control,flag=wx.EXPAND)
        self.checkboxes.append(control)
    def change_check(self,key,value):
        print(key,value)
        self.dynaload.dict[key] = value
    def add_new(self,eve):
        toadd = self.addnewinput.GetValue().lower()
        self.dynaload.dict[toadd] = True
        self.addnewinput.SetValue("")
        self.reload()


class EditorPanel(scrolled.ScrolledPanel):
    def __init__(self,parent):
        super().__init__(parent)
        self.bs = wx.BoxSizer(wx.VERTICAL)
        self.fgs = wx.FlexGridSizer(2,8,8)
        self.addedproperties = []
        self.fgs.AddGrowableCol(1,1)
        self.bs.Add(self.fgs,proportion=0,flag=wx.ALL | wx.EXPAND,border=8)
        self.SetSizer(self.bs)
        self.SetupScrolling()
        self.SetAutoLayout(1)
        self.stage = None
        self.moreinfo = {}
        self.loadstage(None)
    def add_special_property(self,title,control):
        thetext = wx.StaticText(self,label=title)
        self.bs.Add(thetext)
        self.bs.Add(control,proportion=0,flag=wx.ALL,border=8)
        self.addedproperties.append(thetext)
        self.addedproperties.append(control)
    def clearproperties(self):
        for i in self.addedproperties:
            i.Destroy()
        self.moreinfo = {}
        self.dictproperties = {}
        self.addedproperties.clear()
        self.fgs.Clear()
    def adjustlayout(self):
        self.FitInside()
    def addproperty(self,i,v):
        stageattr = getattr(self.stage,v)
        attrtype = type(stageattr)
        textshow = self.displaynames[i]
        if v in self.tooltips.keys():
            textshow += " (?)"
        if attrtype != EmptyType:
            textshow += ":"
        thetext = wx.StaticText(self,label=textshow,pos=(0,8))
        if v in self.tooltips.keys():
            thetext.SetToolTip(self.tooltips[v])
        self.addedproperties.append(thetext)
        self.fgs.Add(thetext,border=2,flag=wx.TOP)
        control = None
        if attrtype == str:
            control = wx.TextCtrl(self)
            control.SetValue(stageattr)
            self.fgs.Add(control,0,wx.EXPAND)
            control.Bind(wx.EVT_TEXT,lambda eve: setattr(self.stage,v,control.GetValue()))
        elif attrtype == int:
            min1 = -1
            max1 = 99999999
            if v in self.moreinfo:
                min1 = self.moreinfo[v].get("min",min1)
                max1 = self.moreinfo[v].get("max",max1)
            control = wx.SpinCtrl(self,min=min1,max=max1)
            control.SetValue(stageattr)
            control.Bind(wx.EVT_TEXT,lambda eve: setattr(self.stage,v,control.GetValue()))
            self.fgs.Add(control)
        elif attrtype == float:
            control = wx.SpinCtrlDouble(self,max=99999999,inc=0.01)
            control.SetValue(stageattr)
            control.Bind(wx.EVT_TEXT,lambda eve: setattr(self.stage,v,control.GetValue()))
            self.fgs.Add(control)
        elif attrtype == bool:
            control = wx.CheckBox(self)
            control.SetValue(stageattr)
            control.Bind(wx.EVT_CHECKBOX,lambda eve: setattr(self.stage,v,control.GetValue()))
            self.fgs.Add(control)
        elif attrtype == FreeSelectionList:
            control = wx.TextCtrl(self)
            control.SetValue(stageattr.value)
            control.Bind(wx.EVT_TEXT,lambda eve: stageattr.set_value(control.GetValue()))
            self.fgs.Add(control,0,wx.EXPAND)
            control.AutoComplete(MyClassCompleterSimple(stageattr.thelist))
        elif attrtype == StrictSelectionList:
            control = wx.Choice(self,choices=stageattr.thelist)
            control.SetSelection(stageattr.thelist.index(stageattr.value))
            control.Bind(wx.EVT_CHOICE,lambda eve: (
                stageattr.set_value(stageattr.thelist[control.GetSelection()]),
                self.onchange(v)
            ))
            self.fgs.Add(control,0,wx.EXPAND)
        elif attrtype == DynaLoad:
            control = DynaLoadEditor(self,stageattr)
            self.fgs.Add(control,1,wx.EXPAND | wx.ALL)
        elif attrtype == EmptyType:
            control = wx.StaticText(self)
            control.SetLabelText(textshow)
            thetext.SetLabelText("")
            font = wx.Font(12,wx.FONTFAMILY_DEFAULT,wx.FONTSTYLE_NORMAL,wx.FONTWEIGHT_BOLD)
            control.SetFont(font)
            self.fgs.Add(control)
        elif attrtype == ConversationValue:
            control = wx.Button(self,label=stageattr.value)
            control.Bind(wx.EVT_BUTTON,lambda eve: (stageattr.show_editor(control)))
            self.fgs.Add(control,0,wx.EXPAND)
        elif attrtype == LocationList:
            control = wx.Button(self,label="Open editor")
            control.Bind(wx.EVT_BUTTON,lambda eve: (stageattr.show_editor(control)))
            self.fgs.Add(control,0,wx.EXPAND)
        else:
            print("invalid type " + attrtype.__name__)
        self.addedproperties.append(control)
        self.dictproperties[i] = control
    def onchange(self,i):
        pass
    def update_layout(self):
        self.Layout()
        self.FitInside()

class MissionEditorPanel(EditorPanel):
    def __init__(self,parent):
        super().__init__(parent)
    def loadstage(self,stage):
        self.stage = stage
        self.clearproperties()
        if stage == None:
            self.update_layout()
            return
        self.properties = ["title","info","level","mission","sundaydrive","restartincar","carlocation","playerlocation"]
        self.displaynames = ["Title","Description","Level","Mission","Sunday Drive","Restart in car","Car location","Player location"]
        self.tooltips = {"sundaydrive":"The mission before the actual mission starts (requiring to talk to a character, etc...)","playerlocation":"Not used when \"Start in car\" is checked."}
        if self.stage.sundaydrive:
            self.properties.pop(0)
            self.properties.pop(0)
            self.displaynames.pop(0)
            self.displaynames.pop(0)
        for i,v in enumerate(self.properties):
            self.addproperty(i,v)
        self.add_special_property("Regions to load",DynaLoadEditor(self,self.stage.dynaload))
        self.update_layout()

class StageEditorPanel(EditorPanel):
    def __init__(self,parent):
        super().__init__(parent)
    def load_objective(self):
        objectivetype = self.stage.objectivetype.value
        self.properties.append("objectivetitle")
        self.displaynames.append("Objective - " + objectivetype)
        self.properties.append("objectivetype")
        self.displaynames.append("Objective Type")
        if objectivetype == "collectcoins":
            self.properties.append("o_coins")
            self.displaynames.append("Coins to collect")
        elif objectivetype == "timer":
            self.properties.append("o_durationtime")
            self.displaynames.append("Duration")
            self.tooltips["o_durationtime"] = "How long the game will wait at this stage"
        elif objectivetype == "talkto":
            self.properties.extend(["o_addnpc_name","o_addnpc_location","o_talkto_icon","o_talkto_yoffset"])
            self.displaynames.extend(["NPC Name","NPC Location","Icon","Y Offset"])
        elif objectivetype == "dialogue":
            self.properties.extend(["o_dialogue_pc","o_dialogue_npc","o_dialogue_conversation","o_dialogue_startwith"])
            self.displaynames.extend(["PC","NPC","Conversation","Start with"])
        elif objectivetype == "getin":
            self.properties.extend(["o_getin_vehicle","o_getin_location"])
            self.displaynames.extend(["Vehicle","Location"])
            self.tooltips["o_getin_vehicle"] = "If no vehicle is specified, all vehicles can be used for this objective. If it's used, the vehicle will be spawned at \"Location\" (one below this property) and only this vehicle can be used to succeed this objective (strict)"
            self.tooltips["o_getin_location"] = "Vehicle location: Is only used when you set strict vehicle."
        elif objectivetype == "goto":
            self.properties.extend(["o_waypoints","o_object","o_collectsound"])
            self.displaynames.extend(["Location","Object","Collect sound"])
            self.tooltips["o_waypoints"] = "Only the first waypoint in the list will be used."

        if objectivetype in objectivetypes_vehicles:
            self.properties.extend(["o_targetvehicle","o_waypoints","o_israce","o_followdistance"])
            self.displaynames.extend(["Vehicle","Waypoints","Is Race","Follow distance"])
            self.tooltips["o_followdistance"] = "A follow distance of 0 means no follow distance. The unit used is probably meters."
        
        if objectivetype == "losetail":
            self.properties.extend(["o_distance"])
            self.displaynames.extend(["Lose distance"])
        if objectivetype in ["dump","delivery"]:
            if objectivetype == "delivery":
                self.properties.append("o_locations")
                self.displaynames.append("Locations")
            elif objectivetype == "dump":
                self.moreinfo["o_collectamount"] = {"min":1,"max":30}
                self.properties.append("o_collectamount")
                self.displaynames.append("Amount")
            self.properties.extend(["o_object","o_collectsound"])
            self.displaynames.extend(["Object","Collect sound"])
            if objectivetype == "dump":
                self.tooltips["o_locations"] = "You don't need to put in actual positions in it, only the amount of locations."
    def loadstage(self,stage):
        self.stage = stage
        self.clearproperties()
        if stage == None:
            self.update_layout()
            return
        self.properties = ["customname","resettohere","timer","timertimeout","keeptimer","message","hudicon","stagecomplete",
                           "conditionstitle",
                           "c_conditioncoins",
                           "c_maxwrenches"
                           ]
        self.displaynames = ["Name","Reset to here","Timer","Timeout","Keep Timer","HUD Message","HUD Icon","TASK COMPLETE",
                             "Conditions",
                             "Coins allowed",
                             "Wrenches allowed"
                             ]
        self.tooltips = {
            "customname":"This name is only for the editor",
            "resettohere":"When going to the menu and selecting \"Restart Mission\", it will start at this stage when checked.",
            "timertimeout":"When the timer reaches 0, the player will lose the mission. (can be used for \"Timer\" and \"Keep Timer\")",
            "stagecomplete":"Show the \"TASK COMPLETE!\" message when completing this stage.",
            "keeptimer":"Keep the timer from the previous stage. Check \"Timeout\" even when keeping the timer.",
            "c_conditioncoins":"Max coins allowed to collect",
            "c_maxwrenches":"Max wrenches allowed to collect"
        }
        self.load_objective()
        for i,v in enumerate(self.properties):
            self.addproperty(i,v)
        self.update_layout()
    def onchange(self,i):
        if i == "objectivetype":
            self.loadstage(self.stage)

class Stage():
    def __init__(self):
        self.customname = "Unnamed Stage"
        self.timer = 0
        self.timertimeout = True
        self.keeptimer = False
        self.resettohere = False
        self.stagecomplete = False
        self.message = ""
        self.objectivetitle = EmptyType()
        self.conditionstitle = EmptyType()
        self.hudicon = FreeSelectionList(list(hudiconmapping.keys()))
        self.objectivetype = StrictSelectionList(load_data_json("objectivetypes.json"),"dummy")
        self.o_coins = 1
        self.o_durationtime = 1
        self.o_addnpc_name = FreeSelectionList(charnames,"marge")
        self.o_addnpc_location = FreeSelectionList(defaultlocator3names,"m1_marge_sd")
        self.o_talkto_icon = StrictSelectionList(["Exclamation","Gift","Door"],"Exclamation")
        self.o_talkto_yoffset = 0.2
        self.o_dialogue_pc = FreeSelectionList(charnames,"homer")
        self.o_dialogue_npc = FreeSelectionList(charnames,"marge")
        self.o_dialogue_conversation = ConversationValue()
        self.o_dialogue_startwith = StrictSelectionList(["NPC","PC"],"NPC")
        self.o_getin_vehicle = FreeSelectionList(vehiclelist,"")
        self.o_getin_location = FreeSelectionList(defaultlocator3names,"level1_carstart")
        self.o_targetvehicle = FreeSelectionList(vehiclelist,"")
        self.o_waypoints = LocationList(0)
        self.o_locations = LocationList(0)
        self.o_israce = False
        self.o_followdistance = 0
        self.o_distance = 0
        self.o_object = FreeSelectionList(list(objectlist.keys()),"carsphere")
        self.o_collectsound = FreeSelectionList(soundlist,"wrench_collect")
        self.o_collectamount = 1
        self.c_conditioncoins = 0
        self.c_maxwrenches = 0

class Mission():
    def __init__(self,levelnumber,missionnumber,sundaydrive=False):
        self.level = levelnumber
        self.mission = missionnumber
        self.sundaydrive = sundaydrive
        self.stages = []
        self.dynaload = DynaLoad({"l1z1":True,"l1r1":True,"l1r7":True})
        self.title = ""
        self.info = ""
        self.restartincar = False
        
        self.carlocation = FreeSelectionList(defaultlocator3names)
        self.playerlocation = FreeSelectionList(defaultlocator3names)
        self.carlocation.value = "level" + str(levelnumber) + "_carstart"
        playerstartmapping = ["level1_homer_start","level2_bartstart","level3_lisa_start","L4_marge_sd","level5_apu_start","level6_bart_start"]
        if levelnumber >= 1 and levelnumber <= 6:
            self.playerlocation.value = playerstartmapping[levelnumber - 1]
    def get_display_name(self):
        name = "L" + str(self.level) + "M" + str(self.mission)
        if self.sundaydrive:
            name += " Before"
        return name
    def get_lm(self,underscored=False):
        part1 = "L" + str(self.level)
        if underscored:
            part1 += "_"
        return part1 + "M" + str(self.mission)
    def get_smallname(self,evenshort=False):
        smallname = "m" + str(self.mission)
        if not evenshort:
            if self.sundaydrive:
                smallname += "sd"
        return smallname
    def get_sort_text(self):
        name = "L" + str(self.level) + "M" + str(self.mission)
        if self.sundaydrive:
            name += " a"
        else:
            name += " b"
        return name

class SaveData():
    def __init__(self):
        self.missions = []
        self.modpath = ""
    def load(self,filename):
        js = {}
        with open(filename) as f:
            js = json.loads(f.read())
        ver = js["version"]
        self.modpath = js["modpath"]
        self.missions.clear()
        for i in js["missions"]:
            mission = Mission(i["level"],i["mission"],i["sundaydrive"])
            mission.title = i["title"]
            mission.info = i["info"]
            mission.dynaload = DynaLoad(i["dynaload"])
            mission.restartincar = i["restartincar"]
            mission.carlocation.value = i["carlocation"]
            mission.playerlocation.value = i["playerlocation"]
            mission.carlocation.value = i["carlocation"]
            for j in i["stages"]:
                stage = Stage()
                stage.customname = j["customname"]
                stage.timer = j["timer"]
                stage.timertimeout = j["timertimeout"]
                stage.keeptimer = j["keeptimer"]
                stage.resettohere = j["resettohere"]
                stage.stagecomplete = j["stagecomplete"]
                stage.message = j["message"]
                stage.hudicon.value = j["hudicon"]
                stage.objectivetype.value = j["objectivetype"]
                stage.o_coins = j["o_coins"]
                stage.o_durationtime = j["o_durationtime"]
                if ver >= 2:
                    stage.o_addnpc_name.value = j["o_addnpc_name"]
                    stage.o_addnpc_location.value = j["o_addnpc_location"]
                    stage.o_talkto_icon.value = j["o_talkto_icon"]
                    stage.o_talkto_yoffset = j["o_talkto_yoffset"]
                if ver >= 3:
                    stage.o_dialogue_conversation.value = j["o_dialogue_conversation"]
                    stage.o_dialogue_npc.value = j["o_dialogue_npc"]
                    stage.o_dialogue_pc.value = j["o_dialogue_pc"]
                    stage.o_dialogue_startwith.value = j["o_dialogue_startwith"]
                if ver >= 4:
                    stage.o_getin_vehicle.value = j["o_getin_vehicle"]
                    stage.o_getin_location.value = j["o_getin_location"]
                if ver >= 5:
                    stage.o_targetvehicle.value = j["o_targetvehicle"]
                    stage.o_waypoints.thelist = j["o_waypoints"]
                if ver >= 6:
                    stage.o_israce = j["o_israce"]
                    stage.o_followdistance = j["o_followdistance"]
                    stage.o_distance = j.get("o_distance",0)
                if ver >= 7:
                    stage.o_object.value = j.get("o_object")
                if ver >= 8:
                    stage.o_collectsound.value = j.get("o_collectsound")
                if ver >= 9:
                    stage.o_locations.thelist = j.get("o_locations")
                if ver >= 10:
                    stage.o_collectamount = j.get("o_collectamount")
                if ver >= 11:
                    stage.c_conditioncoins = j.get("c_conditioncoins")
                    stage.c_maxwrenches = j.get("c_maxwrenches")
                mission.stages.append(stage)
            self.missions.append(mission)
        print("Loaded")
    def save(self,filename):
        js = {}
        js["version"] = 11
        js["modpath"] = self.modpath
        js["missions"] = []
        for mission in self.missions:
            jsmission = {}
            jsmission["level"] = mission.level
            jsmission["mission"] = mission.mission
            jsmission["sundaydrive"] = mission.sundaydrive
            jsmission["title"] = mission.title
            jsmission["info"] = mission.info
            jsmission["dynaload"] = mission.dynaload.dict
            jsmission["restartincar"] = mission.restartincar
            jsmission["carlocation"] = mission.carlocation.value
            jsmission["playerlocation"] = mission.playerlocation.value
            jsmission["stages"] = []
            for stage in mission.stages:
                jsstage = {}
                jsstage["customname"] = stage.customname
                jsstage["timer"] = stage.timer
                jsstage["timertimeout"] = stage.timertimeout
                jsstage["keeptimer"] = stage.keeptimer
                jsstage["resettohere"] = stage.resettohere
                jsstage["stagecomplete"] = stage.stagecomplete
                jsstage["message"] = stage.message
                jsstage["hudicon"] = stage.hudicon.value
                jsstage["objectivetype"] = stage.objectivetype.value
                jsstage["o_coins"] = stage.o_coins
                jsstage["o_durationtime"] = stage.o_durationtime
                jsstage["o_addnpc_name"] = stage.o_addnpc_name.value
                jsstage["o_addnpc_location"] = stage.o_addnpc_location.value
                jsstage["o_talkto_icon"] = stage.o_talkto_icon.value
                jsstage["o_talkto_yoffset"] = stage.o_talkto_yoffset
                jsstage["o_dialogue_conversation"] = stage.o_dialogue_conversation.value
                jsstage["o_dialogue_npc"] = stage.o_dialogue_npc.value
                jsstage["o_dialogue_pc"] = stage.o_dialogue_pc.value
                jsstage["o_dialogue_startwith"] = stage.o_dialogue_startwith.value
                jsstage["o_getin_vehicle"] = stage.o_getin_vehicle.value
                jsstage["o_getin_location"] = stage.o_getin_location.value
                jsstage["o_targetvehicle"] = stage.o_targetvehicle.value
                jsstage["o_waypoints"] = stage.o_waypoints.thelist
                jsstage["o_israce"] = stage.o_israce
                jsstage["o_followdistance"] = stage.o_followdistance
                jsstage["o_distance"] = stage.o_distance
                jsstage["o_object"] = stage.o_object.value
                jsstage["o_collectsound"] = stage.o_collectsound.value
                jsstage["o_locations"] = stage.o_locations.thelist
                jsstage["o_collectamount"] = stage.o_collectamount
                jsstage["c_conditioncoins"] = stage.c_conditioncoins
                jsstage["c_maxwrenches"] = stage.c_maxwrenches
                jsmission["stages"].append(jsstage)
            js["missions"].append(jsmission)
        jsstr = json.dumps(js)
        with open(filename,"w+") as f:
            f.write(jsstr)
        print("Saved")


class Exporter():
    def __init__(self,mw):
        self.save = mw.save
        self.mw = mw
        self.p3dcount = 0
    def create_locator0(self,waypoint):
        x = waypoint["x"]
        y = waypoint["y"]
        z = waypoint["z"]
        self.p3dcount += 1
        thename = "locator" + str(self.p3dcount) + "_0t"
        with open("data/pure3d_templates/locator0.p3d","rb") as f:
            t = list(f.read())

        thename += "0" * (16 - len(thename))

        for i in range(len(thename)):
            t[0x19 + i] = ord(thename[i])
        
        thename2 = thename + "Trigger"
        for i in range(len(thename2)):
            t[0x56 + i] = ord(thename2[i])

        towrite = []
        towrite.extend(struct.pack("f",x))
        towrite.extend(struct.pack("f",y))
        towrite.extend(struct.pack("f",z))

        for i,v in enumerate(towrite):
            t[0x39 + i] = v
            t[0xAE + i] = v

        createfolder(self.save.modpath,"CustomFiles/art/custom/locators")
        files_path = "art/custom/locators/" + thename + ".p3d"
        with open(modpath(self.save.modpath,"CustomFiles/" + files_path),"wb+") as f:
            f.write(bytes(t))
        return thename,files_path
    def create_locator3(self,waypoint):
        x = waypoint["x"]
        y = waypoint["y"]
        z = waypoint["z"]
        rot = waypoint.get("rot",0.0)
        self.p3dcount += 1
        thename = "locator" + str(self.p3dcount) + "_3t"
        with open("data/pure3d_templates/locator3.p3d","rb") as f:
            t = list(f.read())

        thename += "0" * (16 - len(thename))

        for i in range(16):
            t[0x19 + i] = ord(thename[i])

        towrite = []
        towrite.extend(struct.pack("f",(rot / 180.0) * math.pi))
        towrite.extend(struct.pack("f",x))
        towrite.extend(struct.pack("f",y))
        towrite.extend(struct.pack("f",z))

        for i,v in enumerate(towrite):
            t[0x31 + i] = v

        createfolder(self.save.modpath,"CustomFiles/art/custom/locators")
        files_path = "art/custom/locators/" + thename + ".p3d"
        with open(modpath(self.save.modpath,"CustomFiles/" + files_path),"wb+") as f:
            f.write(bytes(t))
        return thename,files_path
    def pad_nicely(self,lines):
        result = ""
        tabs = 0
        for i_ in lines:
            for i in i_:
                if type(i) != str and type(i) != int and type(i) != float:
                    raise Exception("Wrong type for function: " + str(i_))
            i = str(i_[0]) + "("
            args = ['"%s"' % str(j) for j in i_[1:]]
            i += ",".join(args)
            i += ");"
            if i.startswith("Close"):
                tabs -= 1
                if tabs < 0:
                    tabs = 0
            result += ((tabs * 4) * " ") + i + "\r\n"
            if i.startswith("AddObjective") or i.startswith("AddStage(") or i.startswith("AddCondition"):
                tabs += 1
        return result
    def add_customtext(self,header,key,value):
        if not self.customtext.has_section(header):
            self.customtext.add_section(header)
        self.customtext.set(header,key,value)
    def add_customleveltext(self,text,missionsn2):
        nownumber = self.levelscustomtext.get(missionsn2,0) + 1
        self.levelscustomtext[missionsn2] = nownumber
        self.add_customtext("CustomText" + missionsn2,"MISSION_OBJECTIVE_" + addzero(nownumber),text)
        return nownumber
    def export_error(self,message):
        return wx.MessageBox(message,"Error",style=wx.OK | wx.CENTER | wx.ICON_ERROR,parent=mw)
    def export(self):
        missionsfolder = "CustomFiles/scripts/missions"
        createfolder(self.save.modpath,missionsfolder)
        with open(modpath(self.save.modpath,"Meta.ini")) as f:
            self.metaini = f.read().splitlines()
            self.beforemetaini = list(self.metaini)

        # CustomFiles for the custom missions
        # CustomText for the mission title and description and stage text
        # OggVorbisSupport for the custom voicelines
        requiredhacks = ["CustomFiles","CustomText","OggVorbisSupport","AdditionalScriptFunctionality"]

        for i in requiredhacks:
            shouldadd = True
            line = "RequiredHack=" + str(i)
            for j in self.metaini:
                if line == j.replace(" ",""):
                    shouldadd = False
            if shouldadd:
                self.metaini.insert(self.metaini.index("[Miscellaneous]") + 1,line)
        
        self.customtext = configparser.ConfigParser()
        self.customtext.optionxform = str
        self.levelscustomtext = {}
        customtext_path = modpath(self.save.modpath,"CustomText.ini")
        if os.path.exists(customtext_path):
            with open(customtext_path) as f:
                self.customtext.read_string(f.read())
        self.add_customtext("Miscellaneous","Title","English")
        for mission in self.save.missions:
            linesi = [] # mission script
            linesl = [] # mission load script
            p3dfiles_toload = [] # LoadP3DFile in the mission load script
            cars_toload = {}
            lfname = get_level_folder(mission.level)
            missionsn = mission.get_smallname()
            missionsn2 = mission.get_lm(True)

            # make it easier for camera warps
            if mission.level == 1:
                for i in range(8): # mission0cam.p3d - mission7cam.p3d (except 3 and 5)
                    if i != 3 and i != 5:
                        p3dfiles_toload.append("art\\missions\\level"+addzero(mission.level)+"\\mission"+str(i)+"cam.p3d")
            elif mission.level in [2,3,6]: # levels 2, 3, 6
                for i in range(1,7): # mission1cam.p3d - mission6cam.p3d
                    p3dfiles_toload.append("art\\missions\\level"+addzero(mission.level)+"\\mission"+str(i)+"cam.p3d")
            elif mission.level == 4:
                for i in range(2,8): # mission2cam.p3d - mission7cam.p3d
                    p3dfiles_toload.append("art\\missions\\level"+addzero(mission.level)+"\\mission"+str(i)+"cam.p3d")
            elif mission.level == 5:
                for i in [1,2,3,5,7]: # missionXcam.p3d (1,2,3,5,7)
                    p3dfiles_toload.append("art\\missions\\level"+addzero(mission.level)+"\\mission"+str(i)+"cam.p3d")
            elif mission.level == 7:
                for i in [2,3,5]: # missionXcam.p3d (2,3,5)
                    p3dfiles_toload.append("art\\missions\\level"+addzero(mission.level)+"\\mission"+str(i)+"cam.p3d")
            
            if not mission.sundaydrive:
                self.add_customtext("CustomText","MISSION_TITLE_" + missionsn2,mission.title)
                self.add_customtext("CustomText","MISSION_INFO_" + missionsn2,mission.info)

            linesi.append(["SelectMission",missionsn])
            p3dfiles_toload.append("art\\missions\\"+get_level_folder(mission.level)+"\\"+mission.get_smallname(True)+".p3d")
            
            init_vehicles = []
            for i in mission.stages:
                if i.objectivetype.value == "getin":
                    veh = i.o_getin_vehicle.value
                    if veh != "":
                        if veh not in init_vehicles:
                            init_vehicles.append(veh)
                            linesi.append(["InitLevelPlayerVehicle",veh,i.o_getin_location.value,"OTHER"])
                            cars_toload[veh] = "OTHER"

            if mission.restartincar:
                linesi.append(["SetMissionResetPlayerInCar",mission.carlocation.value])
            else:
                linesi.append(["SetMissionResetPlayerOutCar",mission.playerlocation.value,mission.carlocation.value])

            dynaloaddata = mission.dynaload.convert_to_text()
            if dynaloaddata != "":
                linesi.append(["SetDynaLoadData",dynaloaddata])

            for i,stage in enumerate(mission.stages):
                linesi.append(["AddStage"])
                if stage.resettohere:
                    linesi.append(["RESET_TO_HERE"])
                
                hudicon = stage.hudicon.value
                if hudicon != "":
                    iconfolder = ""
                    if hudicon in hudiconmapping:
                        iconfolder = hudiconmapping[hudicon]
                    else:
                        iconfolder = "custom"
                    p3dfiles_toload.append("art\\frontend\\dynaload\\images\\msnicons\\" + iconfolder + "\\"+hudicon+".p3d")
                    linesi.append(["SetHUDIcon",hudicon])
                if stage.message != "":
                    message_index = self.add_customleveltext(stage.message,missionsn2.replace("_",""))
                    linesi.append(["SetStageMessageIndex",addzero(message_index)])
                if stage.timer > 0:
                    linesi.append(["SetStageTime",stage.timer])
                if stage.keeptimer:
                    linesi.append(["AddStageTime",0])
                if stage.timertimeout and (stage.timer > 0 or stage.keeptimer):
                    linesi.append(["AddCondition","timeout"])
                    linesi.append(["CloseCondition"])
                objectivetype = stage.objectivetype.value
                extra_addobjective = []
                if objectivetype == "getin":
                    if stage.o_getin_vehicle.value != "":
                        extra_addobjective.append(stage.o_getin_vehicle.value)
                allwaypointnames = []
                if objectivetype in objectivetypes_vehicles:
                    startwaypoint = stage.o_waypoints.thelist[0]
                    name,path = self.create_locator3(startwaypoint)
                    cars_toload[stage.o_targetvehicle.value] = "AI"
                    linesi.append(["AddStageVehicle",stage.o_targetvehicle.value,name,objectivetype_vehiclebehaviours.get(objectivetype,"target")])
                    p3dfiles_toload.append(path)
                    for i,v in enumerate(stage.o_waypoints.thelist[1:]):
                        name,path = self.create_locator0(v)
                        allwaypointnames.append(name)
                        linesi.append(["AddStageWaypoint",name])
                        p3dfiles_toload.append(path)
                linesi.append(["AddObjective",objectivetype] + extra_addobjective)
                if objectivetype == "collectcoins":
                    linesi.append(["SetObjTotal",stage.o_coins])
                elif objectivetype == "timer":
                    linesi.append(["SetDurationTime",stage.o_durationtime])
                elif objectivetype == "talkto":
                    linesi.append(["AddNPC",stage.o_addnpc_name.value,stage.o_addnpc_location.value])
                    linesi.append(["SetTalkToTarget",stage.o_addnpc_name.value,stage.o_talkto_icon.thelist.index(stage.o_talkto_icon.value),stage.o_talkto_yoffset])
                elif objectivetype == "dialogue":
                    convname = stage.o_dialogue_conversation.value
                    npcname = stage.o_dialogue_npc.value
                    pcname = stage.o_dialogue_pc.value
                    spt_start = pcname
                    spt_second = npcname
                    startwithnpc = stage.o_dialogue_startwith.value == "NPC"
                    if startwithnpc:
                        spt_start,spt_second = (spt_second,spt_start)
                    with open(modpath(mw.save.modpath,"CustomFiles/sound/scripts/dialog.spt"),"r") as f:
                        dialogspt = f.read()
                        if "C_" + convname + "_1_convinit" not in dialogspt:
                            return self.export_error("Conversation " + convname + " does not exist in the dialog script (dialog.spt)")
                        if "C_" + convname + "_1_convinit_" + dialoguecodes[spt_start] not in dialogspt:
                            return self.export_error("Conversation " + convname + " has an error, please try converting the voicelines again.")
                    linesi.append(["SetDialogueInfo",pcname,npcname,convname,0]) # last number is the "pause", but the number is never used
                elif objectivetype == "getin":
                    linesi.append(["SetObjTargetVehicle","current"]) # does nothing
                elif objectivetype == "race":
                    p3dfiles_toload.append("art\\missions\\generic\\fline.p3d")
                    for i,v in enumerate(allwaypointnames):
                        #if i == len(allwaypointnames) - 1:
                        linesi.append(["AddCollectible",v,"carsphere"])
                        #else:
                        #    linesi.append(["AddCollectible",v])
                elif objectivetype == "goto":
                    setdest = ["SetDestination"]
                    if len(stage.o_waypoints.thelist) == 0:
                        return self.export_error("A goto objective has no location set.")
                    lname, lpath = self.create_locator0(stage.o_waypoints.thelist[0])
                    p3dfiles_toload.append(lpath)
                    setdest.append(lname)
                    obj = stage.o_object.value
                    if obj != "":
                        setdest.append(obj)
                        obj_p3d = objectlist[obj]
                        if obj_p3d != "":
                            p3dfiles_toload.append(obj_p3d)
                    linesi.append(setdest)
                    if stage.o_collectsound.value != "":
                        linesi.append(["SetCollectibleEffect",stage.o_collectsound.value])
                if objectivetype == "destroy" or objectivetype == "follow" or objectivetype == "losetail" or objectivetype == "dump":
                    linesi.append(["SetObjTargetVehicle",stage.o_targetvehicle.value])
                if objectivetype == "delivery" or objectivetype == "dump":
                    p3dfiles_toload.append(objectlist[stage.o_object.value])
                    if objectivetype == "delivery":
                        for i in stage.o_locations.thelist:
                            name,path = self.create_locator0(i)
                            p3dfiles_toload.append(path)
                            linesi.append(["AddCollectible",name,stage.o_object.value])
                    elif objectivetype == "dump":
                        for i in range(stage.o_collectamount):
                            name,path = self.create_locator0({"x":0,"y":0,"z":0})
                            p3dfiles_toload.append(path)
                            linesi.append(["AddCollectible",name,stage.o_object.value])
                    if stage.o_collectsound.value != "":
                        linesi.append(["SetCollectibleEffect",stage.o_collectsound.value])
                if objectivetype == "losetail":
                    linesi.append(["SetObjDistance",stage.o_distance])
                linesi.append(["CloseObjective"])
                if objectivetype in objectivetypes_vehicles:
                    if stage.o_israce:
                        linesi.append(["AddCondition","race"]) # to make you probably lose or something
                        linesi.append(["SetCondTargetVehicle",stage.o_targetvehicle.value])
                        linesi.append(["CloseCondition"])
                    if stage.o_followdistance > 0:
                        linesi.append(["AddCondition","followdistance"])
                        linesi.append(["SetFollowDistances",0,stage.o_followdistance])
                        linesi.append(["SetCondTargetVehicle",stage.o_targetvehicle.value])
                        linesi.append(["CloseCondition"])
                if stage.stagecomplete:
                    linesi.append(["ShowStageComplete"])
                if stage.c_conditioncoins > 0:
                    linesi.append(["AddCondition","collectcoins"])
                    linesi.append(["SetCondTotal",stage.c_conditioncoins])
                    linesi.append(["CloseCondition"])
                if stage.c_maxwrenches > 0:
                    linesi.append(["AddCondition","collectwrench"])
                    linesi.append(["SetCondTotal",stage.c_maxwrenches])
                    linesi.append(["CloseCondition"])
                linesi.append(["CloseStage"])
            if not mission.sundaydrive:
                linesi.append(["AddStage","final"])
                linesi.append(["AddObjective","timer"])
                linesi.append(["SetDurationTime","0.2"])
                linesi.append(["CloseObjective"])
                linesi.append(["CloseStage"])
            linesi.append(["CloseMission"])

            for i,v in cars_toload.items():
                linesl.append(["LoadDisposableCar","art\\cars\\" + i + ".p3d",i,v])
            p3dloaded = []
            for i in p3dfiles_toload:
                if i in p3dloaded:
                    continue
                p3dloaded.append(i)
                linesl.append(["LoadP3DFile",i])


            scriptpath = missionsfolder + "/" + lfname + "/" + missionsn

            write_to_file(modpath(self.save.modpath,scriptpath + "i.mfk"),self.pad_nicely(linesi))
            write_to_file(modpath(self.save.modpath,scriptpath + "l.mfk"),self.pad_nicely(linesl))
        with open(customtext_path,"w+") as f:
            self.customtext.write(f)
        if str(self.metaini) != str(self.beforemetaini):
            print("Meta.ini changed")
            write_to_file(modpath(self.save.modpath,"Meta.ini"),"\r\n".join(self.metaini))
        else:
            print("Meta.ini didn't change")
        print("Exported")

class MainWindow(wx.Frame):
    def __init__(self):
        super().__init__(None,title="SHAR Mission Creator",size=(1000,850))
        
        self.save = SaveData()
        self.save.modpath = ""
        self.savefilename = None

        statusbar = self.CreateStatusBar(style=wx.BORDER_NONE)
        statusbar.SetStatusText("Made by @chocolateimage | v" + program_version)

        menubar = wx.MenuBar()

        menufile = wx.Menu()
        menu_new = menufile.Append(wx.ID_NEW,"New")
        menu_open = menufile.Append(wx.ID_OPEN,"Open...")
        menu_save = menufile.Append(wx.ID_SAVE,"Save")
        menu_saveas = menufile.Append(wx.ID_SAVEAS,"Save as...")
        menu_export = menufile.Append(wx.NewIdRef(),"Export")
        menubar.Append(menufile,"File")

        menuedit = wx.Menu()
        menu_selectmodpath = menuedit.Append(wx.NewIdRef(),"Select modpath")
        menu_addmission = menuedit.Append(wx.NewIdRef(),"Add Mission")
        menu_addstage = menuedit.Append(wx.NewIdRef(),"Add Stage")
        menu_reload = menuedit.Append(wx.ID_REFRESH,"Reload")
        menubar.Append(menuedit,"Edit")

        menuhelp = wx.Menu()
        menu_about = menuhelp.Append(wx.NewIdRef(),"About")
        menubar.Append(menuhelp,"Help")

        self.SetMenuBar(menubar)
        self.Bind(wx.EVT_MENU,self.menu_new,menu_new)
        self.Bind(wx.EVT_MENU,self.menu_open,menu_open)
        self.Bind(wx.EVT_MENU,self.menu_save,menu_save)
        self.Bind(wx.EVT_MENU,self.menu_saveas,menu_saveas)
        self.Bind(wx.EVT_MENU,self.menu_selectmodpath,menu_selectmodpath)
        self.Bind(wx.EVT_MENU,self.menu_addmission,menu_addmission)
        self.Bind(wx.EVT_MENU,self.menu_addstage,menu_addstage)
        self.Bind(wx.EVT_MENU,self.export,menu_export)
        self.Bind(wx.EVT_MENU,self.menu_reload,menu_reload)
        self.Bind(wx.EVT_MENU,self.menu_about,menu_about)

        toolbar = self.CreateToolBar(wx.TB_HORZ_TEXT)
        toolbar_addmission = toolbar.AddTool(wx.NewIdRef(),"Add Mission",wx.ArtProvider.GetBitmap(wx.ART_PLUS),wx.NullBitmap,longHelp="Adds a mission")
        toolbar_addstage = toolbar.AddTool(wx.NewIdRef(),"Add Stage",wx.ArtProvider.GetBitmap(wx.ART_PLUS),wx.NullBitmap,longHelp="Adds a stage to the selected mission on the very left list")
        toolbar_export = toolbar.AddTool(wx.NewIdRef(),"Export",wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE),wx.NullBitmap,longHelp="Exports to the selected mod path")
        toolbar.Realize()
        self.Bind(wx.EVT_MENU,self.menu_addmission,toolbar_addmission)
        self.Bind(wx.EVT_MENU,self.menu_addstage,toolbar_addstage)
        self.Bind(wx.EVT_MENU,self.export,toolbar_export)

        #self.mgr = wx.aui.AuiManager(self)

        self.splitter = wx.SplitterWindow(self)
        self.splitter_left = wx.SplitterWindow(self.splitter)

        self.pnl1 = wx.ListBox(self.splitter_left) # missions
        self.pnl2 = wx.ListBox(self.splitter_left) # stages
        self.pnl2.Bind(wx.EVT_RIGHT_DOWN,self.open_stage_contextmenu)
        self.splitter_right = wx.SplitterWindow(self.splitter) # stage
        self.pnl3 = StageEditorPanel(self.splitter_right)
        self.pnl4 = MissionEditorPanel(self.splitter_right)

        self.splitter_left.SplitVertically(self.pnl1,self.pnl2,200)
        self.splitter_left.Update()

        self.splitter_right.SplitHorizontally(self.pnl3,self.pnl4,370)
        self.splitter_right.Update()

        self.splitter.SplitVertically(self.splitter_left,self.splitter_right,450)

        self.splitter.Update()

        #self.mgr.AddPane(pnl1,wx.aui.AuiPaneInfo().Caption("Missions").Left())
        #self.mgr.AddPane(pnl2,wx.aui.AuiPaneInfo().Caption("Stages").())
        #self.mgr.AddPane(pnl3,wx.aui.AuiPaneInfo().Caption("Stage").Left())

        #self.mgr.Update()

        """for i in range(1,8):
            for j in range(7):
                if i == 1 or j != 0:
                    pnl1.Append("L" + str(i) + "M" + str(j) + " START")
                    pnl1.Append("L" + str(i) + "M" + str(j))"""

        self.pnl2.Bind(wx.EVT_LISTBOX,self.stage_change)
        self.pnl1.Bind(wx.EVT_LISTBOX,self.mission_change)

        self.Show(True)
    def menu_about(self,event):
        info = wx.adv.AboutDialogInfo()
        info.SetName("SHAR Mission Creator")
        info.SetVersion(program_version)
        info.SetDescription("Create missions with a GUI for The Simpsons Hit & Run")
        info.SetCopyright("2023 chocolateimage <chocolateimage@protonmail.com>")
        wx.adv.AboutBox(info)
    def open_stage_contextmenu(self,event):
        stage = self.get_curstage()
        if stage == None:
            return
        menu = wx.Menu()
        cm_up = wx.MenuItem(menu,id=wx.ID_UP)
        cm_down = wx.MenuItem(menu,id=wx.ID_DOWN)
        cm_delete = wx.MenuItem(menu,id=wx.ID_DELETE)
        menu.Append(cm_up)
        menu.Append(cm_down)
        menu.Append(cm_delete)
        menu.Bind(wx.EVT_MENU,self.cm_stage_moveup,cm_up)
        menu.Bind(wx.EVT_MENU,self.cm_stage_movedown,cm_down)
        menu.Bind(wx.EVT_MENU,self.cm_stage_delete,cm_delete)
        self.PopupMenu(menu)
        menu.Destroy()
    def cm_stage_moveup(self,event):
        self.cm_stage_move(-1)
    def cm_stage_movedown(self,event):
        self.cm_stage_move(1)
    def cm_stage_move(self,howmuch):
        mission = self.get_curmission()
        stage = self.get_curstage()
        if stage not in mission.stages:
            print("stage not in selected mission")
            return
        curstageindex = mission.stages.index(stage)
        if howmuch == -1 and curstageindex == 0:
            print("can't move stage further up")
            return
        if howmuch == 1 and curstageindex == len(mission.stages) - 1:
            print("can't move stage further down")
            return
        mission.stages.remove(stage)
        mission.stages.insert(curstageindex + howmuch,stage)
        self.reloadstuff(stages=True,stage=True)
    def cm_stage_delete(self,event):
        mission = self.get_curmission()
        stage = self.get_curstage()
        if stage not in mission.stages:
            print("stage not in selected mission")
            return
        if wx.MessageBox("Are you sure you want to delete the stage "+stage.customname+" in "+mission.get_display_name()+"?",style=wx.YES_NO,parent=self) != wx.YES:
            print("didn't click yes")
            return
        print("deleted stage")
        mission.stages.remove(stage)
        self.reloadstuff(stages=True,stage=True)

    def warn_unsaved(self):
        return wx.MessageBox("This will delete all unsaved changes, do you want to continue?",style=wx.YES_NO,parent=self) == wx.YES
    def menu_new(self,event):
        if not self.warn_unsaved():
            pass
        self.save = SaveData()
        self.reload_after_open()
    def menu_open(self,event):
        if not self.warn_unsaved():
            pass
        dlg = wx.FileDialog(self,"Open",wildcard=file_wildcard,style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.save = SaveData()
            self.save.load(path)
            self.savefilename = path
            self.reload_after_open()
    def menu_save(self,event):
        if self.savefilename == None:
            self.menu_saveas(event)
        else:
            self.save.save(self.savefilename)
    def menu_saveas(self,event):
        dlg = wx.FileDialog(self,"Save",wildcard=file_wildcard,style=wx.FD_SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            if not path.endswith(".smc"):
                path += ".smc"
            self.savefilename = path
            self.menu_save(event)
    def menu_reload(self,event):
        self.reloadstuff(True,True,True)
    def export(self,unused0=0):
        if self.save.modpath == "":
            return wx.MessageBox("You haven't selected your mod yet.\nGo to Edit->Select modpath")
        exporter = Exporter(self)
        exporter.export()
    def menu_selectmodpath(self,event):
        dlg = wx.DirDialog(self, "Choose the mod directory")
        result = dlg.ShowModal()
        if result == wx.ID_OK:
            modpath = dlg.GetPath()
            if not os.path.exists(modpath):
                return wx.MessageBox("Mod directory doesn't exist")
            metaini = False
            for i in os.listdir(modpath):
                if ".lmlm" in i:
                    return wx.MessageBox("Create a mod inside the \"Mods\" folder, then select that instead.")
                if i == "Meta.ini":
                    metaini = True
            if not metaini:
                return wx.MessageBox("You didn't create your mod fully (\"Meta.ini\" missing)")
            self.save.modpath = modpath
            
    def menu_addmission(self,event):
        name = ask(self,"Enter level and mission name (like L1M1)","L1M1")
        if name == None:
            return
        l,m = name.lower().split("m")
        l = int(l.replace("l",""))
        m = int(m)
        for i in self.save.missions:
            if i.level == l and i.mission == m:
                wx.MessageBox("A mission already exists with " + i.get_display_name())
                return
        self.save.missions.append(Mission(l,m,True))
        self.save.missions.append(Mission(l,m))
        self.reloadstuff(missions=True)
    def menu_addstage(self,event):
        if self.get_curmission() == None:
            return
        name = ask(self,"Enter stage name (not displayed in game)","Unnamed Stage")
        if name == None:
            return
        stage = Stage()
        stage.customname = name
        self.get_curmission().stages.append(stage)
        self.reloadstuff(stages=True,stage=True)
    def stage_change(self,event):
        self.reloadstuff(stage=True)
    def mission_change(self,event):
        self.reloadstuff(mission=True,stages=True,stage=True)
    def get_curmission(self):
        selectedindex = self.pnl1.Selection
        if selectedindex < 0:
            return None
        else:
            return self.save.missions[selectedindex]
    def get_curstage(self):
        selectedindex = self.pnl2.Selection
        if selectedindex < 0:
            return None
        else:
            curmis = self.get_curmission()
            if curmis == None:
                return None
            else:
                return curmis.stages[selectedindex]
    def reload_after_open(self):
        self.reloadstuff(True,True,True,True)
    def reloadstuff(self,stage=False,mission=False,stages=False,missions=False):
        if missions:
            items = []
            self.save.missions.sort(key=lambda a: a.get_sort_text())
            for i in self.save.missions:
                items.append(i.get_display_name())
            self.pnl1.Set(items)
        if stages:
            curmission = self.get_curmission()
            if curmission == None:
                self.pnl2.Set([])
            else:
                items = []
                for i in curmission.stages:
                    items.append(i.customname)
                self.pnl2.Set(items)
        if stage or stages:
            self.pnl3.loadstage(self.get_curstage())
        if mission or missions:
            self.pnl4.loadstage(self.get_curmission())

# by @chocolateimage

if __name__ == "__main__":
    app = wx.App()
    print("loading...")
    charnames = load_data_json("charnames.json")
    hudiconmapping = load_data_json("hudiconmapping.json")
    defaultlocator3names = load_data_json("defaultlocator3names.json")
    dialoguecodes = load_data_json("dialoguecodes.json")
    dialoguecodes = {v: k for k, v in dialoguecodes.items()}
    vehiclelist = load_data_json("vehiclelist.json")
    objectivetypes_vehicles = ["destroy","dump","follow","losetail","race"]
    objectivetype_vehiclebehaviours = {"race":"race","losetail":"chase"}
    objectlist = load_data_json("objects.json")
    soundlist = load_data_json("sounds.json")
    print("done loading first stuff")
    mw = MainWindow()
    app.MainLoop()