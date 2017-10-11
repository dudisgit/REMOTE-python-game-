#This file is used to render entities
import pygame, time, screenLib, os, pickle

class Scematic:
    def __init__(self,LINK,edit=False):
        self.__LINK = LINK
        self.__edit = edit #If the view of this scematic is through an editor (e.g. map editor)
        self.ents = [] #Entities to be rendered
        self.__scaleChange = 0 #Used to detect changes in scale
    def render(self,x,y,scale,surf=None):
        if surf is None:
            surf = self.__LINK["main"]
        edit = self.__edit == True
        if scale != self.__scaleChange: #Resize all images if a scale change is detected.
            for a in self.__LINK["content"]:
                siz = list(self.__LINK["content"][a].get_size())
                self.__LINK["cont"][a] = pygame.transform.scale(self.__LINK["content"][a],(int(siz[0]*scale/10.24),int(siz[1]*scale/10.24)))
            self.__scaleChange = scale+0
        for a in self.ents:
            if a.canShow() or edit:
                a.sRender((a.pos[0]*scale)-x,(a.pos[1]*scale)-y,scale,surf,edit)

def drawDevMesh(x,y,scale,surf,LINK): #Used in development only, this will draw a pixel grid for MESH
    for xp in LINK["mesh"]:
        for yp in LINK["mesh"][xp]:
            pygame.draw.rect(surf,(75,0,75),[(xp*scale*125)-x,(yp*scale*125)-y,125*scale,125*scale],1)
            surf.blit(LINK["font24"].render(str(len(LINK["mesh"][xp][yp])),16,(255,0,255)),[(xp*scale*125)-x,(yp*scale*125)-y])
            mid = [(xp*scale*125)-x+(62*scale),(yp*scale*125)-y+(62*scale)]
            for a in LINK["mesh"][xp][yp]:
                pygame.draw.line(surf, (75,0,75), mid, [(a.pos[0]*scale)-x,(a.pos[1]*scale)-y])
def drawConnection(x,y,surf,LINK): #Used in development only, will draw a graph explaining how behind SYNC is
    #The algorithms made to display this infomation are not designed to be fast!
    if LINK["multi"]==1: #Is a client
        POS,BRS = LINK["cli"].getInfo()
        MX = 1
        DR = []
        for a in BRS: #Find maximum message length
            if a!=False:
                LN = len(pickle.dumps(a))
                if LN>MX:
                    MX = LN+0
                DR.append(LN)
            else:
                DR.append(False)
        for i,a in enumerate(DR): #Draw all bars
            Height = 10
            if i==POS: #Is currently received message
                col = (0,255,0)
            elif a!=False: #Bar is awaiting to be processed
                col = (255,0,0)
            else: #Received and processed
                col = (0,0,0)
            if a!=False:
                Height = int((a/MX)*20)
                if Height<5:
                    Height = 5
            pygame.draw.line(surf,col,[x+(i*2),y],[x+(i*2),y+Height],2)
        pygame.draw.rect(surf,(255,255,0),[x,y,len(BRS)*2,20],1)
    elif LINK["multi"]==2: #Is a server
        i = 0
        for a in LINK["serv"].users: #Draw a bar graph for all users connected
            surf.blit(LINK["font24"].render(LINK["serv"].users[a].name,16,(255,255,255)),[x+10,y+5+(i*70)])
            cPos = LINK["serv"].users[a].IDRec
            IC = LINK["serv"].users[a].getIDSend()
            for i2,b in enumerate(LINK["serv"].users[a].ReceiveBuffer): #Draw a bar graph for the received buffer
                if i2==cPos: #Currently received message
                    col = (0,255,0)
                elif i2==IC: #Is the currently sent position (used for reference in anouther graph)
                    col = (0,0,255)
                elif not b is None: #Is awaiting to be processed
                    col = (255,0,0)
                else: #Processed and finished
                    col = (0,0,0)
                pygame.draw.line(surf,col,[x+(i2*2),y+25+(i*70)],[x+(i2*2),y+40+(i*70)],2)
            pygame.draw.rect(surf,(255,255,0),[x,y+25+(i*70),len(LINK["serv"].users[a].ReceiveBuffer)*2,20],1)
            MX = 1
            DR = []
            for b in LINK["serv"].users[a].SendingBuffer: #Find the maximum bar height
                if not b is None:
                    LN = len(pickle.dumps(b))
                    if LN>MX:
                        MX = LN+0
                    DR.append(LN)
                else:
                    DR.append(None)
            for i2,b in enumerate(DR): #Draw all the bars
                if b is None:
                    Height = 10
                else:
                    Height = int((b/MX)*20)
                    if Height<5:
                        Height = 5
                pygame.draw.line(surf,(255,255,255),[x+(i2*2),y+50+(i*70)],[x+(i2*2),y+50+Height+(i*70)],2)
            pygame.draw.rect(surf,(255,255,0),[x,y+50+(i*70),len(LINK["serv"].users[a].ReceiveBuffer)*2,20],1)
            b1,b2 = LINK["serv"].users[a].getBufs()
            surf.blit(LINK["font24"].render("Last send: "+str(LINK["serv"].users[a].SendingBuffer[IC-1]),16,(255,255,255)),[x+130,y+20+(i*70)])
            surf.blit(LINK["font24"].render("TCP length: "+str(b1),16,(255,255,255)),[x+130,y+40+(i*70)])
            surf.blit(LINK["font24"].render("UDP length: "+str(b2),16,(255,255,255)),[x+130,y+60+(i*70)])
            i+=1
class CommandLine: #A command line interface with tabs
    def __init__(self,LINK,drones=3):
        self.__LINK = LINK
        self.tabs = [] #Variable to store all the tabs inside of.
        #Syntax:
        #0: Tab name
        #1: Contents
        #2: Damage/colour of tab
        #3: Upgrades
        #4: Is being attacked
        #5: (option) Drone object
        self.tabs.append(["SCHEMATIC",[[">",[255,255,255]]],0,[],False]) #For the ship
        self.activeTab = 0
    def settings(self,Tab,dmg=0,attacked=False,upgrades=None): #Change settings of a tab
        if Tab<0 or Tab>=len(self.tabs): #Check if tab is valid
            self.__LINK["errorDisplay"]("Command line was asked to edit a tab but it doesen't exist.")
        else:
            self.tabs[Tab][2] = dmg #Apply damage
            self.tabs[Tab][4] = attacked == True #Being attacked
            if upgrades!=None: #Check if any upgrades need changing
                self.tabs[Tab][3] = upgrades
    def addLine(self,line,colour,Tab=-1): #Adds a line with its colour to the command line
        if Tab==-1: #Add command to current tab
            if self.activeTab>=0 and self.activeTab<len(self.tabs): #Check if current tab is valid
                self.tabs[self.activeTab][1].append([line,colour])
                if len(self.tabs[self.activeTab][1])>60:
                    self.tabs[self.activeTab][1].pop(-1)
            else: #Display error
                self.__LINK["errorDisplay"]("Active tab in command line is invalid!")
        elif Tab>=0 and Tab<len(self.tabs): #Check if given tab is valid
            self.tabs[Tab][1].append([line,colour])
            if len(self.tabs[Tab][1])>60:
                self.tabs[Tab][1].pop(-1)
        else: #Display an error
            self.__LINK["errorDisplay"]("Given tab does not exist "+str(Tab))
    def replaceLast(self,line,col=None,tab=None): #Changes the text at the end of the current tab command line
        if tab is None:
            TAB = self.activeTab
        else:
            TAB = tab
        if TAB>=0 and TAB<len(self.tabs): #Check if current tab is valid
            self.tabs[TAB][1][-1][0] = line
            if not col is None:
                self.tabs[TAB][1][-1][1] = col
        else: #Display an error
            self.__LINK["errorDisplay"]("Editing tab that doesen't exist "+str(TAB))
    def render(self,x,y,sizex,sizey,surf=None): #Render the command line
        if surf is None: #Get the main surface if none is supplied
            surf = self.__LINK["main"]
        col2 = (0,0,0) #Colour for the boarder of the command line
        for i,a in enumerate(self.tabs): #Render all tabs
            if i==self.activeTab: #Tab is currently selected
                col = (0,200,0)
                #Set boarder colour to tabs damage status
                if a[2]==0:
                    col2 = (200,200,200)
                elif a[2]==1:
                    col2 = (200,200,0)
                else:
                    col2 = (200,0,0)
            elif a[2]==0: #Normal
                col = (200,200,200)
            elif a[2]==1: #Damaged
                col = (200,200,0)
            elif a[2]==2: #Dead
                col = (200,0,0)
            else: #Error
                col = (0,0,0)
            pygame.draw.rect(surf,(0,0,0),[x+(i*80),y-19,70,20]) #Draw black rectangle to the box isn't see-through
            pygame.draw.rect(surf,col,[x+(i*80),y-19,70,20],2+(round(time.time()-int(time.time()))*int(a[4])*5)) #Draw border of tab
            surf.blit(self.__LINK["font16"].render(a[0],16,(255,255,255)),(x+(i*80)+3,y-15)) #Draw name of tab
            if len(a)!=5:
                H = a[5].health/a[5].settings["maxHealth"]
                if a[2]==2:
                    H = 0
                pygame.draw.polygon(surf,(0,50,0),[ [x+(i*80),y-49], [x+(i*80)+70,y-49], [x+(i*80)+(70*H)+70,y-((71*H)+49)], [x+(i*80)+(70*H),y-((71*H)+49)] ])
                pygame.draw.polygon(surf,(0,255,0),[ [x+(i*80),y-49], [x+(i*80)+70,y-49], [x+(i*80)+140,y-120], [x+(i*80)+70,y-120] ],2)
            for c,b in enumerate(a[3]):
                if b.damage==0:
                    if b.used:
                        col = (0,255,0)
                    else:
                        col = (255,255,255)
                elif b.damage==1:
                    col = (255,255,0)
                else:
                    col = (255,0,0)
                dr = pygame.transform.rotate(self.__LINK["font24"].render(b.displayName,16,col),45)
                surf.blit(dr,(x+(i*80)+3+(c*25),y-45-dr.get_height()))
                if "icon"+b.name in self.__LINK["content"]:
                    surf.blit(self.__LINK["content"]["icon"+b.name],(x+(i*80)+3+(c*25),y-45))
                else:
                    surf.blit(self.__LINK["content"]["iconbase"],(x+(i*80)+3+(c*25),y-45))
        pygame.draw.rect(surf,(0,0,0),[x,y,sizex,sizey]) #Draw a black rectangle so it isn't see-through
        pygame.draw.rect(surf,col2,[x,y,sizex,sizey],2) #Draw boarder for command line
        if self.activeTab>=0 and self.activeTab<len(self.tabs): #Render command lines text if the tab is valid
            #Draw command line with text wrapping
            X = x+3
            Y = y+sizey-24
            for i in range(1,60): #Go throguh 60 possible text lines (normlay it will only go to 12)
                if i>len(self.tabs[self.activeTab][1]):
                    break
                a = self.tabs[self.activeTab][1][-i]
                #Text wrapping into a list
                Split = a[0].split(" ")
                Build = ""
                words = []
                for b in Split:
                    if self.__LINK["font24"].size(Build+b+" ")[0]>sizex:
                        words.append(Build+"")
                        Build = b+" "
                    else:
                        Build += b+" "
                words.append(Build)
                words.reverse()
                #Draw the text wrap list
                for i2,b in enumerate(words):
                    surf.blit(self.__LINK["font24"].render(b,16,a[1]),(X,Y))
                    Y -= 18
                    if Y<y: #Going off the top of the command line window
                        break
                if Y<y: #Going off the top of the command line window
                    break

class DebugServer: #This is a tkinter window that is used to debug the server and show entities.
    def __init__(self,LINK):
        pygame.init() #Initialize pygame
        self.__LINK = LINK
        LINK["DEVDIS"] = True
        self.__main = pygame.display.set_mode([500,400]) #Make a pygame window
        files = os.listdir("content")
        LINK["content"] = {}
        for a in files:
            if a[-4:]==".png":
                LINK["content"][a[:-4]] = pygame.image.load("content/"+a)
                LINK["content"][a[:-4]].set_colorkey((0,0,0))
        LINK["cont"] = {} #This is used for storing "content" in LINK but is resized every frame.
        LINK["font24"] = pygame.font.Font("comandFont.ttf",24)
        LINK["font16"] = pygame.font.Font("comandFont.ttf",16)
        LINK["font42"] = pygame.font.Font("comandFont.ttf",42)
        self.__textEnt = screenLib.TextEntry(0,0,LINK,200,True,"Command line",self.COM) #Command line entry
        self.__pos = [0,0]
        self.__zoom = 1
        self.__rdn = Scematic(LINK)
        self.__av = 60 #Average FPS
        self.__lastTime = time.time()
        pygame.display.set_caption("Server debug window")
        LINK["main"] = self.__main
    def COM(self,LNK,text):
        self.__LINK["world"].doCommand(text,-1)
        self.__textEnt.text = ""
    def render(self,MAP):
        self.__rdn.ents = MAP
        lag = (time.time()-self.__lastTime)*30 # Used to vary lag
        self.__lastTime = time.time()
        EV = []
        for event in pygame.event.get():
            EV.append(event)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.__pos[1]+=15
                elif event.key == pygame.K_DOWN:
                    self.__pos[1]-=15
                elif event.key == pygame.K_LEFT:
                    self.__pos[0]+=15
                elif event.key == pygame.K_RIGHT:
                    self.__pos[0]-=15
                elif event.key == pygame.K_w:
                    self.__zoom /= 2
                elif event.key == pygame.K_s:
                    self.__zoom *= 2
        mouseRaw = pygame.mouse.get_pressed()
        mouse = [mouseRaw[0]]+list(pygame.mouse.get_pos())+[mouseRaw[1],mouseRaw[2]]
        self.__textEnt.loop(mouse,EV)
        self.__main.fill((0,0,0))
        self.__rdn.render(self.__pos[0],self.__pos[1],self.__zoom,self.__main)
        self.__textEnt.render()
        self.__main.blit(self.__LINK["font24"].render("FPS: "+str(int(30/lag)),16,(255,0,255)),[10,60])
        self.__av = ((self.__av*800) + int(30/lag))/801
        self.__main.blit(self.__LINK["font24"].render("AVERAGE FPS: "+str(int(self.__av)),16,(255,0,255)),[10,75])
        self.__main.blit(self.__LINK["font24"].render("LAG: "+str(lag),16,(255,0,255)),[10,90])
        drawConnection(10,120,self.__main,self.__LINK)
        pygame.display.flip()
