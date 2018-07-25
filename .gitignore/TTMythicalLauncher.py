from toontown.toonbase import "ToontownGlobals.py"
from toontown.toonbase import "ToontownLoader.py"
from otp.otpbase import OTPBase, "OTPGlobals.py"
from otp.nametag.ChatBalloon import "ChatBalloon.py"
from otp.nametag import NametagGlobals "NametagGlobals.py"
from otp.margins.MarginManager import "MarginManager.py"
from toontown.toonbase import TTLocalizer, "ToontownBattleGlobals.py"
tempdir = tempfile.mkdtemp()
vfs = VirtualFileSystem.getGlobalPtr()
searchPath = DSearchPath()
if __debug__:
    searchPath.appendDirectory(Filename('resources/phase_3/etc'))
searchPath.appendDirectory(Filename('/phase_3/etc'))

for filename in ['toonmono.cur', 'icon.ico']:
    p3filename = Filename(filename)
    found = vfs.resolveFilename(p3filename, searchPath)
    if not found:
        continue
    with open(os.path.join(tempdir, filename), 'wb') as f:
        f.write(vfs.readFile(p3filename, False))
loadPrcFileData('Window: icon', 'icon-filename %s' % Filename.fromOsSpecific(os.path.join(tempdir, 'icon.ico')))

class ToonBase(OTPBase.OTPBase):
    notify = DirectNotifyGlobal.directNotify.newCategory('ToonBase')

    def __init__(self):
        OTPBase.OTPBase.__init__(self)
        self.disableShowbaseMouse()
        self.addCullBins()
        self.debugRunningMultiplier /= OTPGlobals.ToonSpeedFactor
        self.lightspeed =   3.00 * 10 ** 8
        self.baseXpMultiplier = self.config.GetFloat('base-xp-multiplier', 1.0)
        self.toonChatSounds = self.config.GetBool('toon-chat-sounds', 1)
        self.placeBeforeObjects = self.config.GetBool('place-before-objects', 1)
        self.endlessQuietZone = False
        self.wantDynamicShadows = 0
        self.exitErrorCode = 0
        camera.setPosHpr(0, 0, 0, 0, 0, 0)
        self.camLens.setMinFov(settings['fov']/(4./3.))
        self.camLens.setNearFar(ToontownGlobals.DefaultCameraNear, ToontownGlobals.DefaultCameraFar)
        self.musicManager.setVolume(0.65)
        self.setBackgroundColor(ToontownGlobals.DefaultBackgroundColor)
        tpm = TextPropertiesManager.getGlobalPtr()
        candidateActive = TextProperties()
        candidateActive.setTextColor(0, 0, 1, 1)
        tpm.setProperties('candidate_active', candidateActive)
        candidateInactive = TextProperties()
        candidateInactive.setTextColor(0.3, 0.3, 0.7, 1)
        tpm.setProperties('candidate_inactive', candidateInactive)
        self.transitions.IrisModelName = 'phase_3/models/misc/iris'
        self.transitions.FadeModelName = 'phase_3/models/misc/fade'
        self.exitFunc = self.userExit
        globalClock.setMaxDt(0.2)
        if self.config.GetBool('want-particles', 1) == 1:
            self.notify.debug('Enabling particles')
            self.enableParticles()

        self.accept(ToontownGlobals.ScreenshotHotkey, self.takeScreenShot)

        # OS X Specific Actions
        if platform == "darwin":
            self.acceptOnce(ToontownGlobals.QuitGameHotKeyOSX, self.exitOSX)
            self.accept(ToontownGlobals.QuitGameHotKeyRepeatOSX, self.exitOSX)
            self.acceptOnce(ToontownGlobals.HideGameHotKeyOSX, self.hideGame)
            self.accept(ToontownGlobals.HideGameHotKeyRepeatOSX, self.hideGame)
            self.acceptOnce(ToontownGlobals.MinimizeGameHotKeyOSX, self.minimizeGame)
            self.accept(ToontownGlobals.MinimizeGameHotKeyRepeatOSX, self.minimizeGame)

        self.accept('f3', self.toggleGui)
        self.accept('f4', self.oobe)
        self.accept('panda3d-render-error', self.panda3dRenderError)
        oldLoader = self.loader
        self.loader = ToontownLoader.ToontownLoader(self)
        __builtins__['loader'] = self.loader
        oldLoader.destroy()
        self.preloader = Preloader()
        __builtins__['preloader'] = self.preloader
        self.accept('PandaPaused', self.disableAllAudio)
        self.accept('PandaRestarted', self.enableAllAudio)
        self.wantPets = self.config.GetBool('want-pets', 1)
        self.wantBingo = self.config.GetBool('want-fish-bingo', 1)
        self.wantKarts = self.config.GetBool('want-karts', 1)
        self.wantGroupTracker = self.config.GetBool('want-grouptracker', 0)
        self.inactivityTimeout = self.config.GetFloat('inactivity-timeout', ToontownGlobals.KeyboardTimeout)
        if self.inactivityTimeout:
            self.notify.debug('Enabling Panda timeout: %s' % self.inactivityTimeout)
            self.mouseWatcherNode.setInactivityTimeout(self.inactivityTimeout)
        self.mouseWatcherNode.setEnterPattern('mouse-enter-%r')
        self.mouseWatcherNode.setLeavePattern('mouse-leave-%r')
        self.mouseWatcherNode.setButtonDownPattern('button-down-%r')
        self.mouseWatcherNode.setButtonUpPattern('button-up-%r')
        self.randomMinigameAbort = self.config.GetBool('random-minigame-abort', 0)
        self.randomMinigameDisconnect = self.config.GetBool('random-minigame-disconnect', 0)
        self.randomMinigameNetworkPlugPull = self.config.GetBool('random-minigame-netplugpull', 0)
        self.autoPlayAgain = self.config.GetBool('auto-play-again', 0)
        self.skipMinigameReward = self.config.GetBool('skip-minigame-reward', 0)
        self.wantMinigameDifficulty = self.config.GetBool('want-minigame-difficulty', 0)
        self.minigameDifficulty = self.config.GetFloat('minigame-difficulty', -1.0)
        if self.minigameDifficulty == -1.0:
            del self.minigameDifficulty
        self.minigameSafezoneId = self.config.GetInt('minigame-safezone-id', -1)
        if self.minigameSafezoneId == -1:
            del self.minigameSafezoneId
        cogdoGameSafezoneId = self.config.GetInt('cogdo-game-safezone-id', -1)
        cogdoGameDifficulty = self.config.GetFloat('cogdo-game-difficulty', -1)
        if cogdoGameDifficulty != -1:
            self.cogdoGameDifficulty = cogdoGameDifficulty
        if cogdoGameSafezoneId != -1:
            self.cogdoGameSafezoneId = cogdoGameSafezoneId
        ToontownBattleGlobals.SkipMovie = self.config.GetBool('skip-battle-movies', 0)
        self.housingEnabled = self.config.GetBool('want-housing', 1)
        self.cannonsEnabled = self.config.GetBool('estate-cannons', 0)
        self.fireworksEnabled = self.config.GetBool('estate-fireworks', 0)
        self.dayNightEnabled = self.config.GetBool('estate-day-night', 0)
        self.cloudPlatformsEnabled = self.config.GetBool('estate-clouds', 0)
        self.greySpacing = self.config.GetBool('allow-greyspacing', 0)
        self.slowQuietZone = self.config.GetBool('slow-quiet-zone', 0)
        self.slowQuietZoneDelay = self.config.GetFloat('slow-quiet-zone-delay', 5)
        self.killInterestResponse = self.config.GetBool('kill-interest-response', 0)
        
        # group tracker prefs
        print('setting group tracker setting')
        if 'grouptracker' in settings:
            self.showGroupTracker = settings.get('grouptracker', False)
        else:
            self.showGroupTracker = True
        
        settings['grouptracker'] = self.showGroupTracker
        print('Group Tracker Settings:', self.showGroupTracker)

        tpMgr = TextPropertiesManager.getGlobalPtr()
        WLDisplay = TextProperties()
        WLDisplay.setSlant(0.3)
        tpMgr.setProperties('WLDisplay', WLDisplay)
        WLRed = tpMgr.getProperties('red')
        WLRed.setTextColor(1.0, 0.0, 0.0, 1)
        tpMgr.setProperties('WLRed', WLRed)
        del tpMgr
        self.lastScreenShotTime = globalClock.getRealTime()
        self.accept('InputState-forward', self.__walking)
        self.canScreenShot = 1
        self.glitchCount = 0
        self.walking = 0
        self.oldX = max(1, base.win.getXSize())
        self.oldY = max(1, base.win.getYSize())
        self.aspectRatio = float(self.oldX) / self.oldY
        self.localAvatarStyle = None

        self.filters = CommonFilters(self.win, self.cam)
        self.wantCogInterface = settings.get('cogInterface', True)
        self.wantantialiasing = settings.get('antialiasing', 1)

	self.wantWASD = settings.get('want-WASD', False)
	self.wantNews = settings.get('want-News', True)

       
        self.Move_Up = 'arrow_up'
        self.Move_Left = 'arrow_left'       
        self.Move_Down = 'arrow_down'
        self.Move_Right = 'arrow_right'
        self.JUMP = 'control'
        
        if self.wantWASD:
            self.Move_Up = 'w'
            self.Move_Left = 'a'            
            self.Move_Down = 's'
            self.Move_Right = 'd'
            self.JUMP = 'space'
        # Show cog levels on the battle GUI :D
#        self.wantCogLevelGui = settings.get('want-ShowCogLevel', True)        
        return

    def openMainWindow(self, *args, **kw):
        result = OTPBase.OTPBase.openMainWindow(self, *args, **kw)
        self.setCursorAndIcon()
        return result

    def windowEvent(self, win):
        OTPBase.OTPBase.windowEvent(self, win)
        if not config.GetInt('keep-aspect-ratio', 0):
            return
        x = max(1, win.getXSize())
        y = max(1, win.getYSize())
        maxX = base.pipe.getDisplayWidth()
        maxY = base.pipe.getDisplayHeight()
        cwp = win.getProperties()
        originX = 0
        originY = 0
        if cwp.hasOrigin():
            originX = cwp.getXOrigin()
            originY = cwp.getYOrigin()
            if originX > maxX:
                originX = originX - maxX
            if originY > maxY:
                oringY = originY - maxY
        maxX -= originX
        maxY -= originY
        if math.fabs(x - self.oldX) > math.fabs(y - self.oldY):
            newY = x / self.aspectRatio
            newX = x
            if newY > maxY:
                newY = maxY
                newX = self.aspectRatio * maxY
        else:
            newX = self.aspectRatio * y
            newY = y
            if newX > maxX:
                newX = maxX
                newY = maxX / self.aspectRatio
        wp = WindowProperties()
        wp.setSize(newX, newY)
        base.win.requestProperties(wp)
        base.cam.node().getLens().setFilmSize(newX, newY)
        self.oldX = newX
        self.oldY = newY

    def setCursorAndIcon(self):
        tempdir = tempfile.mkdtemp()
        atexit.register(shutil.rmtree, tempdir)
        vfs = VirtualFileSystem.getGlobalPtr()

        searchPath = DSearchPath()
        searchPath.appendDirectory(Filename('/phase_3/etc'))

        for filename in ['toonmono.cur', 'icon.ico']:
            p3filename = Filename(filename)
            found = vfs.resolveFilename(p3filename, searchPath)
            if not found:
                return # Can't do anything past this point.

            with open(os.path.join(tempdir, filename), 'wb') as f:
                f.write(vfs.readFile(p3filename, False))

        wp = WindowProperties()
        wp.setCursorFilename(Filename.fromOsSpecific(os.path.join(tempdir, 'toonmono.cur')))
        wp.setIconFilename(Filename.fromOsSpecific(os.path.join(tempdir, 'icon.ico')))
        self.win.requestProperties(wp)

    def addCullBins(self):
        cbm = CullBinManager.getGlobalPtr()
        cbm.addBin('ground', CullBinManager.BTUnsorted, 18)
        cbm.addBin('shadow', CullBinManager.BTBackToFront, 19)
        cbm.addBin('gui-popup', CullBinManager.BTFixed, 60)

    def disableShowbaseMouse(self):
        self.useDrive()
        self.disableMouse()
        if self.mouseInterface: self.mouseInterface.detachNode()
        if self.mouse2cam: self.mouse2cam.detachNode()

    def __walking(self, pressed):
        self.walking = pressed

    def toggleGui(self):
        if aspect2d.isHidden():
            aspect2d.show()
        else:
            aspect2d.hide()

    def takeScreenShot(self):
        if not os.path.exists(TTLocalizer.ScreenshotPath):
            os.mkdir(TTLocalizer.ScreenshotPath)
            self.notify.info('Made new directory to save screenshots.')
        namePrefix = TTLocalizer.ScreenshotPath + launcher.logPrefix + 'screenshot'
        timedif = globalClock.getRealTime() - self.lastScreenShotTime
        if self.glitchCount > 10 and self.walking:
            return
        if timedif < 1.0 and self.walking:
            self.glitchCount += 1
            return
        if not hasattr(self, 'localAvatar'):
            self.screenshot(namePrefix=namePrefix)
            self.lastScreenShotTime = globalClock.getRealTime()
            return
        if self.flashTrack and self.flashTrack.isPlaying():
            self.flashTrack.finish()
        self.transitions.noFade()
        coordOnScreen = self.config.GetBool('screenshot-coords', 0)
        self.localAvatar.stopThisFrame = 1
        ctext = self.localAvatar.getAvPosStr()
        self.screenshotStr = ''
        messenger.send('takingScreenshot')
        if coordOnScreen:
            coordTextLabel = DirectLabel(pos=(-0.81, 0.001, -0.87), text=ctext, text_scale=0.05, text_fg=VBase4(1.0, 1.0, 1.0, 1.0), text_bg=(0, 0, 0, 0), text_shadow=(0, 0, 0, 1), relief=None)
            coordTextLabel.setBin('gui-popup', 0)
            strTextLabel = None
            if len(self.screenshotStr):
                strTextLabel = DirectLabel(pos=(0.0, 0.001, 0.9), text=self.screenshotStr, text_scale=0.05, text_fg=VBase4(1.0, 1.0, 1.0, 1.0), text_bg=(0, 0, 0, 0), text_shadow=(0, 0, 0, 1), relief=None)
                strTextLabel.setBin('gui-popup', 0)
        self.graphicsEngine.renderFrame()
        self.screenshot(namePrefix=namePrefix, imageComment=ctext + ' ' + self.screenshotStr)
        self.lastScreenShotTime = globalClock.getRealTime()
        self.transitions.setFadeColor(1, 1, 1)
        self.flashTrack = Sequence(
            Func(base.playSfx, self.snapshotSfx),
            Func(self.transitions.fadeOut, 0.15),
            Wait(0.2),
            Func(self.transitions.fadeIn, 0.8),
            Wait(1.0),
            Func(self.transitions.setFadeColor, 0, 0, 0)
        )
        self.flashTrack.start()
        if coordOnScreen:
            if strTextLabel is not None:
                strTextLabel.destroy()
            coordTextLabel.destroy()
        return

    def addScreenshotString(self, str):
        if len(self.screenshotStr):
            self.screenshotStr += '\n'
        self.screenshotStr += str

    def initNametagGlobals(self):
        NametagGlobals.setMe(base.cam)

        NametagGlobals.setCardModel('phase_3/models/props/panel.bam')
        NametagGlobals.setArrowModel('phase_3/models/props/arrow.bam')
        NametagGlobals.setChatBalloon3dModel('phase_3/models/props/chatbox.bam')
        NametagGlobals.setChatBalloon2dModel('phase_3/models/props/chatbox_noarrow.bam')
        NametagGlobals.setThoughtBalloonModel('phase_3/models/props/chatbox_thought_cutout.bam')

        chatButtonGui = loader.loadModel('phase_3/models/gui/chat_button_gui.bam')
        NametagGlobals.setPageButton(
            chatButtonGui.find('**/Horiz_Arrow_UP'), chatButtonGui.find('**/Horiz_Arrow_DN'),
            chatButtonGui.find('**/Horiz_Arrow_Rllvr'), chatButtonGui.find('**/Horiz_Arrow_UP'))
        NametagGlobals.setQuitButton(
            chatButtonGui.find('**/CloseBtn_UP'), chatButtonGui.find('**/CloseBtn_DN'),
            chatButtonGui.find('**/CloseBtn_Rllvr'), chatButtonGui.find('**/CloseBtn_UP'))
        chatButtonGui.removeNode()

        rolloverSound = DirectGuiGlobals.getDefaultRolloverSound()
        if rolloverSound is not None:
            NametagGlobals.setRolloverSound(rolloverSound)
        clickSound = DirectGuiGlobals.getDefaultClickSound()
        if clickSound is not None:
            NametagGlobals.setClickSound(clickSound)

        self.marginManager = MarginManager()
        self.margins = self.aspect2d.attachNewNode(
            self.marginManager, DirectGuiGlobals.MIDGROUND_SORT_INDEX + 1)
        self.leftCells = [
            self.marginManager.addCell(0.1, -0.6, self.a2dTopLeft),
            self.marginManager.addCell(0.1, -1.0, self.a2dTopLeft),
            self.marginManager.addCell(0.1, -1.4, self.a2dTopLeft)
        ]
        self.bottomCells = [
            self.marginManager.addCell(0.4, 0.1, self.a2dBottomCenter),
            self.marginManager.addCell(-0.4, 0.1, self.a2dBottomCenter),
            self.marginManager.addCell(-1.0, 0.1, self.a2dBottomCenter),
            self.marginManager.addCell(1.0, 0.1, self.a2dBottomCenter)
        ]
        self.rightCells = [
            self.marginManager.addCell(-0.1, -0.6, self.a2dTopRight),
            self.marginManager.addCell(-0.1, -1.0, self.a2dTopRight),
            self.marginManager.addCell(-0.1, -1.4, self.a2dTopRight)
        ]
        
    def setCellsActive(self, cells, active):
        for cell in cells:
            cell.setActive(active)
        self.marginManager.reorganize()
        
    def cleanupDownloadWatcher(self):
        self.downloadWatcher.cleanup()
        self.downloadWatcher = None
        

    def startShow(self, cr, launcherServer = None):
        self.cr = cr
        if self.display.antialias:
            render.setAntialias(AntialiasAttrib.MAuto)
        base.graphicsEngine.renderFrame()
        self.downloadWatcher = ToontownDownloadWatcher.ToontownDownloadWatcher(TTLocalizer.LauncherPhaseNames)
        if launcher.isDownloadComplete():
            self.cleanupDownloadWatcher()
        else:
            self.acceptOnce('launcherAllPhasesComplete', self.cleanupDownloadWatcher)
        gameServer = config.GetString('game-server', '')
        if gameServer:
            self.notify.info('Using game-server from Configrc: %s ' % gameServer)
        elif launcherServer:
            gameServer = launcherServer
            self.notify.info('Using gameServer from launcher: %s ' % gameServer)
        else:
            gameServer = 'localhost'
        serverPort = config.GetInt('server-port', 7198)
        serverList = []
        for name in gameServer.split(';'):
            url = URLSpec(name, 1)
            if config.GetBool('server-force-ssl', False):
                url.setScheme('s')
            if not url.hasPort():
                url.setPort(serverPort)
            serverList.append(url)

        if len(serverList) == 1:
            failover = config.GetString('server-failover', '')
            serverURL = serverList[0]
            for arg in failover.split():
                try:
                    port = int(arg)
                    url = URLSpec(serverURL)
                    url.setPort(port)
                except:
                    url = URLSpec(arg, 1)

                if url != serverURL:
                    serverList.append(url)

        cr.loginFSM.request('connect', [serverList])
        self.ttAccess = ToontownAccess.ToontownAccess()
        self.ttAccess.initModuleInfo()

        if config.GetBool('want-speedhack-fix', False):
            # Start checking for speedhacks.
            self.lastSpeedhackCheck = time.time()
            self.trueClock = TrueClock.getGlobalPtr()
            self.lastTrueClockTime = self.trueClock.getLongTime()
            taskMgr.add(self.__speedhackCheckTick, 'speedhack-tick')            

    def __speedhackCheckTick(self, task):
        # Check if the time elapsed is less than interval-1 (1 second extra just in case)
        elapsed = time.time() - self.lastSpeedhackCheck
        
        tc_elapsed = self.trueClock.getLongTime() - self.lastTrueClockTime
        if tc_elapsed > elapsed + 1:
            # They responded too fast. This indicates that the TrueClock is running faster
            # than normal, and possibly means they sped the process up.
            self.__killSpeedHacker()
            return task.done
        # Clean! Lets wait until the next iteration...
        self.lastSpeedhackCheck = time.time()
        self.lastTrueClockTime = self.trueClock.getLongTime()
        return task.cont
        
    def __killSpeedHacker(self):
        # go fuck yo' self and yo' cheat engine, fuck'r.
        self.cr.bootedIndex = 128
        self.cr.bootedText = 'SERVER CONNECTION FAILURE. CLIENT HAS EXCEEDED RATE-LIMIT.'
        self.cr.stopReaderPollTask()
        self.cr.lostConnection()

    def removeGlitchMessage(self):
        self.ignore('InputState-forward')
        print 'ignoring InputState-forward'

    def exitShow(self, errorCode = None):
        self.notify.info('Exiting Toontown: errorCode = %s' % errorCode)
        if errorCode:
            launcher.setPandaErrorCode(errorCode)
        else:
            launcher.setPandaErrorCode(0)
        sys.exit()

    def setExitErrorCode(self, code):
        self.exitErrorCode = code
        if os.name == 'nt':
            exitCode2exitPage = {OTPLauncherGlobals.ExitEnableChat: 'chat',
             OTPLauncherGlobals.ExitSetParentPassword: 'setparentpassword',
             OTPLauncherGlobals.ExitPurchase: 'purchase'}
            if code in exitCode2exitPage:
                launcher.setRegistry('EXIT_PAGE', exitCode2exitPage[code])

    def getExitErrorCode(self):
        return self.exitErrorCode

    def userExit(self):
        try:
            self.localAvatar.d_setAnimState('TeleportOut', 1)
        except:
            pass

        if hasattr(self, 'ttAccess'):
            self.ttAccess.delete()
        if self.cr.timeManager:
            self.cr.timeManager.setDisconnectReason(ToontownGlobals.DisconnectCloseWindow)
        base.cr._userLoggingOut = False
        try:
            localAvatar
        except:
            pass
        else:
            messenger.send('clientLogout')
            self.cr.dumpAllSubShardObjects()

        self.cr.loginFSM.request('shutdown')
        self.notify.warning('Could not request shutdown; exiting anyway.')
        self.ignore(ToontownGlobals.QuitGameHotKeyOSX)
        self.ignore(ToontownGlobals.QuitGameHotKeyRepeatOSX)
        self.ignore(ToontownGlobals.HideGameHotKeyOSX)
        self.ignore(ToontownGlobals.HideGameHotKeyRepeatOSX)
        self.ignore(ToontownGlobals.MinimizeGameHotKeyOSX)
        self.ignore(ToontownGlobals.MinimizeGameHotKeyRepeatOSX)
        self.exitShow()

    def panda3dRenderError(self):
        launcher.setPandaErrorCode(14)
        if self.cr.timeManager:
            self.cr.timeManager.setDisconnectReason(ToontownGlobals.DisconnectGraphicsError)
        self.cr.sendDisconnect()
        sys.exit()

    def getShardPopLimits(self):
        return (config.GetInt('shard-low-pop', ToontownGlobals.LOW_POP), config.GetInt('shard-mid-pop', ToontownGlobals.MID_POP), config.GetInt('shard-high-pop', ToontownGlobals.HIGH_POP))

    def playMusic(self, music, looping = 0, interrupt = 1, volume = None, time = 0.0):
        OTPBase.OTPBase.playMusic(self, music, looping, interrupt, volume, time)


    # OS X Specific Actions
    def exitOSX(self):
        self.confirm = TTDialog.TTGlobalDialog(doneEvent='confirmDone', message=TTLocalizer.OptionsPageExitConfirm, style=TTDialog.TwoChoice)
        self.confirm.show()
        self.accept('confirmDone', self.handleConfirm)

    def handleConfirm(self):
        status = self.confirm.doneStatus
        self.ignore('confirmDone')
        self.confirm.cleanup()
        del self.confirm
        if status == 'ok':
            self.userExit()

    def hideGame(self):
        # Hacky, I know, but it works
        hideCommand = """osascript -e 'tell application "System Events"
                                            set frontProcess to first process whose frontmost is true
                                            set visible of frontProcess to false
                                       end tell'"""
        os.system(hideCommand)

    def minimizeGame(self):
        wp = WindowProperties()
        wp.setMinimized(True)
        base.win.requestProperties(wp)
