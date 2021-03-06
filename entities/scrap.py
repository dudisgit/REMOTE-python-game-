#Do not run this file, it is a module!
import pygame, random
import entities.base as base

SCRAP_COL = (200,200,0)

class Main(base.Main):
    def __init__(self,x,y,LINK,ID):
        self.init(x,y,LINK) #Init on the base class, __init__ is not called because its used for error detection.
        self.ID = ID
        self.__model = random.randint(1,3) #What model to use for the scrap
        self.__sShow = True #Show in games scematic view
        self.__inRoom = False #Is true if the scrap is inside a room
        self.size = [25,25]
        self.beingSucked = False #Make this entity suckable out of an airlock
        if LINK["multi"]!=2: #Is not a server
            self.__rmodel = LINK["render"].Model(LINK,"floorScrap"+str(random.randint(1,11))) #Model to render
        self.hintMessage = "Scrap is used to reward players, use it like coins."
    def SaveFile(self): #Give all infomation about this object ready to save to a file
        return ["scrap",self.ID,self.pos]
    def deleting(self): #Called when this entity is being deleted
        if self.LINK["multi"]==2: #Is server
            self.LINK["serv"].SYNC.pop("e"+str(self.ID))
    def LoadFile(self,data,idRef): #Load from a file
        self.pos = data[2]
    def rightInit(self,surf): #Initialize context menu for map designer
        self.__surface = pygame.Surface((210,40)) #Surface to render too
        self.__lastRenderPos = [0,0] #Last rendering position
        self.__but1 = self.LINK["screenLib"].Button(5,5,self.LINK,"Delete",lambda LINK: self.delete()) #Delete button
    def rightLoop(self,mouse,kBuf): #Event loop for the widgets inside the context menu
        self.__but1.loop([mouse[0],mouse[1]-self.__lastRenderPos[0],mouse[2]-self.__lastRenderPos[1]]+mouse[3:],kBuf)
    def SyncData(self,data): #Syncs the data with this scrap
        self.pos[0] = data["x"]
        self.pos[1] = data["y"]
        self.discovered = data["D"]
    def GiveSync(self): #Returns the synced data for this scrap
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
            self.movePath(lag)
    def rightRender(self,x,y,surf): #Render the context menu
        windowPos = [x,y+50] #Window position
        #The 4 IF statments below will make sure the context menu is allways on the screen, even if this entity is not.
        if windowPos[0]<300:
            windowPos[0] = 300
        if windowPos[0]>self.LINK["reslution"][0]-150:
            windowPos[0] = self.LINK["reslution"][0]-150
        if windowPos[1]<10:
            windowPos[1] = 10
        if windowPos[1]>self.LINK["reslution"][1]-90:
            windowPos[1] = self.LINK["reslution"][1]-90
        self.__surface.fill((0,0,0)) #Empty the context menu surface
        self.__but1.render(self.__but1.pos[0],self.__but1.pos[1],1,1,self.__surface) #Render delete button
        surfSize = self.__surface.get_size() #Get the size of the context menu
        self.__lastRenderPos = [windowPos[0]-int(surfSize[0]/2),windowPos[1]] #Used for event loops
        pygame.draw.polygon(surf,(0,255,0),[ [windowPos[0]-int(surfSize[0]/3),windowPos[1]],
                                             [x,y],
                                             [windowPos[0]+int(surfSize[0]/3),windowPos[1]] ],2) #This is the triangle pointing from the menu to the entity
        pygame.draw.rect(self.__surface,(0,255,0),[1,1,208,surfSize[1]-3],2) #Outline rectangle
        surf.blit(self.__surface,self.__lastRenderPos) #Draw all results to the screen
    def rightUnload(self): #This delets the pygame surface and widget classes. This is mainly so theirs no memory leaks.
        self.__surface = None
        self.HINT = False
        self.__but1 = None
    def editMove(self,ents): #The scrap is being moved
        self.__inRoom = type(self.insideRoom(ents)) != bool
    def giveError(self,ents): #Scans and gives an error out
        if type(self.insideRoom(ents)) == bool: #Check if inside a room
            return "No room (scrap)"
        return False
    def sRender(self,x,y,scale,surf=None,edit=False,droneView=False): #Render in scematic view
        if surf is None:
            surf = self.LINK["main"]
        if edit:
            if self.__inRoom:
                surf.blit(self.getImage("scrap1"),(x,y))
            else:
                surf.blit(self.getImage("scrap3"),(x,y))
        else:
            surf.blit(self.getImage("scrap"+str(self.__model)),(x,y))
        if self.HINT:
            self.renderHint(surf,self.hintMessage,[x,y])
    def canShow(self,Dview=False): #Should the scrap render in scematic view
        return True
    def render(self,x,y,scale,ang,surf=None,arcSiz=-1,eAng=None): #Render scrap in 3D
        if surf is None:
            surf = self.LINK["main"]
        sx,sy = surf.get_size()
        self.__rmodel.render(x+(25*scale),y+(25*scale),0,scale/3,surf,SCRAP_COL,ang,eAng,arcSiz)
