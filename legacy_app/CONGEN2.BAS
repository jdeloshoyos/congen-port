'$INCLUDE: 'DIRECTQB.BI'

IF DQBinit(4, 14, 0) THEN DQBclose: PRINT DQBerror$: END

DQBinitVGA

IF DQBinstallSB(FALSE, 6, 22050, AUTO, AUTO, AUTO) THEN DQBclose: PRINT DQBerror$: END

RANDOMIZE TIMER

' Declaraci¢n de tipos de datos

TYPE PlayerType
  x AS INTEGER
  y AS INTEGER
  VelX AS INTEGER
  VelY AS INTEGER
  Turnflag AS INTEGER
  Shotdelay AS INTEGER
  Health AS INTEGER
  Deathflag AS INTEGER
  Score AS LONG
  Gunlevel AS INTEGER
  Invencible AS INTEGER
  Ammo AS INTEGER
END TYPE

TYPE MissileType
  x AS SINGLE
  y AS SINGLE
  VelX AS SINGLE
  VelY AS SINGLE
  Owner AS INTEGER
  Ang AS INTEGER
  Lockon AS INTEGER
END TYPE

TYPE PshotType
  x AS INTEGER
  y AS INTEGER
  VelY AS INTEGER
  Class AS INTEGER
END TYPE

TYPE DebrisType
  x AS SINGLE
  y AS SINGLE
  VelX AS SINGLE
  VelY AS SINGLE
  Userflag AS INTEGER
END TYPE

TYPE EventType
  Frame AS INTEGER
  Kind AS STRING * 1
  Buff AS STRING * 40
  x AS INTEGER
  y AS INTEGER
END TYPE

TYPE EnemyType
  x AS SINGLE
  y AS SINGLE
  VelX AS SINGLE
  VelY AS SINGLE
  Userflag AS INTEGER
  Health AS INTEGER
  Kind AS INTEGER
  Powerup AS STRING * 1
  BossDeathFlag AS INTEGER
END TYPE

TYPE EShotType
  x AS SINGLE
  y AS SINGLE
  VelX AS SINGLE
  VelY AS SINGLE
  Ang AS INTEGER
END TYPE

' Variables y constantes del juego
DIM maxscore AS LONG

OPEN "cg2data\savegame.dat" FOR INPUT AS #1
INPUT #1, maxscore
INPUT #1, maxlevelreached
CLOSE #1

maxplayers = 2
maxpshots = 4
maxdebris = 50
' map$ = "mapa1"
mapnumber = 1

' Dimensionamiento de variables y matrices

DIM Pal AS STRING * 768
DIM Player(maxplayers) AS PlayerType
DIM pshot(maxpshots) AS PshotType
DIM Debris(maxdebris) AS DebrisType
DIM plsprites(514 * 10) AS INTEGER
DIM enemysprites(514 * 11) AS INTEGER
DIM explsprites(514 * 8) AS INTEGER
DIM bosssprites(514 * 12) AS INTEGER
DIM debrsprites(34 * 8) AS INTEGER
DIM tileset(514 * 20) AS INTEGER
DIM scrollstring AS STRING * 10
DIM mapdata(1 TO 10, 1 TO 400)  AS STRING * 1
DIM Eventdata(200) AS EventType
DIM Enemy(8) AS EnemyType
DIM EShot(8) AS EShotType
DIM Missile(4) AS MissileType
DIM missileprecision AS SINGLE
DIM tilesetfile AS STRING * 12

' Cargando Gr ficos

IF DQBloadImage(1, 0, 0, "cg2data\nave.pcx", Pal, iw, ih) THEN DQBclose: PRINT DQBerror$: END
IF DQBloadImage(1, 32, 0, "cg2data\nave2.pcx", Pal, iw, ih) THEN DQBclose: PRINT DQBerror$: END
IF DQBloadImage(1, 64, 0, "cg2data\nave3.pcx", Pal, iw, ih) THEN DQBclose: PRINT DQBerror$: END
IF DQBloadImage(1, 96, 0, "cg2data\disparo.pcx", Pal, iw, ih) THEN DQBclose: PRINT DQBerror$: END
IF DQBloadImage(1, 128, 0, "cg2data\disparo2.pcx", Pal, iw, ih) THEN DQBclose: PRINT DQBerror$: END
IF DQBloadImage(1, 160, 0, "cg2data\disparo3.pcx", Pal, iw, ih) THEN DQBclose: PRINT DQBerror$: END
IF DQBloadImage(1, 192, 0, "cg2data\powerup.pcx", Pal, iw, ih) THEN DQBclose: PRINT DQBerror$: END
IF DQBloadImage(1, 224, 0, "cg2data\salud.pcx", Pal, iw, ih) THEN DQBclose: PRINT DQBerror$: END
IF DQBloadImage(1, 0, 96, "cg2data\explo.pcx", Pal, iw, ih) THEN DQBclose: PRINT DQBerror$: END
IF DQBloadImage(1, 256, 0, "cg2data\debris.pcx", Pal, iw, ih) THEN DQBclose: PRINT DQBerror$: END
IF DQBloadImage(1, 0, 128, "cg2data\malo1.pcx", Pal, iw, ih) THEN DQBclose: PRINT DQBerror$: END
IF DQBloadImage(1, 192, 96, "cg2data\hit.pcx", Pal, iw, ih) THEN DQBclose: PRINT DQBerror$: END
IF DQBloadImage(1, 256, 96, "cg2data\misil.pcx", Pal, iw, ih) THEN DQBclose: PRINT DQBerror$: END
IF DQBloadImage(1, 288, 96, "cg2data\misilbox.pcx", Pal, iw, ih) THEN DQBclose: PRINT DQBerror$: END
IF DQBloadImage(1, 64, 128, "cg2data\malo2.pcx", Pal, iw, ih) THEN DQBclose: PRINT DQBerror$: END
IF DQBloadImage(1, 160, 128, "cg2data\malo3.pcx", Pal, iw, ih) THEN DQBclose: PRINT DQBerror$: END
IF DQBloadImage(1, 224, 128, "cg2data\mina.pcx", Pal, iw, ih) THEN DQBclose: PRINT DQBerror$: END
IF DQBloadImage(1, 256, 128, "cg2data\malo4.pcx", Pal, iw, ih) THEN DQBclose: PRINT DQBerror$: END
IF DQBloadImage(1, 0, 160, "cg2data\malo5.pcx", Pal, iw, ih) THEN DQBclose: PRINT DQBerror$: END

IF DQBloadFont("cg2data\hitech.fnt") THEN DQBclose: PRINT DQBerror$: END

FOR t = 0 TO 7
  DQBget 1, t * 32, 0, t * 32 + 31, 31, VARSEG(plsprites(t * 514)), VARPTR(plsprites(t * 514))
NEXT t
DQBget 1, 256, 96, 256 + 31, 96 + 31, VARSEG(plsprites(8 * 514)), VARPTR(plsprites(8 * 514))
DQBget 1, 288, 96, 288 + 31, 96 + 31, VARSEG(plsprites(9 * 514)), VARPTR(plsprites(9 * 514))

FOR t = 0 TO 7
  DQBget 1, t * 32, 96, t * 32 + 31, 96 + 31, VARSEG(explsprites(t * 514)), VARPTR(explsprites(t * 514))
NEXT t

FOR t = 0 TO 7
  DQBget 1, 256 + t * 8, 0, 256 + t * 8 + 7, 7, VARSEG(debrsprites(t * 34)), VARPTR(debrsprites(t * 34))
NEXT t

FOR t = 0 TO 9
  DQBget 1, t * 32, 128, t * 32 + 31, 159, VARSEG(enemysprites(t * 514)), VARPTR(enemysprites(t * 514))
NEXT t

FOR t = 0 TO 0
  DQBget 1, t * 32, 160, t * 32 + 31, 191, VARSEG(enemysprites((t + 10) * 514)), VARPTR(enemysprites((t + 10) * 514))
NEXT t


' DQBcopyLayer 1, 0                 ' }
' DO                                ' }
' LOOP UNTIL INKEY$ <> ""           ' } Para mostrar los gr ficos
' DQBclose                          ' }
' END                               ' }

' Carga de sonidos

IF DQBloadSound(1, "cg2data\disparo.wav") THEN DQBclose: PRINT DQBerror$: END
IF DQBloadSound(2, "cg2data\explo.wav") THEN DQBclose: PRINT DQBerror$: END
IF DQBloadSound(3, "cg2data\golpe.wav") THEN DQBclose: PRINT DQBerror$: END
IF DQBloadSound(4, "cg2data\muerte.wav") THEN DQBclose: PRINT DQBerror$: END
IF DQBloadSound(5, "cg2data\pausa.wav") THEN DQBclose: PRINT DQBerror$: END
IF DQBloadSound(6, "cg2data\texto.wav") THEN DQBclose: PRINT DQBerror$: END
IF DQBloadSound(7, "cg2data\disparo2.wav") THEN DQBclose: PRINT DQBerror$: END
IF DQBloadSound(8, "cg2data\disparo3.wav") THEN DQBclose: PRINT DQBerror$: END
IF DQBloadSound(9, "cg2data\powerup.wav") THEN DQBclose: PRINT DQBerror$: END
IF DQBloadSound(10, "cg2data\salud.wav") THEN DQBclose: PRINT DQBerror$: END
IF DQBloadSound(11, "cg2data\finjefe.wav") THEN DQBclose: PRINT DQBerror$: END
IF DQBloadSound(12, "cg2data\misil.wav") THEN DQBclose: PRINT DQBerror$: END
IF DQBloadSound(13, "cg2data\rocketl.wav") THEN DQBclose: PRINT DQBerror$: END
IF DQBloadSound(14, "cg2data\menu.wav") THEN DQBclose: PRINT DQBerror$: END

DQBinstallKeyboard
DQBsetFrameRate 50

' Interfaz del men£ principal.

MenuPrincipal:

DQBclearLayer 2
DQBclearLayer 1
DQBclearLayer 0

DQBsetPal Pal

IF DQBloadImage(3, 0, 0, "cg2data\menu1.pcx", Pal, iw, ih) THEN DQBclose: PRINT DQBerror$: END

IF DQBloadImage(2, 0, 0, "cg2data\menu2.pcx", Pal, iw, ih) THEN DQBclose: PRINT DQBerror$: END

DQBcopyTransLayer 3, 1

DQBprint 2, "Iniciar juego", 180, 60, 255
DQBprint 2, "Nivel de inicio:", 180, 100, 255
' DQBprint 2, "1", 180, 108, 145
DQBprint 2, "Salir", 180, 140, 255
DQBprint 2, "Maximo puntaje:", 10, 191, 40
DQBprint 2, STR$(maxscore), 120, 191, 125


DQBput 1, 140, 48, VARSEG(enemysprites(2 * 514)), VARPTR(enemysprites(2 * 514))

DQBcopyLayer 1, 0

maxkeydelay = 25
keydelay = 0
menuopt = 1
cursorframe = 0

DO

DQBcopyLayer 2, 1
DQBcopyTransLayer 3, 1

DQBput 1, 140, (menuopt - 1) * 40 + 48, VARSEG(enemysprites((INT(cursorframe / 5) + 2) * 514)), VARPTR(enemysprites((INT(cursorframe / 5) + 2) * 514))

cursorframe = cursorframe + 1
IF cursorframe = 15 THEN cursorframe = 0

IF DQBkey(KEYUP) OR DQBkey(KEYDOWN) OR DQBkey(KEYLEFT) OR DQBkey(KEYRIGHT) THEN
  IF keydelay > 0 THEN keydelay = keydelay - 1
ELSE
  keydelay = 0
END IF

IF keydelay = 0 THEN
  IF DQBkey(KEYUP) THEN
    keydelay = maxkeydelay
    menuopt = menuopt - 1
    DQBplaySound 14, 1, 22050, ONCE
    IF menuopt = 0 THEN menuopt = 3
    IF menuopt = 4 THEN menuopt = 1
    SELECT CASE menuopt
      CASE 1
        IF DQBloadImage(2, 0, 0, "cg2data\menu2.pcx", Pal, iw, ih) THEN DQBclose: PRINT DQBerror$: END
      CASE 2
        IF DQBloadImage(2, 0, 0, "cg2data\menu3.pcx", Pal, iw, ih) THEN DQBclose: PRINT DQBerror$: END
      CASE 3
        IF DQBloadImage(2, 0, 0, "cg2data\menu4.pcx", Pal, iw, ih) THEN DQBclose: PRINT DQBerror$: END
    END SELECT
  END IF
  IF DQBkey(KEYDOWN) THEN
    keydelay = maxkeydelay
    menuopt = menuopt + 1
    DQBplaySound 14, 1, 22050, ONCE
    IF menuopt = 0 THEN menuopt = 3
    IF menuopt = 4 THEN menuopt = 1
    SELECT CASE menuopt
      CASE 1
        IF DQBloadImage(2, 0, 0, "cg2data\menu2.pcx", Pal, iw, ih) THEN DQBclose: PRINT DQBerror$: END
      CASE 2
        IF DQBloadImage(2, 0, 0, "cg2data\menu3.pcx", Pal, iw, ih) THEN DQBclose: PRINT DQBerror$: END
      CASE 3
        IF DQBloadImage(2, 0, 0, "cg2data\menu4.pcx", Pal, iw, ih) THEN DQBclose: PRINT DQBerror$: END
    END SELECT
  END IF
  IF DQBkey(KEYLEFT) AND menuopt = 2 THEN
    keydelay = maxkeydelay
    mapnumber = mapnumber - 1
    DQBplaySound 14, 1, 22050, ONCE
  END IF
  IF DQBkey(KEYRIGHT) AND menuopt = 2 THEN
    keydelay = maxkeydelay
    mapnumber = mapnumber + 1
    DQBplaySound 14, 1, 22050, ONCE
  END IF
  IF DQBkey(KEYENTER) AND menuopt = 1 THEN EXIT DO
 
  IF DQBkey(KEYENTER) AND menuopt = 3 THEN
    DQBfadeTo 0, 0, 0
    KILL "cg2data\savegame.dat"
    OPEN "cg2data\savegame.dat" FOR OUTPUT AS #1
    PRINT #1, maxscore
    PRINT #1, maxlevelreached
    CLOSE #1
    DQBclose
    END
  END IF

  IF mapnumber = 0 THEN mapnumber = 1
  IF mapnumber > maxlevelreached THEN mapnumber = maxlevelreached
END IF

DQBprint 1, "Maximo puntaje:", 10, 191, 40
DQBprint 1, STR$(mapnumber), 180, 108, 145

DO
LOOP UNTIL DQBframeReady

DQBcopyLayer 1, 0

LOOP


' Seteo de valores iniciales

numplayers = 1
maxshotdelay = 10
missileprecision = .4
missilexspd = 4

FOR t = 1 TO maxplayers
  Player(t).x = 144
  Player(t).y = 160
  Player(t).VelX = 4
  Player(t).VelY = 3
  Player(t).Turnflag = 0
  Player(t).Health = 100
  Player(t).Score = 0
  Player(t).Gunlevel = 0
  Player(t).Invencible = 0
  Player(t).Ammo = 5
  Player(t).Deathflag = 0
NEXT t

FOR t = 1 TO 8
  Enemy(t).x = -32
  Enemy(t).y = 0
  Enemy(t).VelX = 0
  Enemy(t).VelY = 0
  Enemy(t).Userflag = 0
  Enemy(t).Health = 1
  Enemy(t).Kind = 0
  Enemy(t).Powerup = " "
  Enemy(t).BossDeathFlag = 0
NEXT t

FOR t = 1 TO 8
  EShot(t).x = -10
  EShot(t).y = 0
  EShot(t).VelX = 0
  EShot(t).VelY = 0
NEXT t

FOR t = 1 TO maxpshots
  pshot(t).x = -33
  pshot(t).y = 100
  pshot(t).VelY = 0
  pshot(t).Class = 0
NEXT t

FOR t = 1 TO 4
  Missile(t).x = -33
  Missile(t).y = -33
  Missile(t).VelX = 0
  Missile(t).VelY = 0
  Missile(t).Owner = -1
  Missile(t).Ang = 0
  Missile(t).Lockon = 1
NEXT t

FOR t = 1 TO maxdebris
  Debris(t).x = -33
  Debris(t).y = 100
  Debris(t).VelX = 0
  Debris(t).VelY = 0
  Debris(t).Userflag = 0
NEXT t

FOR t = 1 TO 200
  Eventdata(t).Frame = 0
  Eventdata(t).Kind = SPACE$(1)
  Eventdata(t).Buff = SPACE$(40)
  Eventdata(t).x = 0
  Eventdata(t).y = 0
NEXT t

' Ciclo Principal; Cada ciclo es un frame


InicioNivel:

map$ = "mapa" + LTRIM$(RTRIM$(STR$(mapnumber)))

byte = 1
OPEN "cg2data\" + map$ + ".cmp" FOR BINARY AS #1
  GET #1, byte, tilesetfile
  byte = byte + 12
  FOR t = 1 TO 400
    FOR i = 1 TO 10
      GET #1, byte, mapdata(i, t)
      byte = byte + 1
    NEXT i
  NEXT t
CLOSE #1

byte = 1
OPEN "cg2data\" + map$ + ".dat" FOR INPUT AS #1
INPUT #1, boss$
INPUT #1, bosshealth
DO
  INPUT #1, a$
  bvar = INSTR(a$, "_")
  Eventdata(byte).Frame = VAL(LEFT$(a$, bvar - 1))
  bvar2 = INSTR(bvar + 1, a$, "_")
  Eventdata(byte).Kind = MID$(a$, bvar + 1, 1)
  Eventdata(byte).Buff = MID$(a$, bvar + 2, bvar2 - bvar - 2)
  bvar3 = INSTR(bvar2 + 1, a$, "_")
  Eventdata(byte).x = VAL(MID$(a$, bvar2 + 1, bvar3 - bvar2 - 1))
  Eventdata(byte).y = VAL(MID$(a$, bvar3 + 1, LEN(a$) - bvar3))
  IF Eventdata(byte).Kind = "F" THEN EXIT DO
  byte = byte + 1
LOOP
CLOSE #1

IF DQBloadImage(1, 0, 0, "cg2data\" + boss$ + ".pcx", Pal, iw, ih) THEN DQBclose: PRINT DQBerror$: END
IF DQBloadImage(1, 0, 64, "cg2data\" + boss$ + "wk.pcx", Pal, iw, ih) THEN DQBclose: PRINT DQBerror$: END

FOR t = 0 TO 3
  FOR i = 0 TO 2
    DQBget 1, i * 32, t * 32, i * 32 + 31, t * 32 + 31, VARSEG(bosssprites((t * 3 + i) * 514)), VARPTR(bosssprites((t * 3 + i) * 514))
  NEXT i
NEXT t

IF DQBloadImage(1, 0, 32, "cg2data\" + LTRIM$(RTRIM$(tilesetfile)), Pal, iw, ih) THEN DQBclose: PRINT DQBerror$: END

FOR t = 0 TO 1
  FOR i = 0 TO 9
    DQBget 1, i * 32, t * 32 + 32, i * 32 + 31, t * 32 + 32 + 31, VARSEG(tileset((t * 10 + i) * 514)), VARPTR(tileset((t * 10 + i) * 514))
  NEXT i
NEXT t

FOR t = 0 TO 9
  FOR i = 0 TO 7
    rn = ASC(mapdata(t + 1, i + 393)) - 35
    DQBput 2, t * 32, i * 32, VARSEG(tileset(rn * 514)), VARPTR(tileset(rn * 514))
  NEXT i
NEXT t

scrollpos = -31
mappos = 392
curframe = 0
curevent = 1
curtext = 0
curenemy = 1
cureshot = 1
curchan = 1
noharm = 0
levelpassed = 0
nextpshot = 1
nextmissile = 1
nextdebris = 1
rn2 = 0

DQBclearLayer 1

' DQBplaySound 11, 6, 22050, LOOPED

DO

  IF DQBkey(KEYESC) THEN EXIT DO

  DQBcopyLayer 2, 1

  DQBscroll 2, 0, 1

  FOR t = 0 TO 9
    rn = ASC(mapdata(t + 1, mappos)) - 35
    DQBput 2, t * 32, scrollpos, VARSEG(tileset(rn * 514)), VARPTR(tileset(rn * 514))
  NEXT t

  scrollpos = scrollpos + 1
  IF scrollpos = 1 THEN
    scrollpos = -31
    mappos = mappos - 1
    IF mappos = 0 THEN mappos = 392
  END IF

  rn = 0

  FOR t = 1 TO numplayers
    rn = rn + Player(t).Deathflag
    IF Player(t).Deathflag < 300 THEN
     
      IF curframe MOD 2 = 0 THEN
        DQBhPut 1, Player(t).x - ((Player(t).x - 160) * .2), Player(t).y - ((Player(t).y - 100) * .2), VARSEG(plsprites(0)), VARPTR(plsprites(0)), 245
      END IF

      IF Player(t).Turnflag = 0 THEN
        DQBput 1, Player(t).x, Player(t).y, VARSEG(plsprites(0)), VARPTR(plsprites(0))
      ELSEIF Player(t).Turnflag = 1 THEN
        DQBput 1, Player(t).x, Player(t).y, VARSEG(plsprites(1 * 514)), VARPTR(plsprites(1 * 514))
      ELSEIF Player(t).Turnflag = 2 THEN
        DQBput 1, Player(t).x, Player(t).y, VARSEG(plsprites(2 * 514)), VARPTR(plsprites(2 * 514))
      ELSEIF Player(t).Turnflag = 3 THEN
        DQBmPut 1, Player(t).x, Player(t).y, VARSEG(plsprites(2 * 514)), VARPTR(plsprites(2 * 514)), 1
      END IF
    END IF

    IF Player(t).Turnflag = 0 THEN
      Player(t).Turnflag = 1
    ELSEIF Player(t).Turnflag = 1 THEN
      Player(t).Turnflag = 0
    END IF

    IF Player(t).Turnflag > 1 THEN Player(t).Turnflag = 0

    IF Player(t).Shotdelay > 0 THEN Player(t).Shotdelay = Player(t).Shotdelay - 1
    IF DQBkey(KEYUP) AND Player(t).y > 5 THEN Player(t).y = Player(t).y - Player(t).VelY
    IF DQBkey(KEYDOWN) AND Player(t).y < 162 THEN Player(t).y = Player(t).y + Player(t).VelY
    IF DQBkey(KEYLEFT) AND Player(t).x > 0 THEN
      Player(t).x = Player(t).x - Player(t).VelX
      Player(t).Turnflag = 2
    END IF
    IF DQBkey(KEYRIGHT) AND Player(t).x < 283 THEN
      Player(t).x = Player(t).x + Player(t).VelX
      Player(t).Turnflag = 3
    END IF

    ' Cheat. F1 hace invencible, F2, F3 y F4 dan armas 1, 2 y 3
    IF DQBkey(59) AND Player(t).Invencible < 2 AND Player(t).Health > 0 THEN
      IF Player(t).Invencible = 1 THEN
        Player(t).Invencible = 2
      ELSE
        Player(t).Invencible = 3
      END IF
    END IF
    IF (NOT DQBkey(59)) AND Player(t).Invencible > 1 THEN Player(t).Invencible = Player(t).Invencible - 2
    IF DQBkey(60) THEN Player(t).Gunlevel = 0
    IF DQBkey(61) THEN Player(t).Gunlevel = 1
    IF DQBkey(62) THEN Player(t).Gunlevel = 2
    IF DQBkey(63) THEN Player(t).Ammo = 100

    IF missiledelay > 0 THEN missiledelay = missiledelay - 1

    IF DQBkey(KEYSPACE) AND Player(1).Ammo > 0 AND missiledelay = 0 AND Player(t).Health > 0 THEN
      ' Lanza un misil del jugador
      Player(1).Ammo = Player(1).Ammo - 1
      missiledelay = 100
      DQBplaySound 12, curchan, 22050, ONCE

      Missile(nextmissile).x = Player(1).x
      Missile(nextmissile).y = Player(1).y
      Missile(nextmissile).VelX = 0
      Missile(nextmissile).VelY = -1
      Missile(nextmissile).Owner = 0
      Missile(nextmissile).Ang = 0
      Missile(nextmissile).Lockon = 0
      FOR i = 1 TO 8
        Missile(nextmissile).Lockon = Missile(nextmissile).Lockon + Enemy(i).Kind
      NEXT i
      IF Missile(nextmissile).Lockon = 0 THEN
        Missile(nextmissile).Lockon = 1
      ELSE
        DO
          Missile(nextmissile).Lockon = INT(RND * 8 + 1)
        LOOP WHILE Enemy(Missile(nextmissile).Lockon).Kind = 0
      END IF

      nextmissile = nextmissile + 1
      IF nextmissile = 5 THEN nextmissile = 1

    END IF

    IF DQBkey(29) AND Player(t).Shotdelay = 0 AND Player(t).Health > 0 THEN
      pshot(nextpshot).x = Player(t).x
      pshot(nextpshot).y = Player(t).y - 10
      SELECT CASE Player(1).Gunlevel
        CASE 0
          pshot(nextpshot).VelY = 8
          pshot(nextpshot).Class = 0
          DQBplaySound 1, curchan, 22050, ONCE
        CASE 1
          pshot(nextpshot).VelY = 12
          pshot(nextpshot).Class = 1
          DQBplaySound 7, curchan, 22050, ONCE
        CASE 2
          pshot(nextpshot).VelY = 16
          pshot(nextpshot).Class = 2
          DQBplaySound 8, curchan, 22050, ONCE
      END SELECT
      curchan = curchan + 1
      IF curchan = 5 THEN curchan = 1
      nextpshot = nextpshot + 1
      IF nextpshot > maxpshots THEN nextpshot = 1
      Player(t).Shotdelay = maxshotdelay - Player(1).Gunlevel
    END IF
    ' REMOVER EL SIGUIENTE IF!!!!!!!!!!!!!!!!!!!
    ' IF DQBkey(KEYSPACE) THEN Player(1).Health = Player(1).Health - 1

    IF DQBkey(25) THEN        ' Pausa
      DQBplaySound 5, curchan, 22050, ONCE
      curchan = curchan + 1
      IF curchan = 5 THEN curchan = 1
      DO
      LOOP UNTIL NOT DQBkey(25)
      DO
      LOOP UNTIL DQBkey(25)
      DO
      LOOP UNTIL NOT DQBkey(25)
    END IF

    IF Player(t).Health <= 0 THEN
      Player(t).Health = 0
      IF Player(t).Deathflag = 0 THEN Player(t).Deathflag = 1
    END IF

    IF Player(t).Deathflag > 0 THEN
      IF Player(t).Deathflag < 300 THEN
        Debris(nextdebris).x = Player(t).x + RND * 50 - 25
        Debris(nextdebris).y = Player(t).y + RND * 50 - 25
        Debris(nextdebris).VelX = 0
        Debris(nextdebris).VelY = 3
        Debris(nextdebris).Userflag = 0
        nextdebris = nextdebris + 1
        IF nextdebris > maxdebris THEN nextdebris = 1
      END IF
      IF Player(t).Deathflag = 299 THEN
        DQBplaySound 4, 5, 22050, ONCE
        FOR i = 1 TO 20
          Debris(nextdebris).x = Player(t).x + 12
          Debris(nextdebris).y = Player(t).y + 12
          Debris(nextdebris).VelX = RND * 10 - 5
          Debris(nextdebris).VelY = RND * 10 - 3
          Debris(nextdebris).Userflag = INT(RND * 9) + 20
          nextdebris = nextdebris + 1
          IF nextdebris > maxdebris THEN nextdebris = 1
        NEXT i
      END IF
      Player(t).Deathflag = Player(t).Deathflag + 1
      IF Player(t).Deathflag > 300 THEN Player(t).Deathflag = 300
    END IF

    IF Player(t).Invencible > 0 THEN Player(t).Health = 100
  NEXT t

  IF rn = 300 * numplayers THEN
    DQBfadeStepTo 63, 63, 63
    rn2 = rn2 + 1
    IF rn2 = 100 THEN EXIT DO
  END IF

  FOR t = 1 TO maxdebris
    IF Debris(t).Userflag < 18 THEN
      DQBput 1, INT(Debris(t).x), INT(Debris(t).y), VARSEG(explsprites(INT(Debris(t).Userflag / 3) * 514)), VARPTR(explsprites(INT(Debris(t).Userflag / 3) * 514))
      Debris(t).Userflag = Debris(t).Userflag + 1
      IF Debris(t).Userflag = 1 AND Debris(t).x <> -33 THEN
        IF Player(1).Health > 0 AND Enemy(1).BossDeathFlag = 0 THEN
          DQBplaySound 2, curchan, 22050, ONCE
        ELSE
          IF INT(RND * 10) = 0 THEN DQBplaySound 2, curchan, 22050, ONCE
        END IF
      END IF
      curchan = curchan + 1
      IF curchan = 5 THEN curchan = 1
      IF Debris(t).Userflag = 18 THEN
        Debris(t).x = -33
        Debris(t).y = 100
        Debris(t).VelX = 0
        Debris(t).VelY = 0
        Debris(t).Userflag = 0
      END IF
    END IF
    IF Debris(t).Userflag > 19 AND Debris(t).Userflag < 29 THEN
      DQBput 1, INT(Debris(t).x), INT(Debris(t).y), VARSEG(debrsprites(INT((Debris(t).Userflag - 20) / 3 + 3) * 34)), VARPTR(debrsprites(INT((Debris(t).Userflag - 20) / 3 + 3) * 34))
      Debris(t).Userflag = Debris(t).Userflag + 1
      IF Debris(t).Userflag = 29 THEN Debris(t).Userflag = 20
      IF Debris(t).VelX + Debris(t).VelY < .05 THEN
        Debris(t).x = -33
        Debris(t).y = 100
        Debris(t).VelX = 0
        Debris(t).VelY = 0
        Debris(t).Userflag = 0
      END IF
      IF Debris(t).Userflag = 22 OR Debris(t).Userflag = 27 THEN
        Debris(nextdebris).x = Debris(t).x
        Debris(nextdebris).y = Debris(t).y
        Debris(nextdebris).Userflag = 30
        Debris(nextdebris).VelX = 0
        Debris(nextdebris).VelY = 1
        nextdebris = nextdebris + 1
        IF nextdebris > maxdebris THEN nextdebris = 1
      END IF
      ' Debris(t).VelX = Debris(t).VelX * .9
      ' Debris(t).VelY = Debris(t).VelY * .9
    END IF
    IF Debris(t).Userflag > 29 AND Debris(t).Userflag < 57 THEN
      DQBput 1, INT(Debris(t).x), INT(Debris(t).y), VARSEG(debrsprites(INT((Debris(t).Userflag - 30) / 9) * 34)), VARPTR(debrsprites(INT((Debris(t).Userflag - 30) / 9) * 34))
      Debris(t).Userflag = Debris(t).Userflag + 1
      IF Debris(t).Userflag = 57 THEN
        Debris(t).x = -33
        Debris(t).y = 100
        Debris(t).VelX = 0
        Debris(t).VelY = 0
        Debris(t).Userflag = 0
      END IF
    END IF
    IF Debris(t).Userflag > 59 AND Debris(t).Userflag < 68 THEN
      SELECT CASE Debris(t).Userflag
        CASE 60 TO 61
          DQBput 1, INT(Debris(t).x), INT(Debris(t).y), VARSEG(explsprites(6 * 514)), VARPTR(explsprites(6 * 514))
        CASE 62 TO 63
          DQBput 1, INT(Debris(t).x), INT(Debris(t).y), VARSEG(explsprites(7 * 514)), VARPTR(explsprites(7 * 514))
        CASE 64 TO 65
          DQBmPut 1, INT(Debris(t).x), INT(Debris(t).y), VARSEG(explsprites(6 * 514)), VARPTR(explsprites(6 * 514)), 1
        CASE 66 TO 67
          DQBmPut 1, INT(Debris(t).x), INT(Debris(t).y), VARSEG(explsprites(7 * 514)), VARPTR(explsprites(7 * 514)), 1
      END SELECT
      Debris(t).Userflag = Debris(t).Userflag + 1
      IF Debris(t).Userflag = 68 THEN
        Debris(t).x = -33
        Debris(t).y = 100
        Debris(t).VelX = 0
        Debris(t).VelY = 0
        Debris(t).Userflag = 0
      END IF
    END IF
    IF Debris(t).Userflag > 69 AND Debris(t).Userflag < 80 THEN
      DQBput 1, INT(Debris(t).x), INT(Debris(t).y), VARSEG(debrsprites(7 * 34)), VARPTR(debrsprites(7 * 34))
      Debris(t).Userflag = Debris(t).Userflag + 1
      IF Debris(t).Userflag = 80 THEN
        Debris(t).x = -33
        Debris(t).y = 100
        Debris(t).VelX = 0
        Debris(t).VelY = 0
        Debris(t).Userflag = 0
      END IF
    END IF
    Debris(t).x = Debris(t).x + Debris(t).VelX
    Debris(t).y = Debris(t).y + Debris(t).VelY
  NEXT t

  FOR t = 1 TO 4
    ' Rutina de los misiles
    DQBrPut 1, Missile(t).x, Missile(t).y, VARSEG(plsprites(8 * 514)), VARPTR(plsprites(8 * 514)), Missile(t).Ang, 100

    Missile(t).x = Missile(t).x + Missile(t).VelX
    Missile(t).y = Missile(t).y + Missile(t).VelY

    IF Missile(t).Owner > -1 THEN
      IF Missile(t).y < -62 THEN
        Missile(t).x = -33
        Missile(t).y = -33
        Missile(t).VelX = 0
        Missile(t).VelY = 0
        Missile(t).Owner = -1
        Missile(t).Ang = 0
        Missile(t).Lockon = 1
      END IF

      IF Missile(t).VelY > -5 THEN Missile(t).VelY = Missile(t).VelY - .1
    
      IF Enemy(Missile(t).Lockon).Kind <> 0 THEN
        IF Missile(t).x > Enemy(Missile(t).Lockon).x THEN
          Missile(t).VelX = Missile(t).VelX - missileprecision
          IF Missile(t).VelX < -missilexspd THEN Missile(t).VelX = -missilexspd
        END IF

        IF Missile(t).x < Enemy(Missile(t).Lockon).x THEN
          Missile(t).VelX = Missile(t).VelX + .2
          IF Missile(t).VelX > missilexspd THEN Missile(t).VelX = missilexspd
        END IF
      END IF
      Missile(t).Ang = INT(Missile(t).VelX * 8)
      IF Missile(t).Ang < 0 THEN Missile(t).Ang = Missile(t).Ang + 255

      Debris(nextdebris).x = Missile(t).x + 12
      Debris(nextdebris).y = Missile(t).y + 12
      Debris(nextdebris).VelX = 0
      Debris(nextdebris).VelY = 2
      Debris(nextdebris).Userflag = 30
      nextdebris = nextdebris + 1
      IF nextdebris > maxdebris THEN nextdebris = 1

    END IF

  NEXT t

  FOR t = 1 TO 8
    SELECT CASE Enemy(t).Kind

      CASE 1
        DQBput 1, INT(Enemy(t).x), INT(Enemy(t).y), VARSEG(enemysprites(Enemy(t).Userflag * 514)), VARPTR(enemysprites(Enemy(t).Userflag * 514))
 
      CASE 2
        SELECT CASE Enemy(t).Userflag
          CASE 0 TO 4
            DQBput 1, INT(Enemy(t).x), INT(Enemy(t).y), VARSEG(enemysprites(2 * 514)), VARPTR(enemysprites(2 * 514))
          CASE 5 TO 9
            DQBput 1, INT(Enemy(t).x), INT(Enemy(t).y), VARSEG(enemysprites(3 * 514)), VARPTR(enemysprites(3 * 514))
          CASE 10 TO 14
            DQBput 1, INT(Enemy(t).x), INT(Enemy(t).y), VARSEG(enemysprites(4 * 514)), VARPTR(enemysprites(4 * 514))
        END SELECT

      CASE 3
        SELECT CASE Enemy(t).Userflag
          CASE 0 TO 1
            DQBput 1, INT(Enemy(t).x), INT(Enemy(t).y), VARSEG(enemysprites((5 + Enemy(t).Userflag) * 514)), VARPTR(enemysprites((5 + Enemy(t).Userflag) * 514))
          CASE 2 TO 3
            DQBmPut 1, INT(Enemy(t).x), INT(Enemy(t).y), VARSEG(enemysprites((3 + Enemy(t).Userflag) * 514)), VARPTR(enemysprites((3 + Enemy(t).Userflag) * 514)), 1
        END SELECT

      CASE 4
        DQBmPut 1, INT(Enemy(t).x), INT(Enemy(t).y), VARSEG(enemysprites(Enemy(t).Userflag * 514)), VARPTR(enemysprites(Enemy(t).Userflag * 514)), 2

      CASE 5
        DQBrPut 1, INT(Enemy(t).x), INT(Enemy(t).y), VARSEG(enemysprites(7 * 514)), VARPTR(enemysprites(7 * 514)), DQBangle(Enemy(t).x, Enemy(t).y, Player(1).x, Player(1).y), 100
   
      CASE 6
        IF curframe MOD 2 = 1 THEN
          DQBrPut 1, INT(Enemy(t).x), INT(Enemy(t).y), VARSEG(enemysprites(8 * 514)), VARPTR(enemysprites(8 * 514)), Enemy(t).Userflag, 100
        ELSE
          DQBrPut 1, INT(Enemy(t).x), INT(Enemy(t).y), VARSEG(enemysprites(9 * 514)), VARPTR(enemysprites(9 * 514)), Enemy(t).Userflag, 100
        END IF

      CASE 7
        DQBrPut 1, INT(Enemy(t).x), INT(Enemy(t).y), VARSEG(enemysprites(10 * 514)), VARPTR(enemysprites(10 * 514)), Enemy(t).Userflag, 100

      CASE 10 TO 21
        DQBput 1, INT(Enemy(t).x), INT(Enemy(t).y), VARSEG(bosssprites((Enemy(t).Kind - 10) * 514)), VARPTR(bosssprites((Enemy(t).Kind - 10) * 514))

      CASE 100
        DQBsPut 1, INT(Enemy(t).x - ((Enemy(t).Userflag / 2) - 16)), INT(Enemy(t).y - ((Enemy(t).Userflag / 2) - 16)), VARSEG(plsprites(6 * 514)), VARPTR(plsprites(6 * 514)), Enemy(t).Userflag, Enemy(t).Userflag
        Enemy(t).Userflag = Enemy(t).Userflag - 1
        IF Enemy(t).Userflag < 25 THEN Enemy(t).Userflag = 40
  
      CASE 101
        DQBsPut 1, INT(Enemy(t).x - ((Enemy(t).Userflag / 2) - 16)), INT(Enemy(t).y - ((Enemy(t).Userflag / 2) - 16)), VARSEG(plsprites(7 * 514)), VARPTR(plsprites(7 * 514)), Enemy(t).Userflag, Enemy(t).Userflag
        Enemy(t).Userflag = Enemy(t).Userflag + 1
        IF Enemy(t).Userflag > 40 THEN Enemy(t).Userflag = 25

      CASE 102
        DQBsPut 1, INT(Enemy(t).x - ((Enemy(t).Userflag / 2) - 16)), INT(Enemy(t).y - ((Enemy(t).Userflag / 2) - 16)), VARSEG(plsprites(9 * 514)), VARPTR(plsprites(9 * 514)), Enemy(t).Userflag, Enemy(t).Userflag
        Enemy(t).Userflag = Enemy(t).Userflag + 1
        IF Enemy(t).Userflag > 40 THEN Enemy(t).Userflag = 25

    END SELECT

    IF Enemy(t).Kind < 10 THEN
      ON Enemy(t).Kind GOSUB AI1, AI2, AI3, AI4, AI5, AI6, AI7
    END IF

    IF Enemy(t).Kind > 9 AND Enemy(t).Kind < 22 AND t = 1 THEN
      GOSUB AIBoss
    END IF

    IF Enemy(t).BossDeathFlag > 0 THEN Enemy(t).BossDeathFlag = Enemy(t).BossDeathFlag + 1
    IF Enemy(t).BossDeathFlag = 400 THEN EXIT DO

    IF Enemy(t).Kind = 16 THEN
      IF Enemy(2).Kind = 17 AND Enemy(3).Kind = 18 AND Enemy(4).Kind = 19 AND Enemy(5).Kind = 20 AND Enemy(6).Kind = 21 THEN
        Debris(nextdebris).x = Enemy(t).x + RND * 84 - 10
        Debris(nextdebris).y = Enemy(t).y + RND * 52 - 10
        Debris(nextdebris).VelX = 0
        Debris(nextdebris).VelY = -1
        Debris(nextdebris).Userflag = 0
        nextdebris = nextdebris + 1
        IF nextdebris > maxdebris THEN nextdebris = 1
        Enemy(1).Userflag = 3
        Enemy(1).VelX = 0
        Enemy(1).VelY = .2
        IF Enemy(1).BossDeathFlag = 0 THEN Enemy(1).BossDeathFlag = 1

        IF Enemy(1).BossDeathFlag = 300 THEN
          DQBplaySound 11, curchan, 22050, ONCE
          curchan = curchan + 1
          IF curchan = 5 THEN curchan = 1
          levelpassed = 1
          FOR i = 1 TO 10
            Debris(nextdebris).x = Enemy(1).x + 44
            Debris(nextdebris).y = Enemy(1).y + 28
            Debris(nextdebris).VelX = RND * 10 - 5
            Debris(nextdebris).VelY = RND * 10 - 3
            Debris(nextdebris).Userflag = INT(RND * 9) + 20
            nextdebris = nextdebris + 1
            IF nextdebris > maxdebris THEN nextdebris = 1
          NEXT i
          FOR i = 1 TO 6
            Enemy(i).x = -32
            Enemy(i).y = 0
            Enemy(i).VelX = 0
            Enemy(i).VelY = 0
            Enemy(i).Userflag = 0
            Enemy(i).Health = 1
            Enemy(t).Kind = 0
          NEXT i
        END IF

      END IF
    END IF
   
    Enemy(t).x = Enemy(t).x + Enemy(t).VelX
    Enemy(t).y = Enemy(t).y + Enemy(t).VelY
 
    IF Enemy(t).x > 321 OR Enemy(t).x < -33 OR Enemy(t).y > 201 OR Enemy(t).y < -33 THEN
      IF Enemy(t).Kind < 10 OR Enemy(t).Kind > 15 THEN
        Enemy(t).x = -32
        Enemy(t).y = 0
        Enemy(t).VelX = 0
        Enemy(t).VelY = 0
        Enemy(t).Userflag = 0
        Enemy(t).Health = 1
        Enemy(t).Kind = 0
      END IF
    END IF

    IF Enemy(t).Health > 0 THEN
      FOR i = 1 TO maxpshots
        IF Enemy(t).Kind > 0 AND Enemy(t).Kind < 16 AND pshot(i).x > 0 AND pshot(i).x > Enemy(t).x - 24 AND pshot(i).x < Enemy(t).x + 24 AND pshot(i).y > Enemy(t).y - 16 AND pshot(i).y < Enemy(t).y + 16 THEN
          Enemy(t).Health = Enemy(t).Health - (pshot(i).Class + 1)
          FOR exb = 1 TO 4
            bmx = Enemy(t).x + 16 + (RND * 200 - 100)
            bmy = Enemy(t).y + 16 + (RND * 200 - 100)
            DQBtri 1, Enemy(t).x + 16, Enemy(t).y + 16, bmx + RND * 10 - 5, bmy + RND * 10 - 5, bmx + RND * 10 - 5, bmy + RND * 10 - 5, 255
          NEXT exb
          DQBplaySound 3, curchan, 22050, ONCE
          curchan = curchan + 1
          IF curchan = 5 THEN curchan = 1
          Debris(nextdebris).x = pshot(i).x
          Debris(nextdebris).y = pshot(i).y
          Debris(nextdebris).VelX = 0
          Debris(nextdebris).VelY = 0
          Debris(nextdebris).Userflag = 60
          nextdebris = nextdebris + 1
          IF nextdebris > maxdebris THEN nextdebris = 1
          pshot(i).x = -33
          pshot(i).y = 100
          pshot(i).VelY = 0
          pshot(i).Class = 0
        END IF
      NEXT i

      FOR i = 1 TO 4
        IF Enemy(t).Kind > 0 AND Enemy(t).Kind < 16 AND Missile(i).x > Enemy(t).x - 30 AND Missile(i).x < Enemy(t).x + 30 AND Missile(i).y > Enemy(t).y - 30 AND Missile(i).y < Enemy(t).y + 30 THEN
          Enemy(t).Health = Enemy(t).Health - 20
          DQBplaySound 3, curchan, 22050, ONCE
          curchan = curchan + 1
          IF curchan = 5 THEN curchan = 1
          FOR i1 = 1 TO 10
            Debris(nextdebris).x = Missile(i).x + INT(RND * 60 - 30)
            Debris(nextdebris).y = Missile(i).y + INT(RND * 60 - 30)
            Debris(nextdebris).VelX = 0
            Debris(nextdebris).VelY = -2
            Debris(nextdebris).Userflag = 0
            nextdebris = nextdebris + 1
            IF nextdebris > maxdebris THEN nextdebris = 1
          NEXT i1
          Missile(i).x = -33
          Missile(i).y = -33
          Missile(i).VelX = 0
          Missile(i).VelY = 0
          Missile(i).Owner = -1
          Missile(i).Ang = 0
          Missile(i).Lockon = 1
        END IF
      NEXT i

    END IF

    IF Enemy(t).Health <= 0 THEN
      Debris(nextdebris).x = Enemy(t).x + RND * 20 - 10
      Debris(nextdebris).y = Enemy(t).y + RND * 20 - 10
      Debris(nextdebris).VelX = 0
      Debris(nextdebris).VelY = 1
      Debris(nextdebris).Userflag = 0
      nextdebris = nextdebris + 1
      IF nextdebris > maxdebris THEN nextdebris = 1

      Enemy(t).Health = Enemy(t).Health - 1
      IF Enemy(t).Health <= -6 THEN
        FOR i = 1 TO 5
          Debris(nextdebris).x = Enemy(t).x + 12
          Debris(nextdebris).y = Enemy(t).y + 12
          Debris(nextdebris).VelX = RND * 10 - 5
          Debris(nextdebris).VelY = RND * 10 - 3
          Debris(nextdebris).Userflag = INT(RND * 9) + 20
          nextdebris = nextdebris + 1
          IF nextdebris > maxdebris THEN nextdebris = 1
        NEXT i
       
        SELECT CASE Enemy(t).Kind
          CASE 1
            Player(1).Score = Player(1).Score + 1500
          CASE 2
            Player(1).Score = Player(1).Score + 3000
          CASE 3
            Player(1).Score = Player(1).Score + 3500
          CASE 4
            Player(1).Score = Player(1).Score + 5000
          CASE 5
            Player(1).Score = Player(1).Score + 6000
          CASE 6
            Player(1).Score = Player(1).Score + 2500
          CASE 7
            Player(1).Score = Player(1).Score + 7000
          CASE 10 TO 15
            Player(1).Score = Player(1).Score + 10000

        END SELECT

        IF Enemy(t).Powerup = "P" THEN
          Enemy(curenemy).x = Enemy(t).x
          Enemy(curenemy).y = Enemy(t).y
          Enemy(curenemy).VelX = 0
          Enemy(curenemy).VelY = 1
          Enemy(curenemy).Userflag = 32
          Enemy(curenemy).Health = 100
          Enemy(curenemy).Kind = 100
          curenemy = curenemy + 1
          IF curenemy = 9 THEN curenemy = 1
        END IF

        IF Enemy(t).Powerup = "H" THEN
          Enemy(curenemy).x = Enemy(t).x
          Enemy(curenemy).y = Enemy(t).y
          Enemy(curenemy).VelX = 0
          Enemy(curenemy).VelY = 1
          Enemy(curenemy).Userflag = 32
          Enemy(curenemy).Health = 100
          Enemy(curenemy).Kind = 101
          curenemy = curenemy + 1
          IF curenemy = 9 THEN curenemy = 1
        END IF

        IF Enemy(t).Powerup = "M" THEN
          Enemy(curenemy).x = Enemy(t).x
          Enemy(curenemy).y = Enemy(t).y
          Enemy(curenemy).VelX = 0
          Enemy(curenemy).VelY = 1
          Enemy(curenemy).Userflag = 32
          Enemy(curenemy).Health = 100
          Enemy(curenemy).Kind = 102
          curenemy = curenemy + 1
          IF curenemy = 9 THEN curenemy = 1
        END IF

        IF Enemy(t).Kind > 9 AND Enemy(t).Kind < 16 THEN
          Enemy(t).Kind = Enemy(t).Kind + 6
          Enemy(t).Health = 1
        ELSE
          Enemy(t).x = -32
          Enemy(t).y = 0
          Enemy(t).VelX = 0
          Enemy(t).VelY = 0
          Enemy(t).Userflag = 0
          Enemy(t).Health = 1
          Enemy(t).Kind = 0
        END IF
      END IF
    END IF

    IF INT(RND * 40) = 0 AND Enemy(t).Kind > 0 AND Enemy(t).Kind < 16 AND EShot(cureshot).x = -10 THEN
      DistX = ABS(Enemy(t).x - Player(1).x)
      DistY = ABS(Enemy(t).y - Player(1).y)
      IF DistX > DistY THEN
        EShot(cureshot).VelX = 3
        EShot(cureshot).VelY = DistY / (DistX / 3)
        EShot(cureshot).x = Enemy(t).x + 12
        EShot(cureshot).y = Enemy(t).y + 12
      ELSE
        EShot(cureshot).VelY = 3
        EShot(cureshot).VelX = DistX / (DistY / 3)
        EShot(cureshot).x = Enemy(t).x + 12
        EShot(cureshot).y = Enemy(t).y + 12
      END IF

      EShot(cureshot).Ang = DQBangle(Player(1).x, Player(1).y, Enemy(t).x, Enemy(t).y)
     
      IF Enemy(t).x > Player(1).x THEN EShot(cureshot).VelX = EShot(cureshot).VelX * -1
      IF Enemy(t).y > Player(1).y THEN EShot(cureshot).VelY = EShot(cureshot).VelY * -1

      cureshot = cureshot + 1
      IF cureshot = 9 THEN cureshot = 1
    END IF

    IF (Enemy(t).Kind < 16 OR Enemy(t).Kind > 99) AND Enemy(t).x > Player(1).x - 16 AND Enemy(t).x < Player(1).x + 16 AND Enemy(t).y > Player(1).y - 16 AND Enemy(t).y < Player(1).y + 16 THEN
      IF noharm = 0 AND Enemy(t).Kind < 100 THEN
        noharm = 10
        Player(1).Health = Player(1).Health - 30
        Debris(nextdebris).x = Player(1).x + 12
        Debris(nextdebris).y = Player(1).y + 12
        Debris(nextdebris).VelX = RND * 10 - 5
        Debris(nextdebris).VelY = RND * 10 - 3
        Debris(nextdebris).Userflag = INT(RND * 9) + 20
        nextdebris = nextdebris + 1
        IF nextdebris > maxdebris THEN nextdebris = 1
        Enemy(t).Health = Enemy(t).Health - 5
      END IF
      IF Enemy(t).Kind = 100 THEN
        Player(1).Gunlevel = Player(1).Gunlevel + 1
        IF Player(1).Gunlevel = 3 THEN Player(1).Gunlevel = 2
        Enemy(t).x = -32
        Enemy(t).y = 0
        Enemy(t).VelX = 0
        Enemy(t).VelY = 0
        Enemy(t).Userflag = 0
        Enemy(t).Health = 1
        Enemy(t).Kind = 0
        DQBplaySound 9, curchan, 22050, ONCE
        curchan = curchan + 1
        IF curchan = 5 THEN curchan = 1
      END IF
      IF Enemy(t).Kind = 101 AND Player(1).Health > 0 THEN
        Player(1).Health = Player(1).Health + 20
        IF Player(1).Health > 100 THEN Player(1).Health = 100
        Enemy(t).x = -32
        Enemy(t).y = 0
        Enemy(t).VelX = 0
        Enemy(t).VelY = 0
        Enemy(t).Userflag = 0
        Enemy(t).Health = 1
        Enemy(t).Kind = 0
        DQBplaySound 10, curchan, 22050, ONCE
        curchan = curchan + 1
        IF curchan = 5 THEN curchan = 1
      END IF
      IF Enemy(t).Kind = 102 THEN
        IF Player(1).Ammo < 10 THEN Player(1).Ammo = Player(1).Ammo + 1
        Enemy(t).x = -32
        Enemy(t).y = 0
        Enemy(t).VelX = 0
        Enemy(t).VelY = 0
        Enemy(t).Userflag = 0
        Enemy(t).Health = 1
        Enemy(t).Kind = 0
        DQBplaySound 13, curchan, 22050, ONCE
        curchan = curchan + 1
        IF curchan = 5 THEN curchan = 1
      END IF
   
    END IF

  NEXT t

  FOR t = 1 TO maxpshots
    SELECT CASE pshot(t).Class
      CASE 0
        DQBput 1, pshot(t).x, pshot(t).y, VARSEG(plsprites(3 * 514)), VARPTR(plsprites(3 * 514))
      CASE 1
        DQBput 1, pshot(t).x, pshot(t).y, VARSEG(plsprites(4 * 514)), VARPTR(plsprites(4 * 514))
      CASE 2
       DQBput 1, pshot(t).x, pshot(t).y, VARSEG(plsprites(5 * 514)), VARPTR(plsprites(5 * 514))
    END SELECT
    pshot(t).y = pshot(t).y - pshot(t).VelY
    IF pshot(t).y < -33 THEN
      pshot(t).x = -33
      pshot(t).y = 100
      pshot(t).VelY = 0
      pshot(t).Class = 0
    END IF
    IF pshot(t).Class = 2 THEN
      Debris(nextdebris).x = pshot(t).x + RND * 24
      Debris(nextdebris).y = pshot(t).y + RND * 24
      Debris(nextdebris).VelX = 0
      Debris(nextdebris).VelY = -1
      Debris(nextdebris).Userflag = 70
      nextdebris = nextdebris + 1
      IF nextdebris > maxdebris THEN nextdebris = 1
    END IF
  NEXT t

  FOR t = 1 TO 8
    DQBrPut 1, INT(EShot(t).x), INT(EShot(t).y), VARSEG(debrsprites(204)), VARPTR(debrsprites(204)), EShot(t).Ang, 100
    EShot(t).x = EShot(t).x + EShot(t).VelX
    EShot(t).y = EShot(t).y + EShot(t).VelY
    IF EShot(t).x < -11 OR EShot(t).x > 321 OR EShot(t).y < -9 OR EShot(t).y > 201 THEN
      EShot(t).x = -10
      EShot(t).y = 0
      EShot(t).VelX = 0
      EShot(t).VelY = 0
    END IF
    IF noharm = 0 AND EShot(t).x > Player(1).x AND EShot(t).x < Player(1).x + 24 AND EShot(t).y > Player(1).y AND EShot(t).y < Player(1).y + 24 THEN
      noharm = 10
      DQBplaySound 3, curchan, 22050, ONCE
      curchan = curchan + 1
      IF curchan = 5 THEN curchan = 1
      Player(1).Health = Player(1).Health - 15
      Debris(nextdebris).x = EShot(t).x
      Debris(nextdebris).y = EShot(t).y
      Debris(nextdebris).VelX = RND * 10 - 5
      Debris(nextdebris).VelY = RND * 10 - 3
      Debris(nextdebris).Userflag = INT(RND * 9) + 20
      nextdebris = nextdebris + 1
      IF nextdebris > maxdebris THEN nextdebris = 1
      EShot(t).x = -10
      EShot(t).y = 0
      EShot(t).VelX = 0
      EShot(t).VelY = 0
    END IF
  NEXT t

  IF noharm > 0 THEN noharm = noharm - 1

  FOR t = 1 TO numplayers
    DQBprint 1, "Energia P" + STR$(t) + " :", 10, t * 10, 255
    DQBprint 1, STR$(Player(t).Health) + "%", 100, t * 10, 145
    DQBprint 1, STR$(Player(t).Score), 200, t * 10, 40
    DQBprint 1, "Arma Nivel" + STR$(Player(t).Gunlevel + 1), 10, t * 10 + 8, 125
    DQBprint 1, "Misiles :" + STR$(Player(t).Ammo), 208, t * 10 + 8, 125
    IF noharm <> 0 OR Player(t).Invencible = 1 THEN DQBprint 1, "ESCUDO", 140, t * 10, 160
  NEXT t

  IF curtext > 0 THEN
    curtext = curtext - 1
    DQBprint 1, textt$, textx, texty, 50
  END IF

  IF Eventdata(curevent).Frame = curframe THEN
    IF Eventdata(curevent).Kind = "T" THEN
      DQBplaySound 6, curchan, 22050, ONCE
      curchan = curchan + 1
      IF curchan = 5 THEN curchan = 1
      textx = Eventdata(curevent).x
      texty = Eventdata(curevent).y
      textt$ = Eventdata(curevent).Buff
      curtext = 100
    END IF
    IF Eventdata(curevent).Kind = "F" THEN         ' El Jefe aparece!!
      FOR t = 1 TO 6
        IF t < 4 THEN
          Enemy(t).x = 116 + (t - 1) * 32
          Enemy(t).y = 200
        ELSE
          Enemy(t).x = 116 + (t - 4) * 32
          Enemy(t).y = 232
        END IF
        Enemy(t).Kind = 9 + t
        Enemy(t).Powerup = ""
        Enemy(t).VelX = 0
        Enemy(t).VelY = -1
        Enemy(t).Userflag = 0
        Enemy(t).Health = bosshealth
      NEXT t
    END IF

    IF VAL(Eventdata(curevent).Kind) >= 1 AND VAL(Eventdata(curevent).Kind) <= 9 THEN
      Enemy(curenemy).x = Eventdata(curevent).x
      Enemy(curenemy).y = Eventdata(curevent).y
      Enemy(curenemy).Kind = VAL(Eventdata(curevent).Kind)
      Enemy(curenemy).Powerup = LEFT$(Eventdata(curevent).Buff, 1)
      SELECT CASE Enemy(curenemy).Kind
       
        CASE 1
          Enemy(curenemy).VelX = 0
          Enemy(curenemy).VelY = 0
          Enemy(curenemy).Userflag = 0
          Enemy(curenemy).Health = 1

        CASE 2
          IF Enemy(curenemy).x < 144 THEN
            Enemy(curenemy).VelX = 1
          ELSE
            Enemy(curenemy).VelX = -1
          END IF
          Enemy(curenemy).VelY = 4
          Enemy(curenemy).Userflag = 0
          Enemy(curenemy).Health = 2

        CASE 3
          IF Enemy(curenemy).x < 144 THEN
            Enemy(curenemy).VelX = 1.5
            Enemy(curenemy).Userflag = 2
          ELSE
            Enemy(curenemy).VelX = -1.5
            Enemy(curenemy).Userflag = 0
          END IF
          Enemy(curenemy).VelY = 0
          Enemy(curenemy).Health = 2

        CASE 4
          Enemy(curenemy).VelX = 0
          Enemy(curenemy).VelY = 0
          Enemy(curenemy).Userflag = 0
          Enemy(curenemy).Health = 1

        CASE 5
          Enemy(curenemy).VelX = 0
          Enemy(curenemy).VelY = 1
          Enemy(curenemy).Userflag = 0
          Enemy(curenemy).Health = 3

        CASE 6
          IF Enemy(curenemy).x < 144 THEN
            Enemy(curenemy).VelX = 3.5
            Enemy(curenemy).Userflag = 192
          ELSE
            Enemy(curenemy).VelX = -3.5
            Enemy(curenemy).Userflag = 64
          END IF
          Enemy(curenemy).VelY = 0
          Enemy(curenemy).Health = 1

        CASE 7
          IF Enemy(curenemy).x < 144 THEN
            Enemy(curenemy).VelX = 4
          ELSE
            Enemy(curenemy).VelX = -4
          END IF
          Enemy(curenemy).VelY = 4
          Enemy(curenemy).Health = 1
          Enemy(curenemy).Userflag = 255

      END SELECT
      curenemy = curenemy + 1
      IF curenemy = 9 THEN curenemy = 1
    END IF

    curevent = curevent + 1
  END IF

  DO
  LOOP UNTIL DQBframeReady = TRUE
 
  DQBcopyLayer 1, 0
  curframe = curframe + 1
  IF curframe > 32760 THEN curframe = 32760

LOOP

DQBfadeTo 0, 0, 0

IF Player(1).Score > maxscore THEN maxscore = Player(1).Score

IF levelpassed = 0 THEN
  ' Moriste. Hacer rutinas de Game Over despu‚s.
  KILL "cg2data\savegame.dat"
  OPEN "cg2data\savegame.dat" FOR OUTPUT AS #1
  PRINT #1, maxscore
  PRINT #1, maxlevelreached
  CLOSE #1

  GOTO MenuPrincipal
END IF

mapnumber = mapnumber + 1

OPEN "cg2data\mapa" + LTRIM$(RTRIM$(STR$(mapnumber))) + ".dat" FOR RANDOM AS #1
IF LOF(1) = 0 THEN
  CLOSE #1
  KILL "cg2data\mapa" + LTRIM$(RTRIM$(STR$(mapnumber))) + ".dat"
 
mapnumber = mapnumber - 1

  ' Esto es Game Over porque no hay m s niveles. Hacer algo bonito.
  DQBclearLayer 0

  DQBsetPal Pal

  IF DQBloadImage(1, 0, 0, "cg2data\final.pcx", Pal, iw, ih) THEN DQBclose: PRINT DQBerror$: END

  DQBprint 1, "CONGENERATION 2", 20, 10, 50
  DQBprint 1, "Desarrollado usando las librerias DirectQB", 20, 30, 125
  DQBprint 1, "creadas por Angelo Mottola.", 20, 40, 125

  DQBprint 1, "Programacion : Jaime de los Hoyos M.", 20, 60, 125
  DQBprint 1, "Arte : Vicente de los Hoyos M.", 20, 70, 125
  DQBprint 1, "Agradecimientos a :", 20, 80, 125
  DQBprint 1, "Francisca de los Hoyos M.", 20, 90, 125

  DQBprint 1, "jhoyos@entelchile.net", 20, 110, 125

  DQBprint 1, "Presione ENTER para seguir.", 20, 150, 50

  DQBcopyLayer 1, 0

  DO
  LOOP UNTIL DQBkey(KEYENTER)

  DQBfadeTo 0, 0, 0

  DQBclearLayer 0
  DQBsetPal Pal

  KILL "cg2data\savegame.dat"
  OPEN "cg2data\savegame.dat" FOR OUTPUT AS #2
  PRINT #2, maxscore
  PRINT #2, maxlevelreached
  CLOSE #2

  GOTO MenuPrincipal
END IF

CLOSE #1

maxlevelreached = mapnumber

KILL "cg2data\savegame.dat"
OPEN "cg2data\savegame.dat" FOR OUTPUT AS #1
PRINT #1, maxscore
PRINT #1, maxlevelreached
CLOSE #1

FOR t = 1 TO maxplayers
  Player(t).x = 144
  Player(t).y = 160
  Player(t).VelX = 4
  Player(t).VelY = 3
  Player(t).Turnflag = 0
  ' Player(t).Health = 100
  ' Player(t).Score = 0
  ' Player(t).Gunlevel = 0
  Player(t).Invencible = 0
  ' Player(t).Ammo = 5
NEXT t

FOR t = 1 TO 8
  Enemy(t).x = -32
  Enemy(t).y = 0
  Enemy(t).VelX = 0
  Enemy(t).VelY = 0
  Enemy(t).Userflag = 0
  Enemy(t).Health = 1
  Enemy(t).Kind = 0
  Enemy(t).Powerup = " "
  Enemy(t).BossDeathFlag = 0
NEXT t

FOR t = 1 TO 8
  EShot(t).x = -10
  EShot(t).y = 0
  EShot(t).VelX = 0
  EShot(t).VelY = 0
NEXT t

FOR t = 1 TO maxpshots
  pshot(t).x = -33
  pshot(t).y = 100
  pshot(t).VelY = 0
  pshot(t).Class = 0
NEXT t

FOR t = 1 TO 4
  Missile(t).x = -33
  Missile(t).y = -33
  Missile(t).VelX = 0
  Missile(t).VelY = 0
  Missile(t).Owner = -1
  Missile(t).Ang = 0
  Missile(t).Lockon = 1
NEXT t

FOR t = 1 TO maxdebris
  Debris(t).x = -33
  Debris(t).y = 100
  Debris(t).VelX = 0
  Debris(t).VelY = 0
  Debris(t).Userflag = 0
NEXT t

FOR t = 1 TO 200
  Eventdata(t).Frame = 0
  Eventdata(t).Kind = SPACE$(1)
  Eventdata(t).Buff = SPACE$(40)
  Eventdata(t).x = 0
  Eventdata(t).y = 0
NEXT t

DQBclearLayer 0

DQBsetPal Pal

GOTO InicioNivel

' En caso de que las rutinas de salir de nivel fallen...
DQBclose
END



' Rutinas de inteligencia artificial.

AI1:
Enemy(t).VelY = Enemy(t).VelY + .05
IF Enemy(t).Userflag = 0 THEN
  Enemy(t).Userflag = 1
ELSE
  Enemy(t).Userflag = 0
END IF
RETURN

AI2:
Enemy(t).VelY = Enemy(t).VelY - .05
Enemy(t).Userflag = Enemy(t).Userflag + 1
IF Enemy(t).Userflag = 15 THEN Enemy(t).Userflag = 0
RETURN

AI3:
SELECT CASE Enemy(t).Userflag
  CASE 0 TO 1
    IF Enemy(t).Userflag = 0 THEN
      Enemy(t).Userflag = 1
    ELSE
      Enemy(t).Userflag = 0
    END IF
  CASE 2 TO 3
    IF Enemy(t).Userflag = 2 THEN
      Enemy(t).Userflag = 3
    ELSE
      Enemy(t).Userflag = 2
    END IF
END SELECT
RETURN

AI4:
Enemy(t).VelY = Enemy(t).VelY - .05
IF Enemy(t).Userflag = 0 THEN
  Enemy(t).Userflag = 1
ELSE
  Enemy(t).Userflag = 0
END IF
RETURN

AI5:
'Enemigo tont¡n
RETURN

AI6:
Enemy(t).VelY = Enemy(t).VelY + .05
IF curframe MOD 3 = 0 THEN
  IF Enemy(t).VelX > 0 THEN
    Enemy(t).Userflag = Enemy(t).Userflag + 1
  ELSE
    Enemy(t).Userflag = Enemy(t).Userflag - 1
  END IF
END IF
RETURN

AI7:
Enemy(t).Userflag = Enemy(t).Userflag - 10
IF Enemy(t).Userflag < 0 THEN Enemy(t).Userflag = Enemy(t).Userflag + 256
RETURN

AIBoss:
IF Enemy(1).y = 20 AND Enemy(1).Userflag = 0 THEN
  FOR i = 1 TO 6
    Enemy(i).VelY = 0
    Enemy(i).VelX = -1
    Enemy(i).Userflag = 1
  NEXT i
END IF

IF Enemy(1).x = 5 AND Enemy(1).Userflag = 1 THEN
  FOR i = 1 TO 6
    Enemy(i).VelX = 1
    Enemy(i).Userflag = 2
  NEXT i
END IF

IF Enemy(1).x = 218 AND Enemy(1).Userflag = 2 THEN
  FOR i = 1 TO 6
    Enemy(i).VelX = -1
    Enemy(i).Userflag = 1
  NEXT i
END IF

FOR i = 2 TO 6
  IF Enemy(i).Kind > 9 AND Enemy(i).Kind < 22 THEN
    IF i < 4 THEN
      Enemy(i).x = Enemy(1).x + (i - 1) * 32
      Enemy(i).y = Enemy(1).y
    ELSE
      Enemy(i).x = Enemy(1).x + (i - 4) * 32
      Enemy(i).y = Enemy(1).y + 32
    END IF
  END IF
NEXT i

RETURN

