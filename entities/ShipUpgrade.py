#Do not run this file, it is a module!
import pygame, random
import entities.base as base

UPG_COL = (255,255,0)

class Main(base.Main):
    def __init__(self,x,y,LINK,ID,typ="",perm=False):
        self.init(x,y,LINK) #Init on the base class, __init__ is not called because its used for error detection.
        self.ID = ID
        if perm: #Disable towing
            self.number = 0
        else: #Enable towing
            self.number = -1
        self.type = typ #Type of ship upgrade
        if LINK["multi"]!=2: #Is not a server
            if self.LINK["simpleModels"]:
                self.__upg = LINK["render"].Model(LINK,"upgradeSimple")
            else:
                self.__upg = LINK["render"].Model(LINK,"upgrade")
        self.__sShow = True #Show in games scematic view
        self.__inRoom = False #Is true if the Ship upgrade is inside a room
        self.angle = random.randint(0,360) #Put the upgrade at a random angle
        self.size = [25,25]
        self.beingSucked = False #Make this entity suckable out of an airlock
        self.forcePos = None
        self.hintMessage = "Dont spawn"
    def SaveFile(self): #Give all infomation about this object ready to save to a file
        return ["ShipUpgrade",self.ID,self.pos]
    def LoadFile(self,data,idRef): #Load from a file
        self.pos = data[2]
    def SyncData(self,data): #Syncs the data with this upgrade
        self.pos[0] = ((self.pos[0]*3)+data["x"])/4
        self.pos[1] = ((self.pos[1]*3)+data["y"])/4
        self.discovered = data["D"]
    def deleting(self): #Called when this entity is being deleted
        if self.LINK["multi"]==2: #Is server
            self.LINK["serv"].SYNC.pop("e"+str(self.ID))
    def GiveSync(self): #Returns the synced data for this upgrade
        res = {}
        res["x"] = int(self.pos[0])+0
        res["y"] = int(self.pos[1])+0
        res["D"] = self.discovered
        return res
    def loop(self,lag):
        if self.LINK["multi"]==1: #Client
            if "e"+str(self.ID) in self.LINK["cli"].SYNC:
                self.SyncData(self.LINK["cli"].SYNC["e"+str(self.ID)])
            else:
                self.REQUEST_DELETE = True
        elif self.LINK["multi"]==2: #Server
            self.LINK["serv"].SYNC["e"+str(self.ID)] = self.GiveSync()
        if self.LINK["multi"]!=1: #Is not a client
            if not self.forcePos is None:
                bpos = [self.pos[0]+0,self.pos[1]+0]
                self.pos[0] = self.forcePos[0]+0
                self.pos[1] = self.forcePos[1]+0
                self.forcePos = None
                self.changeMesh(bpos)
                self.applyPhysics()
            self.movePath(lag)
    def sRender(self,x,y,scale,surf=None,edit=False,droneView=False): #Render in scematic view
        if surf is None:
            surf = self.LINK["main"]
        surf.blit(self.getImage("upgrade"),(x-int((self.size[0]/2)*scale),y-int((self.size[1]/2)*scale))) #Render upgrade
        if self.HINT:
            self.renderHint(surf,self.hintMessage,[x,y])
    def canShow(self,dview):
        return True
    def render(self,x,y,scale,ang,surf=None,arcSiz=-1,eAng=None): #Render the ship upgrade in 3D
        if surf is None:
            surf = self.LINK["main"]
        sx,sy = surf.get_size()
        self.__upg.render(x+(13*scale),y+(13*scale),self.angle,scale/2,surf,UPG_COL,ang,eAng,arcSiz)
