import pygame, random, math, time, mapGenerator
import multiprocessing as mp

SERVERS = ["127.0.1.1"]#,"REserver_1","REserver_2","REserver_3","REserver_4","REserver_5","REserver_6"]#,"REserver_3","REserver_4","REserver_5","REserver_6","REserver_7","REserver_8","REserver_9","REserver_10"]
#SERVERS = ["JordanG-PC"]

class Main:
    def __init__(self,LINK):
        self.__LINK = LINK
        self.__sep = 2 #Seperation between text
        self.__title = pygame.Surface((500,150)) #Title surface
        self.__title.set_colorkey((0,0,0))
        self.currentDrone = None
        self.__buzz = 0 #Time until the title will "spazz out" again
        self.__buzzWait = random.randint(10,40)/10 #Time to "spazz out" for
        self.__intro = [] #Used for charicter falling introduction
        for i in range(6):
            self.__intro.append(-65 - (i*10))
        self.__mapRend = LINK["render"].Scematic(LINK,False) #Class to use for rendering the map
        LINK["showRooms"] = True #Show all rooms
        LINK["allPower"] = True #Enable power for all rooms
        self.__proc = mp.Process(target=mapGenerator.MapGenerator,args=(self.__LINK,7,"screenMap.map",True)) #Process for generating new maps
        self.__maps = [0,0,random.randint(0,360),0] #Map position, angle and time storage
        self.__mapSim = None
        self.__backSurf = pygame.Surface(LINK["main"].get_size()) #Pygame surface to be used for effects when rendering the map
        self.__IPType = ""
        self.__screen = 0
        #0: Main screen
        #1: Server select
        #2: Options
        #3: Reslution changing
        #4: IP address entering screen
        self.__sel = 0
        self.__opts = ["Take tutorial","Play game","Play multiplayer","Options","Map designer","Quit"]
        sx,sy = LINK["main"].get_size()
        self.__LINK["multi"] = 0
        #sx = 1000
        #sy = 700
        sx2 = sy*1.777
        self.__loading = [pygame.transform.scale(LINK["content"]["loading"],(int(sx2),int(sy))),(sx2-sx)/-2,0,[sx,sy]]
    def displayLoadingScreen(self): #Display a loading screen
        surf = self.__LINK["main"]
        surf.blit(self.__loading[0],(self.__loading[1],0))
        #Error message
        fren = self.__LINK["font42"].render("Loading...",16,(0,255,0))
        sx,sy = fren.get_size()
        pygame.draw.rect(surf,(0,0,0),[int(self.__loading[3][0]/2)-int(sx/2)-5,int(self.__loading[3][1]/2)-5,sx+10,sy+10])
        pygame.draw.rect(surf,(0,255,0),[int(self.__loading[3][0]/2)-int(sx/2)-5,int(self.__loading[3][1]/2)-5,sx+10,sy+10],2)
        surf.blit(fren,(int(self.__loading[3][0]/2)-int(sx/2),int(self.__loading[3][1]/2)))
        pygame.display.flip()
    def __makeNewMap(self):
        if not self.__proc.is_alive(): #Process has finished making a map
            self.__proc = mp.Process(target=mapGenerator.MapGenerator,args=(None,7,"screenMap.map",True,)) #Create a process for generating a random map
            self.__proc.start() #Start the process simutaniulsy with the game
        else: #Process is still making a map
            print("Waiting for map gen to finish")
        self.__LINK["mesh"] = {}
        del self.__mapSim
        self.__mapSim = self.__LINK["screens"]["game"].GameEventHandle(self.__LINK) #Re-create the map simulation class
        self.__mapSim.open("screenMap.map") #Open the map in the simulator
        del self.__mapRend.ents
        self.__mapRend.ents = self.__mapSim.Map #Make the maps entities get rendered
        self.__mapSim.loop() #Only simulate the map once so doors are powered automaticly
        self.__maps = [self.__mapSim.mapSize[2]/2,self.__mapSim.mapSize[3]/2,random.randint(0,360),time.time()+random.randint(5,12)]
    def __restoreDefaults(self):
        self.__LINK["showRooms"] = False #Show all rooms
        self.__LINK["allPower"] = False #Enable power for all rooms
        self.__LINK["multi"] = 0
        self.__LINK["drones"] = [] #Drone list of the players drones
        for i in range(0,3):
            self.__LINK["drones"].append(self.__LINK["ents"]["drone"].Main(i*60,0,self.__LINK,-2-i,i+1))
        self.__LINK["drones"][0].settings["upgrades"][0] = ["motion",0,-1]
        self.__LINK["drones"][0].settings["upgrades"][1] = ["gather",0,-1]
        self.__LINK["drones"][1].settings["upgrades"][0] = ["generator",0,-1]
        self.__LINK["drones"][2].settings["upgrades"][0] = ["interface",0,-1]
        self.__LINK["drones"][2].settings["upgrades"][1] = ["tow",0,-1]
        self.__LINK["drones"][0].loadUpgrades()
        self.__LINK["drones"][1].loadUpgrades()
        self.__LINK["drones"][2].loadUpgrades()
        self.__LINK["shipEnt"] = self.__LINK["ents"]["ship"].Main(0,0,self.__LINK,-1)
        self.__LINK["shipEnt"].loadUpgrades()
        self.__LINK["shipData"] = {"fuel":5,"scrap":5,"shipUpgs":[],"maxShipUpgs":2,"reserveUpgs":[],"reserveMax":8,"invent":[],
        "beforeMap":-1,"mapSaves":[],"maxScore":0,"reserve":[],"maxDrones":4,"maxReserve":2,"maxInvent":70} #Data about the players ship
    def __servInit(self): #Called when the server selecting screen is initilized
        self.__scan = 0
        self.__cli = self.__LINK["client"].Client(SERVERS[0],3746,False)
        self.__LINK["cli"] = self.__cli
        self.__cli.TRIGGER["pls"] = self.__servGetPly
    def __servGetPly(self,pls): #Called when a server responds or the client socket fails to get info about a server
        if pls is None: #Connection failure
            self.__opts[self.__scan] = self.__opts[self.__scan] + " 4 / ERR "+self.__cli.errorReason
        else: #Server responded
            self.__opts[self.__scan] = self.__opts[self.__scan] + " " + str(pls)+" / 4"
        self.__cli.close() #Close client object
        self.__scan += 1 #Move onto next server
        if self.__scan<len(SERVERS): #Is not at the end of the list
            self.__cli = self.__LINK["client"].Client(SERVERS[self.__scan],3746,False)
            self.__LINK["cli"] = self.__cli
            self.__cli.TRIGGER["pls"] = self.__servGetPly #Call this function if the server responds
        else: #Reached the end of the server list
            self.__scan = -1
            self.__cli = None
    def loop(self,mouse,kBuf,lag): #Called continuesly to update the title screen
        if time.time()>self.__buzz:
            for a in range(6): #Go through all the charicter introductions
                if self.__intro[a]<0: #Increment
                    self.__intro[a]+=lag*4
                    if self.__intro[a]>=0:
                        self.__intro[a]=0
        if self.__screen==1: #Servers
            if not self.__cli is None:
                self.__cli.loop()
                if self.__scan!=-1:
                    if self.__cli.failConnect: #Connection failure
                        self.__servGetPly(None)
        for event in kBuf: #Event loop for keyboard
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP: #Up arrow pressed
                    self.__sel -= 1
                elif event.key == pygame.K_DOWN: #Down arrow pressed
                    self.__sel += 1
                elif event.key == pygame.K_RETURN: #Return key pressed
                    if self.__screen==0: #Main screen
                        if self.__sel==0: #Start tutorial
                            self.__restoreDefaults()
                            self.__LINK["hints"] = False
                            self.displayLoadingScreen()
                            self.__LINK["loadScreen"]("game",True)
                            self.__LINK["currentScreen"].open("tutorial.map")
                            return None
                        elif self.__sel==1: #Play the game normaly
                            self.__restoreDefaults()
                            self.displayLoadingScreen()
                            self.__LINK["loadScreen"]("shipSelect")
                            #mapGenerator.MapGenerator(self.__LINK,7,"playingMap.map")
                            #self.__LINK["currentScreen"].open("playingMap.map")
                            return None
                        elif self.__sel==2: #Play multiplayer
                            self.__screen = 1
                            self.__sel = 0
                            self.__opts = SERVERS.copy()+["Direct connect","Back"]
                            self.__servInit()
                        elif self.__sel==3: #Options menu
                            self.__screen = 2
                            self.__sel = 0
                            self.__opts = [[self.__LINK["showFPS"],"FPS counter"],[self.__LINK["particles"],"Particles"],[self.__LINK["floorScrap"],"Floor scrap"],
                                           [self.__LINK["popView"],"pop view (make rooms pop into view, reduced CPU)"],[self.__LINK["simpleModels"],"Simplified 3D models"],
                                           [self.__LINK["backgroundStatic"],"Background static"],[self.__LINK["viewDistort"],"View distortion effects"],
                                           [self.__LINK["hints"],"Hints"],[self.__LINK["threading"],"Multiplayer threading"],"Reslution","Back"]
                        elif self.__sel==4: #Map editor
                            self.__restoreDefaults()
                            self.__LINK["loadScreen"]("mapEdit")
                            return None
                        elif self.__sel==5: #Quit game
                            pygame.event.post(pygame.event.Event(pygame.QUIT)) #Simulate the user pressing the X on the pygame window
                    elif self.__screen==1 and self.__scan==-1: #Multiplayer selecting screen
                        spl = self.__opts[self.__sel].split(" ")
                        if spl[0]=="Back": #Go back to main menu
                            self.__sel = 0
                            self.__screen = 0
                            self.__opts = ["Take tutorial","Play game","Play multiplayer","Options","Map designer","Quit"]
                        elif self.__opts[self.__sel]=="Direct connect": #Go into direct connection window
                            self.__sel = 0
                            self.__screen = 4
                            self.__opts = ["Connect","Back"]
                        elif int(spl[1])<4: #Server is not full
                            self.__restoreDefaults()
                            self.displayLoadingScreen()
                            self.__LINK["cli"] = self.__LINK["client"].Client(SERVERS[self.__sel],3746,self.__LINK["threading"])
                            self.__LINK["multi"] = 1 #Set to client mode
                            self.__LINK["loadScreen"]("game")
                            return None
                    elif self.__screen==2: #In the options menu
                        if type(self.__opts[self.__sel])==list:
                            self.__opts[self.__sel][0] = not self.__opts[self.__sel][0]
                        if self.__sel==0: #FPS counter
                            self.__LINK["showFPS"] = self.__opts[0][0]==True
                        elif self.__sel==1: #Particle effects
                            self.__LINK["particles"] = self.__opts[1][0]==True
                        elif self.__sel==2: #Floor scrap
                            self.__LINK["floorScrap"] = self.__opts[2][0]==True
                        elif self.__sel==3: #Pop view
                            self.__LINK["popView"] = self.__opts[3][0]==True
                        elif self.__sel==4: #Simple models
                            self.__LINK["simpleModels"] = self.__opts[4][0]==True
                        elif self.__sel==5: #Background staitc
                            self.__LINK["backgroundStatic"] = self.__opts[5][0]==True
                        elif self.__sel==6: #View distortion
                            self.__LINK["viewDistort"] = self.__opts[6][0]==True
                        elif self.__sel==7: #Hints
                            self.__LINK["hints"] = self.__opts[7][0]==True
                        elif self.__sel==8: #Threading
                            self.__LINK["threading"] = self.__opts[8][0]==True
                        elif self.__sel==9: #Change Reslution
                            self.__screen=3
                            self.__sel = 0
                            self.__opts = ["1366x768","1920x1080","1440x900","1600x900","1280x1024","1536x864","1680x1050","1280x720","1360x768","2560x1440","1920x1200","1280x768","1024x600","1152x864","800x600","3840x2160","3440x1440","2560x1080","Back"]
                        elif self.__sel==10: #Back
                            self.__sel = 0
                            self.__screen = 0
                            self.__opts = ["Take tutorial","Play game","Play multiplayer","Options","Map designer","Quit"]
                    elif self.__screen==3: #Reslution selecting screen
                        if "x" in self.__opts[self.__sel]: #Change reslution of game
                            spl = self.__opts[self.__sel].split("x")
                            self.__LINK["reslution"] = [int(spl[0]),int(spl[1])]
                            self.__LINK["main"] = pygame.display.set_mode([int(spl[0]),int(spl[1])],pygame.FULLSCREEN) #Remake the pygame window
                        #Go back to options menu
                        self.__screen = 2
                        self.__sel = 0
                        self.__opts = [[self.__LINK["showFPS"],"FPS counter"],[self.__LINK["particles"],"Particles"],[self.__LINK["floorScrap"],"Floor scrap"],
                                        [self.__LINK["popView"],"pop view (make rooms pop into view, reduced CPU)"],[self.__LINK["simpleModels"],"Simplified 3D models"],
                                        [self.__LINK["backgroundStatic"],"Background static"],[self.__LINK["viewDistort"],"View distortion effects"],
                                        [self.__LINK["hints"],"Hints"],[self.__LINK["threading"],"Multiplayer threading"],"Reslution","Back"]
                    elif self.__screen==4: #IP address entering
                        if self.__sel==0: #Connect to server
                            self.__restoreDefaults()
                            self.displayLoadingScreen()
                            self.__LINK["cli"] = self.__LINK["client"].Client(self.__IPType,3746,self.__LINK["threading"])
                            self.__LINK["multi"] = 1 #Set to client mode
                            self.__LINK["loadScreen"]("game")
                            return None
                        else: #Go back to main menu
                            self.__sel = 0
                            self.__screen = 0
                            self.__opts = ["Take tutorial","Play game","Play multiplayer","Options","Map designer","Quit"]
                elif self.__screen==4: #IP address entering
                    if event.key == pygame.K_BACKSPACE:
                        self.__IPType = self.__IPType[:-1]
                    elif (event.key>=48 and event.key<=57) or event.key==46:
                        self.__IPType = self.__IPType+chr(event.key)
                self.__sel = self.__sel % len(self.__opts)
        #Scroll accross the map
        self.__maps[0]+=math.cos(self.__maps[2]/180*math.pi)*lag
        self.__maps[1]+=math.sin(self.__maps[2]/180*math.pi)*lag
        if time.time()>self.__maps[3]: #Create a new map to scroll accross
            self.__makeNewMap()
    def updateTitle(self,surf,amo=10): #Updates the title surface
        self.__title.fill((0,0,0))
        sx,sy = surf.get_size()
        for i,a in enumerate("REMOTE"): #Render each charicter
            self.__title.blit(self.__LINK["font128"].render(a,16,(255,255,255)),((i*30*self.__sep)+40, 20+self.__intro[i]))
        PX = pygame.PixelArray(self.__title)
        for y in range(150): #"Spazz out" each pixel in the X column
            RX = random.randint(0,amo)
            PX[0:400-RX,y] = PX[RX:400,y]
    def render(self,surf=None): #Renders the title screen
        if surf is None:
            surf = self.__LINK["main"]
        sx,sy = surf.get_size()
        if time.time()>self.__buzz or self.__intro[-1]!=0: #"Spazz out" the title screen
            self.updateTitle(surf)
            if time.time()>self.__buzz+self.__buzzWait and self.__intro[-1]==0: #End of "spazz out"
                self.__buzz = time.time()+(random.randint(0,50)/10) #Set time to "spazz out" again
                self.__buzzWait = random.randint(5,20)/10 #Set amount of time to "spazz out" for
                self.updateTitle(surf,0) #Make the title surface clean
                self.__sep = random.randint(18,22)/10 #Add a random seperation between each charicter for next update
                if random.randint(0,1)==1: #50% chance a random charicter will raise to the top
                    self.__intro[random.randint(0,len(self.__intro)-1)] = -20
        sx2,sy2 = self.__title.get_size()
        BSUF = pygame.transform.rotozoom(self.__backSurf,0.6,0.9) #Rotate and zoom out of the previous frame of the map rendering
        BSUF.set_alpha(200) #Darken it by 55
        self.__backSurf.fill((0,0,0)) #Fill current frame with blackness
        self.__backSurf.blit(BSUF,(10,10)) #Render the previous frame onto this one
        self.__mapRend.render(self.__maps[0],self.__maps[1],2,self.__backSurf,False) #Draw the map
        self.__backSurf.set_alpha(100) #Set its alpha down by 155
        surf.blit(self.__backSurf,(0,0)) #Render the final result of the background map onto the screen
        surf.blit(self.__title,((sx/2)-(sx2/2),(sy*0.2)-(sy2/2) )) #Render cached title surface
        mult = abs(math.cos(time.time()*3)) #Box flashing
        scroll = 0
        if (sy*0.4)+(len(self.__opts)*45)>sy*0.8: #Too many options to display on screen
            if (sy*0.4)+(self.__sel*45)>sy*0.6: #Selecting option is going off the screen
                scroll = int((((sy*0.4)+(self.__sel*45))-(sy*0.6))/45) #Start at a few options before selection
        MX = 0 #Maximum width
        Buf = []
        for i,a in enumerate(self.__opts): #Go through to find and measure the longest peaice of text
            if type(a)==list:
                Buf.append(self.__LINK["font42"].render(a[1],16,(255,255,255)))
                if Buf[-1].get_width()+30>MX:
                    MX = Buf[-1].get_width()+30
            else:
                Buf.append(self.__LINK["font42"].render(a,16,(255,255,255)))
                if Buf[-1].get_width()>MX:
                    MX = Buf[-1].get_width()+0
        MX+=5
        for i,a in enumerate(self.__opts[scroll:]):
            pygame.draw.rect(surf,(0,0,0),[15,(sy*0.4)+(i*45)+1,MX,35])
            if i+scroll==self.__sel:
                pygame.draw.rect(surf,(255*mult,255*mult,0),[15,(sy*0.4)+(i*45)+1,MX,35],5)
            else:
                pygame.draw.rect(surf,(0,255,0),[15,(sy*0.4)+(i*45)+1,MX,35],2)
            if type(a)==list: #Rendered option is a boolean option
                col = (255,0,255)
                if a[0]:
                    col = (0,255,0)
                else:
                    col = (255,0,0)
                pygame.draw.rect(surf,col,[20,(sy*0.4)+(i*45)+6,25,25])
                surf.blit(Buf[i+scroll],(50,(sy*0.4)+(i*45)))
            else:
                surf.blit(Buf[i+scroll],(20,(sy*0.4)+(i*45)))
        if self.__screen==4: #In IP entering screen
            tex = self.__LINK["font42"].render(self.__IPType,16,(255,255,255))
            sx2,sy2 = tex.get_size()
            pygame.draw.rect(surf,(0,0,0),[(sx/2)-(sx2/2)-4,(sy*0.35)-4,sx2+8,sy2+8])
            pygame.draw.rect(surf,(0,255*mult,0),[(sx/2)-(sx2/2)-4,(sy*0.35)-4,sx2+8,sy2+8],2)
            surf.blit(tex,(int((sx/2)-(sx2/2)),int(sy*0.35)))