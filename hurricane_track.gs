* Carlos del-Castillo-Negrete
* GEO 387G - Final Project

* global dispaly options
cint=2
'set display color white'

* Files to compile
plotmax=1
numfiles=4
plotindividual=0

* 27 KM case
name.1='27KM'
ctfile.1='/scratch/06307/clos21/jobs/PTCN2014/27KM/output/GrADS/cur/grds_d01.ctl.new'
linecol.1=2
skiparrows.1=7

* 15 KM case
name.2='15KM'
ctfile.2='/scratch/06307/clos21/jobs/PTCN2014/15KM/output/GrADS/cur/grds_d01.ctl.new'
linecol.2=3
skiparrows.2=14

* 15 KM case with updating SST
name.3='15KM_SST'
ctfile.2='/scratch/06307/clos21/jobs/PTCN2014/15KM/output/GrADS/cur/grds_d01.ctl.new'
ctfile.3='/scratch/06307/clos21/jobs/PTCN2014/15KM_SST/output/GrADS/cur/grds_d01.ctl.new'
linecol.3=4
skiparrows.3=14

* 15 KM Future Scenario - 2050 SSP245
name.4='15KM_2050'
ctfile.4='/scratch/06307/clos21/jobs/PTCN2014/15KM/output/GrADS/2050_ssp245/grds_d01.ctl.new'
linecol.4=8
skiparrows.4=14

fno=1
tinit=1
endts=1000
while (fno<=numfiles)

  'close 1'
  say 'Processing file - 'ctfile.fno
  'open 'ctfile.fno
* Get global bounds to control file
  lonlin=sublin(result,3)
  gminlon=subwrd(lonlin,4)
  gmaxlon=subwrd(lonlin,5)
  latlin=sublin(result,4)
  gminlat=subwrd(latlin,4)
  gmaxlat=subwrd(latlin,5)
  'q time'
  tline=sublin(result,5)
  tsize=subwrd(tline,12)

  say 'Global bounds [lon, lat]: ['gminlon', 'gmaxlon'], ['gminlat', 'gmaxlat'] ]'

  if fno<2
    say 'Determining start time... '
    while (timit < tsizes)
      'clear'
      setgraphsettings(cint)
      'set t 'tinit
      'set lat 'gminlat%' '%gmaxlat
      'set lon 'gminlon' 'gmaxlon
      'd slp' 
      'q time'
      time=subwrd(result,3)
      'draw title ' name.fno' SLP (hPA) 'time

      prompt 'Press Enter to continue, type START to set this as start time step: ' 
      pull end 

      if end='START'
        break
      endif

      tinit=tinit+1
    endwhile
  endif

* prompt 'Enter out hurricane track file (Press Enter for no output file) : '
* pull outfile 
  outfile=name.fno'.csv'

  if outfile!=''
    dummy=write(outfile, 'times,minp,minlocx,minlocy,centerlon,centerlat,centerx,centery,wmax,w925max,w850max')
  endif

  maxwts.fno = 1
  minpts.fno = 1
  pmin.fno = 2000
  maxw.fno = 0

  i=1
  ts=tinit
  'clear'
  setgraphsettings(cint)
  'set t 'ts
  'set grid on'
  'set lat 'gminlat%' '%gmaxlat
  'set lon 'gminlon' 'gmaxlon
  'd slp' 
  'q time'
  tstart=subwrd(result,3)
  'draw title ' name.fno' SLP (hPA) 'tinit
  prompt 'Enter initial min latitude: '
  pull initminlat
  prompt 'Enter initial max latitude: '
  pull initmaxlat
  prompt 'Enter initial min longitude: '
  pull initminlon
  prompt 'Enter initial max longitude: '
  pull initmaxlon

  prompt 'Enter hurricane latitude width: '
  pull hurlatwidth
  prompt 'Enter hurricane longitude width: '
  pull hurlonwidth

  hurlatwidth = hurlatwidth/2.0
  hurlonwidth = hurlonwidth/2.0

  while (ts < tsizes)
    say 'endts = 'endts
    if ts>endts
      break
    endif

    guessminlat = initminlat-0.25*hurlatwidth
    guessmaxlat = initmaxlat+0.25*hurlatwidth
    guessminlon = initminlon-0.25*hurlonwidth
    guessmaxlon = initmaxlon+0.25*hurlonwidth
    'clear'
    'set t 'ts
    setgraphsettings(cint)
    'set lat 'gminlat%' '%gmaxlat
    'set lon 'gminlon' 'gmaxlon
    'set grid on'
    'd slp' 
    'q time'
    times.fno.i=subwrd(result,3)
    'draw title ' name.fno' SLP (hPA) 'times.fno.i

    'q w2xy 'guessminlon' 'guessminlat
    xsw=subwrd(result,3)
    ysw=subwrd(result,6)
    'q w2xy 'guessminlon' 'guessmaxlat
    xnw=subwrd(result,3)
    ynw=subwrd(result,6)
    'q w2xy 'guessmaxlon' 'guessmaxlat
    xne=subwrd(result,3)
    yne=subwrd(result,6)
    'q w2xy 'guessmaxlon' 'guessminlat
    xse=subwrd(result,3)
    yse=subwrd(result,6)

    'set line 1 3 7'
    'draw line 'xsw' 'ysw' 'xnw' 'ynw
    'draw line 'xnw' 'ynw' 'xne' 'yne
    'draw line 'xne' 'yne' 'xse' 'yse
    'draw line 'xse' 'yse' 'xsw' 'ysw

    'd amin(slp,lon='guessminlon',lon='guessmaxlon',lat='guessminlat',lat='guessmaxlat')'
    minp.fno.i=subwrd(result,4)
    'd aminlocx(slp,lon='guessminlon',lon='guessmaxlon',lat='guessminlat',lat='guessmaxlat')'
    minlocx.fno.i=subwrd(result,4)
    'd aminlocy(slp,lon='guessminlon',lon='guessmaxlon',lat='guessminlat',lat='guessmaxlat')'
    minlocy.fno.i=subwrd(result,4)
    'q gr2w 'minlocx.fno.i' 'minlocy.fno.i
    centerlon.fno.i=subwrd(result,3)
    centerlat.fno.i=subwrd(result,6)
    'q gr2xy 'minlocx.fno.i' 'minlocy.fno.i
    centerx.fno.i=subwrd(result,3)
    centery.fno.i=subwrd(result,6)

    minlon.fno.i=centerlon.fno.i-hurlonwidth 
    maxlon.fno.i=centerlon.fno.i+hurlonwidth 
    minlat.fno.i=centerlat.fno.i-hurlatwidth
    maxlat.fno.i=centerlat.fno.i+hurlatwidth 
  
    'q w2xy 'minlon.fno.i' 'minlat.fno.i
    xsw=subwrd(result,3)
    ysw=subwrd(result,6)
    'q w2xy 'minlon.fno.i' 'maxlat.fno.i
    xnw=subwrd(result,3)
    ynw=subwrd(result,6)
    'q w2xy 'maxlon.fno.i' 'maxlat.fno.i
    xne=subwrd(result,3)
    yne=subwrd(result,6)
    'q w2xy 'maxlon.fno.i' 'minlat.fno.i
    xse=subwrd(result,3)
    yse=subwrd(result,6)

    say ''
    say 'Guessing range (dashed) : [ ['guessminlat','guessmaxlat'] , ['guessminlon','guessmaxlon'] ]'
    say 'Current time step = 'ts
    say 'Adjusted to range (solid) : [ ['minlat.fno.i','maxlat.fno.i'] , ['minlon.fno.i','maxlon.fno.i'] ]'

    'set line 1 1 7'
    'draw line 'xsw' 'ysw' 'xnw' 'ynw
    'draw line 'xnw' 'ynw' 'xne' 'yne
    'draw line 'xne' 'yne' 'xse' 'yse
    'draw line 'xse' 'yse' 'xsw' 'ysw

    'define w1 = mag(u10,v10)'
    'define w2 = mag(u(lev=925),v(lev=925))'
    'define w3 = mag(u(lev=850),v(lev=850))'
    'd amax(w1,lon='minlon.fno.i',lon='maxlon.fno.i',lat='minlat.fno.i',lat='maxlat.fno.i')'
    wmax.fno.i=subwrd(result,4)
    'd amax(w2,lon='minlon.fno.i',lon='maxlon.fno.i',lat='minlat.fno.i',lat='maxlat.fno.i')'
    w925max.fno.i=subwrd(result,4)
    'd amax(w3,lon='minlon.fno.i',lon='maxlon.fno.i',lat='minlat.fno.i',lat='maxlat.fno.i')'
    w850max.fno.i=subwrd(result,4)

    say 'Center found at = ('centerlon.fno.i','centerlat.fno.i') | ('centerx.fno.i','centery.fno.i')'
    say 'Minimum pressure = 'minp.fno.i
    say 'Maximum wind velocity (10m) = 'wmax.fno.i
    say 'Maximum wind velocity (925hPa) = 'w925max.fno.i
    say 'Maximum wind velocity (850hPA) = 'w850max.fno.i

    say 'minp.fno.i = 'minp.fno.i
    say 'pmin.fno = 'pmin.fno
    if minp.fno.i < pmin.fno
      pmin.fno = minp.fno.i
      minps.fno = ts
      minpsdispts = times.fno.i
    endif
    if wmax.fno.i > maxw.fno
      maxw.fno = wmax.fno.i
      maxwts.fno = ts
      maxwdispts = times.fno.i
    endif

    if outfile!=''
      say 'Writing track data for 'name.fno' to file 'outfile
      val= times.fno.i','minp.fno.i','minlocx.fno.i','minlocy.fno.i','centerlon.fno.i','centerlat.fno.i','centerx.fno.i','centery.fno.i','wmax.fno.i','w925max.fno.i','w850max.fno.i
      say 'WRITING: 'val
      dummy=write(outfile, val, append)
    endif

    prompt 'Press Enter to continue, SAVE to save current image, END to set this as the end timestep: ' 
    pull end 

    if end='SAVE'
      'clear'
      'set t 'ts
      setgraphsettings(cint)
      'set grid off'
      'set lat 'gminlat%' '%gmaxlat
      'set lon 'gminlon' 'gmaxlon
      'd slp' 
      'd skip(u10,'skiparrows.fno','skiparrows.fno');v10'
      'draw title ' name.fno' SLP (hPA) and Wind at 10m (m/s) at 'times.fno.i
      prompt 'Press ENTER to continue'
      pull dummy 
    endif

    if end='END'
      endts=ts
      break
    endif

    initminlon=minlon.fno.i
    initmaxlon=maxlon.fno.i
    initminlat=minlat.fno.i
    initmaxlat=maxlat.fno.i

    ts = ts + 1
    i = i + 1
  endwhile

  close(outfile)

  if plotmax=1
    'clear'
    'set t 'minpts.fno
    setgraphsettings(cint)
    'set lat 'gminlat%' '%gmaxlat
    'set lon 'gminlon' 'gmaxlon
    'd slp' 
    'd skip(u10,'skiparrows.fno','skiparrows.fno');v10'
    'draw title ' name.fno' Minimum SLP - 'pmin.fno' hPA at 'minpsdispts
    prompt 'Press ENTER to continue'
    pull dummy 

    'clear'
    'set t 'maxwts.fno
    setgraphsettings(cint)
    'set lat 'gminlat%' '%gmaxlat
    'set lon 'gminlon' 'gmaxlon
    'd slp' 
    'd skip(u10,10,10);v10'
    'draw title ' name.fno' Max Wind Speed- 'maxw.fno' m/s at 'maxwdispts
    prompt 'Press ENTER to continue'
    pull dummy 
  endif

  fno = fno + 1
endwhile



* Plot hurricane track
say 'Plotting Hurricane Track'

fi=1
max=i
if plotindividual=1
  while fi<=numfiles
    i=1
    j=2
    'clear'
    setgraphsettings(cint)
    'set clevs -500000'
    'set lat 'gminlat%' '%gmaxlat
    'set lon 'gminlon' 'gmaxlon
    'd slp/100' 
    prompt 'Plotting track for 'name.fi
    while (j < max)
      color=1
      if wmax.fi.i>=18
        color=3
      endif
      if wmax.fi.i>=33
        color=5
      endif
      if wmax.fi.i>=43
        color=4
      endif
      if wmax.fi.i>=50
        color=14
      endif
      if wmax.fi.i>=58
        color=8
      endif
      if wmax.fi.i>=70
        color=2
      endif

      'set line 'color' 1 10'
      say 'draw line 'centerx.fi.i' 'centery.fi.i' 'centerx.fi.j' 'centery.fi.j
      'draw line 'centerx.fi.i' 'centery.fi.i' 'centerx.fi.j' 'centery.fi.j

      i=j
      j=j+1


    endwhile
    'draw title Track - 'name.fi
    prompt 'Press Enter to continue: ' 
    pull dummy
    fi = fi + 1
  endwhile
endif

'clear'
setgraphsettings(cint)
'set clevs -500000'
'set lat 'gminlat%' '%gmaxlat
'set lon 'gminlon' 'gmaxlon
'd slp/100' 
fi=1
say 'Plotting all Tracks'
titlestr=name.fi
while fi<=numfiles
  i=1
  j=2
  prompt 'Plotting track for 'name.fi
  while (j < max)

    say 'set line 'linecol.fi' 1 10'
    'set line 'linecol.fi' 1 10'
    say 'draw line 'centerx.fi.i' 'centery.fi.i' 'centerx.fi.j' 'centery.fi.j
    'draw line 'centerx.fi.i' 'centery.fi.i' 'centerx.fi.j' 'centery.fi.j

    i=j
    j=j+1


  endwhile
  if fi>1
    titlestr=titlestr','name.fi
  endif
  prompt 'Press Enter to continue: ' 
  pull dummy
  fi = fi + 1
endwhile
'draw title Best Tracks for cases 'titlestr

prompt 'Press Enter to continue: ' 
pull end 

prompt 'Enter path to hurdat file : ' 
pull path 
hurdat=plothurdata(path)


prompt 'Press Enter to continue, type END to terminate : ' 
pull end 


* HURDATA FORMAT (https://www.nhc.noaa.gov/data/hurdat/hurdat2-format-nencpac.pdf) :
* 20120616, 0100, L, HU, 15.8N, 96.9W, 90, 976, 40, 80, 70, 80, 30, 50, 50, 60, 15, 35, 25, 25,
* 2012 (Spaces 1-4) – Year
* 06 (Spaces 5-6) – Month
* 16 (Spaces 7-8, before 1st comma) – Day
* 01 (Spaces 11-12) – Hours in UTC (Universal Time Coordinate)
* 00 (Spaces 13-14, before 2nd comma) – Minutes
* L (Space 17, before 3rd comma) – Record identifier (see notes below)
*     L – Landfall (center of system crossing a coastline)
*     P – Minimum in central pressure
*     I – An intensity peak in terms of both pressure and maximum wind
*     S – Change of status of the system
*     T – Provides additional detail on the track (position) of the cyclone
* HU (Spaces 20-21, before 4th comma) – Status of system. Options are:
*   TD – Tropical cyclone of tropical depression intensity (< 34 knots)
*   TS – Tropical cyclone of tropical storm intensity (34-63 knots)
*   HU – Tropical cyclone of hurricane intensity (> 64 knots)
*   EX – Extratropical cyclone (of any intensity)
*   SD – Subtropical cyclone of subtropical depression intensity (< 34 knots)
*   SS – Subtropical cyclone of subtropical storm intensity (> 34 knots)
*   LO – A low that is neither a tropical cyclone, a subtropical cyclone, nor an extratropical cyclone (of any intensity)
*   DB – Disturbance (of any intensity) 
* 15.8 (Spaces 24-27) – Latitude
* N (Space 28, before 5th comma) – Hemisphere – North or South
* 96.9 (Spaces 31-35) – Longitude
* W (Space 36, before 6th comma) – Hemisphere – West or East
* 90 (Spaces 39-41, before 7th comma) – Maximum sustained wind (in knots)
* 976 (Spaces 44-47, before 8th comma) – Minimum Pressure (in millibars)
* 40 (Spaces 50-53, before 9th comma) – 34 kt wind radii maximum extent in northeastern quadrant (in nautical miles)
* 80 (Spaces 56-59, before 10th comma) – 34 kt wind radii maximum extent in southeastern quadrant (in nautical miles)
* 70 (Spaces 62-65, before 11th comma) – 34 kt wind radii maximum extent in southwestern quadrant (in nautical miles)
* 80 (Spaces 68-71, before 12th comma) – 34 kt wind radii maximum extent in northwestern quadrant (in nautical miles)
* 30 (Spaces 74-77, before 13th comma) – 50 kt wind radii maximum extent in northeastern quadrant (in nautical miles)
* 50 (Spaces 80-83, before 14th comma) – 50 kt wind radii maximum extent in southeastern quadrant (in nautical miles)
* 50 (Spaces 86-89, before 15th comma) – 50 kt wind radii maximum extent in southwestern quadrant (in nautical miles)
* 60 (Spaces 92-95, before 16th comma) – 50 kt wind radii maximum extent in northwestern quadrant (in nautical miles)
* 15 (Spaces 98-101, before 17th comma) – 64 kt wind radii maximum extent in northeastern quadrant (in nautical miles)
* 35 (Spaces 104-107, before 18th comma) – 64 kt wind radii maximum extent in southeastern quadrant (in nautical miles)
* 25 (Spaces 110-113, before 19th comma) – 64 kt wind radii maximum extent in southwestern quadrant (in nautical miles)
* 25 (Spaces 116-119, before 20th comma) – 64 kt wind radii maximum extent in northwestern quadrant (in nautical miles) 
function plothurdata(path)
  say 'Reading HURDAT from 'path

  i=1
  res=read(path)
  status=subwrd(res,1)
  while (status='0')
    line=sublin(res,2) 
*   say 'Processing line - 'line
    j=1
    while (j < 21)
      hurdat.j.i=readrecord(line,j)
*     say 'Read record 'hurdat.j.i
      j=j+1
    endwhile
  
    if i>1
      if hurdat.4.i='TD'
        color=1
      endif
      if hurdat.4.i='TS'
        color=3
      endif
      if hurdat.4.i='HU'
        color=5
        if hurdat.7.i>=83.58
          color=4
        endif
        if hurdat.7.i>=97.2
          color=14
        endif
        if hurdat.7.i>=112.743
          color=8
        endif
        if hurdat.7.i>=136.07
          color=2
        endif
      endif

      j=i-1
      centerxstart = getcenterlat(hurdat.5.j, hurdat.6.j, 'x')
      centerystart = getcenterlat(hurdat.5.j, hurdat.6.j, 'y')
      centerxend = getcenterlat(hurdat.5.i, hurdat.6.i, 'x')
      centeryend = getcenterlat(hurdat.5.i, hurdat.6.i, 'y')

      'set xlopts 1 3 .15'
      'set ylopts 1 3 .15'
      'set ylint 5'
      'set xlint 10 '
      'set line 'color' 1 10'
      say 'draw line 'centerxstart' 'centerystart' 'centerxend' 'centeryend
      'draw line 'centerxstart' 'centerystart' 'centerxend' 'centeryend

      prompt 'Press Enter to continue, type END to terminate : ' 
      pull end 
    endif
    res=read(path)
    status=subwrd(res,1)
    i=i+1
  endwhile

  return hurdat

function readrecord(line, idx)
  res=subwrd(line,idx)
  len=strlen(res)
  if len=1
    return ''
  endif
  res=substr(res,1,len-1)
  return res

function getcenterlat(latval, lonval, type)
  len=strlen(latval)
  nsval=substr(latval,1,len-1)
  nshem=substr(latval,len,len)
  if nshem='N'
    centerlat=nsval
  endif
  if nshem='S'
    centerlat=-nsval
  endif
  len=strlen(lonval)
  ewval=substr(lonval,1,len-1)
  ewhem=substr(lonval,len,len)
  if ewhem='E'
    centerlon=ewval
  endif
  if ewhem='W'
    centerlon=-ewval
  endif

  'q w2xy 'centerlon' 'centerlat
  centerxstart=subwrd(result,3)
  centerystart=subwrd(result,6)

  if type='x'
    return centerxstart
  endif
  if type='y'
    return centerystart
  endif

function setgraphsettings(cint)
  'set cint 'cint
  'set mpdset hires' 
  'set map 1 1 10'
  'set grads off'
  'set xlopts 1 5 .15'
  'set ylopts 1 5 .15'
  'set ylint 5'
  'set xlint 10'
  return
