# Carlos del-Castillo-Negrete
# GEO 387G Final Project
# autogrid.py - For automatic geogrid configuration.
import re
import os
import pdb
import json
import pprint
import logging
import argparse
import subprocess
from datetime import datetime
from shutil import copy
from itertools import combinations
from time import perf_counter, sleep
from contextlib import contextmanager


logger = logging.getLogger()


@contextmanager
def timing(label: str):
  t0 = perf_counter()
  yield lambda: (label, t1 - t0)
  t1 = perf_counter()

def get_nested_params(readme_path:str='./README.namelist'):
  nested_params = {}
  with open(readme_path, 'r') as fp:
    line = fp.readline()
    while line!='':
      if line.strip().startswith('&'):
        config_type = line.strip().split(' ')[0].replace('&','')
        if config_type not in nested_params.keys():
          nested_params[config_type] = {}
      elif  ('(max_dom)' in line) and ('=' in line):
        param = line.strip().split(' ')[0]
        if '!' in line:
          desc = line.split('!')[1].strip()
        else:
          desc = ''
        if '(' in param:
          param = param.split('(')[0]
        if param not in nested_params[config_type].keys():
          nested_params[config_type][param] = desc
      line = fp.readline()
  return nested_params


def get_corners(path:str):
  logger.debug(f"Running ncdump on {path}")
  res = subprocess.run(["ncdump", "-h", path], stdout=subprocess.PIPE)

  proc1 = subprocess.Popen(['ncdump', '-h', path], stdout=subprocess.PIPE)
  proc2 = subprocess.Popen(['grep', 'corner_l'], stdin=proc1.stdout,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  proc1.stdout.close() # Allow proc1 to receive a SIGPIPE if proc2 exits.
  out, err = proc2.communicate()
  err = err.decode('utf-8')
  out = out.decode('utf-8')

  if err!='':
    msg = f"Unable to access grid file {path} file - {err}"
    logger.debug(msg)
    raise Exception(msg)

  logger.debug("Processing Bounding Box...")
  bounding_box= [[x.split('=')[1] for x in out.split('\t\t')[1:]][0].split(',')[0:2],
                 [x.split('=')[1] for x in out.split('\t\t')[1:]][1].split(',')[1:3]]
  for i, dims in enumerate(bounding_box):
    for j, x in enumerate(dims):
      bounding_box[i][j] = float(x.strip().replace('f', ''))
  logger.debug(f"DONE! Bounding box from {path}: {bounding_box}")

  return bounding_box


def sync_arwpost_namelist(path:str, update_configs:dict=None):
  wps = process_namelist(os.path.join(path, 'namelist.wps'))
  wrf = process_namelist(os.path.join(path, 'namelist.input'))
  arwpost = process_namelist(os.path.join(path, 'namelist.ARWpost'))

  num_doms = int(wps['share']['max_dom'][0])
  start_date = [datetime.strptime(x.replace("'",""),
      '%Y-%m-%d_%H:%M:%S') for x in wps['share']['start_date']]
  end_date = [datetime.strptime(x.replace("'",""),
      '%Y-%m-%d_%H:%M:%S') for x in wps['share']['end_date']]

  # Create a new ARWpost namelist per nested domain
  synced = []
  for d in range(num_doms):

    # Create dictionary of configs to update in ARWpost namelist for this domain
    update_configs = {}
    dt = {}
    dt['start_date'] = wps['share']['start_date'][d]
    dt['end_date'] = wps['share']['end_date'][d]
    dt['interval_seconds'] = int(wrf['time_control']['history_interval'][d])*60
    update_configs['datetime'] = dt

    io = {}
    io['input_root_name'] = f"'../wrf/wrfout_d{d+1:02d}_{start_date[d]}'"
    io['output_root_name'] = f"'../output/GrADS/grds_d{d+1:02d}'"
    update_configs['io'] = io

    update_path = f'd{d+1:02d}.namelist.ARWpost'
    synced.append(process_namelist(os.path.join(path, 'namelist.ARWpost'), update_path=update_path,
        update_configs=update_configs))

  return synced



def sync_wrf_namelist(path:str, update_configs:dict=None):
  wps = process_namelist(os.path.join(path, 'namelist.wps'))
  wrf = process_namelist(os.path.join(path, 'namelist.input'))

  num_doms = int(wps['share']['max_dom'][0])
  start_date = [datetime.strptime(x.replace("'",""),
      '%Y-%m-%d_%H:%M:%S') for x in wps['share']['start_date']]
  end_date = [datetime.strptime(x.replace("'",""),
      '%Y-%m-%d_%H:%M:%S') for x in wps['share']['end_date']]

  # Checks if param for config type is a param that requries definition per nest
  # This information is parsed from the README.namelist specification file
  nested_params = get_nested_params(os.path.join(path,'..','wrf','README.namelist'))
  def fill(config_type, var):
    if var in nested_params[config_type].keys():
      val = wrf[ct][var]
      if len(val)>=num_doms:
        return None
      else:
        return val + (num_doms-len(val))*[val[-1]]

  # Build update config for wrf namelist input file based off of wps input file
  # Only modifying fields relevant to start/stop time and domain information
  update_configs = {}
  time_control = {}
  time_control['run_days'] = [(x[1]-x[0]).days for x in zip(start_date, end_date)]
  seconds = [(x[1]-x[0]).seconds for x in zip(start_date, end_date)]
  sec_min_hrs = [[(x % 60), ((x % 3600) // 60), (x // 3600)] for x in seconds]
  time_control['run_hours'] = [x[2] for x in sec_min_hrs]
  time_control['run_minutes'] = [x[1] for x in sec_min_hrs]
  time_control['run_seconds'] = [x[0] for x in sec_min_hrs]
  time_control['start_year'] = [x.year for x in start_date]
  time_control['start_month'] = [x.month for x in start_date]
  time_control['start_day'] = [x.day for x in start_date]
  time_control['start_hour'] = [x.hour for x in start_date]
  time_control['end_year'] = [x.year for x in end_date]
  time_control['end_month'] = [x.month for x in end_date]
  time_control['end_day'] = [x.day for x in end_date]
  time_control['end_hour'] = [x.hour for x in end_date]
  time_control['interval_seconds'] = wps['share']['interval_seconds'][0]
  time_control['input_from_file'] = num_doms*['.true.']
  update_configs['time_control'] = time_control

  domains = {}
  domains['max_dom'] = wps['share']['max_dom']
  domains['e_we'] = wps['geogrid']['e_we']
  domains['e_sn'] = wps['geogrid']['e_sn']
  domains['dx'] = wps['geogrid']['dx']
  domains['dy'] = wps['geogrid']['dy']
  domains['grid_id'] = [1+x for x in range(num_doms)]
  domains['parent_id'] = [int(x)-1 for x in wps['geogrid']['parent_id']]
  domains['i_parent_start'] = wps['geogrid']['i_parent_start']
  domains['j_parent_start'] = wps['geogrid']['j_parent_start']
  domains['parent_grid_ratio'] = wps['geogrid']['parent_grid_ratio']
  domains['parent_time_step_ratio'] = wps['geogrid']['parent_grid_ratio']
  update_configs['domains'] = domains

  # For the rest of the configs in the namelist, leave as is unless missing information for a
  # nested domains, in which case expand values with values from previous domain.
  # To set these parameters per domain, edit them to appropriate length For each domain before
  # Prior to running geogrid running autogrid.
  for ct in wrf.keys():
    if ct not in update_configs.keys():
      update_configs[ct] = {}
    for key in wrf[ct].keys():
      if key not in update_configs[ct].keys():
        new_val = fill(ct, key)
        if new_val!=None:
          update_configs[ct][key] = new_val

  synced = {}
  synced = process_namelist(os.path.join(path, 'namelist.input'), update_path='new.namelist.input',
      update_configs=update_configs)
  copy(os.path.join(path, 'namelist.input'), os.path.join(path, 'orig.namelist.input'))
  copy(os.path.join(path, 'new.namelist.input'), os.path.join(path, 'namelist.input'))

  return synced


def process_namelist(path:str, update_path:str=None, update_configs:dict=None):
  all_configs = {}
  if update_path!=None:
    logger.debug(f"Creating/Overwriting namelist.wps file at {update_path}")
    with open(update_path, 'w') as of:
      of.write('')
  with open(path, 'r') as fp:
    line = fp.readline()
    while line!='':
      while line.strip().startswith('!') or line.strip()=='':
        logger.debug(f"Skipping comment line: {line.strip()}")
        if update_path!=None:
          logger.debug(f"Writing comment line to {path}: {line.strip()}")
          with open(update_path, 'a') as of:
            of.write(line)
        line = fp.readline()
      config_type = line.strip().replace('&','')

      if update_path!=None:
        with open(update_path, 'a') as of:
          of.write(f"&{config_type}\n")

      config_vals = {}
      line = fp.readline()
      logger.debug(f"Processing configs for {config_type}")
      while not line.strip().startswith('/'):
        while line.strip().startswith('!') or line.strip()=='':
          logger.debug(f"Skipping comment line: {line.strip()}")
          if update_path!=None:
            logger.debug(f"Writing comment line to {path}: {line.strip()}")
            with open(update_path, 'a') as of:
              of.write(line)
          line = fp.readline()
        splt = line.split('=')
        var = splt[0].strip()
        val = splt[1]
        if ',' in val:
          # List values
          val = [x.strip() for x in val.split(',')]
          try: val.remove('')
          except ValueError: pass
        else:
          val = [val.strip()]
        logger.debug(f"Found {config_type}: {var} = {val}")

        if update_path!=None and update_configs!=None:
          update = False
          if config_type in update_configs.keys():
            if var in update_configs[config_type].keys():
              update=True
          if update:
            update_val = update_configs[config_type].pop(var)
            logger.debug(f"Updating config {var} value from {val} to {update_val}")
            val = update_val if type(update_val)==list else [update_val]
          logger.debug(f"Setting {config_type}: {var} = {val}")
          config_vals[var] = val
          line = ' ' + var.rjust(1, ' ').ljust(20, ' ') + " = " + \
              ','.join([str(x).rjust(5, ' ') for x in val])
          logger.debug(f"Writing {config_type} config line: {line}")
          with open(update_path, 'a') as of:
            of.write(line + ',\n')
        else:
          logger.debug(f"Setting {config_type}: {var} = {val}")
          config_vals[var] = val

        line = fp.readline()

      # Add any remaining parameter values for this configuration type that  are in udpate conifgs
      if update_path!=None and config_type in update_configs.keys():
        for key, val in update_configs[config_type].items():
          val = val if type(val)==list else [val]
          line = ' ' + key.ljust(20, ' ') + " = " + \
              ','.join([str(x).rjust(5, ' ') for x in val])
          logger.debug(f"Addding {config_type}: {var} = {val}")
          config_vals[var] = val
          logger.debug(f"Writing {config_type} config line: {line}")
          with open(update_path, 'a') as of:
            of.write(line + ',\n')

      if update_path!=None:
        logger.debug(f"Processed configs for {config_type}.")
        with open(update_path, 'a') as of:
          of.write("/\n")

      # Add to all configs
      logger.debug(f"Final '{config_type}' configs:\n{pprint.pformat(config_vals)}.")
      all_configs[config_type] = config_vals
      line = fp.readline()

  return all_configs


def plong(val:float):
  if val<0:
    val = 360 + val
  return val


def nlong(val:float):
  if val>180:
    val = val - 360
  return val


def guess_bounding_box(target_box, geogrid_configs, domain:int=0):
  dx = float(geogrid_configs['dx'][0])
  dy = float(geogrid_configs['dy'][0])

  # GEOGRID Configs to update
  new_configs={}

  # Turn target box to positive longitude values
  for i, v in enumerate(target_box[1]):
    target_box[1][i] = plong(v)

  new_configs['e_we'] = geogrid_configs['e_we']
  new_configs['e_sn'] = geogrid_configs['e_sn']
  if domain==0:
    new_configs['ref_lon'] = [nlong(target_box[1][0] + (target_box[1][1] - target_box[1][0])/2.0)]
    new_configs['ref_lat'] = [target_box[0][0] + (target_box[0][1] - target_box[0][0])/2.0]
    new_configs['e_we'][0] = int((target_box[1][1] - target_box[1][0]) * 100.0 / (dx/1000.0))
    new_configs['e_sn'][0] = int((target_box[0][1] - target_box[0][0]) * 111.0 / (dy/1000.0))
    new_configs['truelat1'] = new_configs['ref_lat']

  # Turn target box back to negative longitude values
  for i, v in enumerate(target_box[1]):
    target_box[1][i] = nlong(v)

  return new_configs


def guess_nested_box(target_box, geogrid_configs, parent_domain:int=0, ratio:int=3):
  logger.debug(f'Setting up nested domain: {target_box}, START:{start_date}, END:{end_date}')

  p_domain= {'parent_id':geogrid_configs['end_date'][parent_domain-1],
             'parent_grid_ratio':geogrid_configs['parent_grid_ratio'][parent_domain-1],
             'i_parent_start':geogrid_configs['i_parent_start'][parent_domain-1],
             'j_parent_start':geogrid_configs['j_parent_start'][parent_domain-1],
             'e_we':geogrid_configs['e_we'][parent_domain-1],
             'e_sn':geogrid_configs['e_sn'][parent_domain-1],
             'geog_data_res':geogrid_configs['geog_data_res'][parent_domain-1]}
  parent_box = get_corners(f'./geo_em.d{parent_domain:02d}.nc')
  logger.debug(f"Found parent domain #{parent_domain}:\n{pprint.pformat(parent_box)}\n"\
      "{pprint.pformat(parent_domain)}")

  # Turn parent and target box to positive longitude values
  for i, v in enumerate(parent_box[1]):
    parent_box[1][i] = plong(v)
  for i, v in enumerate(target_box[1]):
    target_box[1][i] = plong(v)

  dx = float(geogrid_configs['dx'][0])/1000.0
  dy = float(geogrid_configs['dy'][0])/1000.0

  # Get ture parent grid resolution if parent domain is nested in another domain
  p_id = p_domain['parent_id']
  while p_id!=1:
    dx = dx / geogrid_configs['parent_grid_ratio'][p_id]
    dy = dy / geogrid_configs['parent_grid_ratio'][p_id]
    logger.debug(f"Grandparent domain #{p_id} found. New resolutions (dx, dy) = ({dx}, {dy})")
    p_id = geogrid_configs['parent_id'][p_id]

  geogrid_configs['parent_id'].append(str(parent_domain))
  geogrid_configs['parent_grid_ratio'].append(str(ratio))
  i_parent_start = (target_box[1][0] - parent_box[1][0])*100/dx
  j_parent_start = (target_box[0][0] - parent_box[0][0])*111/dy
  geogrid_configs['i_parent_sart'].append(str(i_parent_start))
  geogrid_configs['j_parent_sart'].append(str(j_parent_start))
  e_we = (((target_box[1][1] - parent_box[1][0]) * 100.0 / dx) - i_parent_start) * ratio + 1
  e_sn = (((target_box[0][1] - parent_box[0][0]) * 111.0 / dy) - j_parent_start) * ratio + 1
  # Make sure remainder of e_we, e_sn is 1 when divided by 3
  rem_we = e_we % 3
  if rem_we != 1:
    e_we = (e_we+1) if rem_we == 0 else (e_we-1)
  rem_sn = e_sn % 3
  if rem_sn != 1:
    e_sn = (e_sn+1) if rem_sn == 0 else (e_sn-1)
  geogrid_configs['e_we'].append(str(e_we))
  geogrid_configs['e_sn'].append(str(e_sn))
  geogrid_configs['geog_data_res'].append(geogrid_configs['geog_data_res'][parent_domain-1])

  logger.debug(f"Updated geogrid configs w/new nested domain:\n{pprint.pformat(geogrid_configs)}")

  return geogrid_configs


def update_bounding_box(current_box, target_box, geogrid_configs, domain:int=0,
    center:bool=True, scale:bool=False, lat:bool=True, lon:bool=False):

  # Turn current and target box to positive longitude values
  for i, v in enumerate(target_box[1]):
    target_box[1][i] = plong(v)
  for i, v in enumerate(current_box[1]):
    current_box[1][i] = plong(v)

  if domain==0:
    dx = float(geogrid_configs['dx'][0])
    dy = float(geogrid_configs['dy'][0])
    e_we = int(geogrid_configs['e_we'][0])
    e_sn = int(geogrid_configs['e_sn'][0])
    ref_lat = float(geogrid_configs['ref_lat'][0])
    ref_lon = plong(float(geogrid_configs['ref_lon'][0]))

    # GEOGRID Configs to update
    new_configs={}

    if center:
      if lon:
        # Get current center value
        cur_lon_center = current_box[1][0] + (current_box[1][1] - current_box[1][0])/2.0
        tar_lon_center = target_box[1][0] + (target_box[1][1] - target_box[1][0])/2.0

        # Calculate offset from central value
        lon_offset = tar_lon_center-cur_lon_center

        new_configs['ref_lon'] = [nlong(ref_lon + lon_offset)]
      if lat:
        # Get current center value
        cur_lat_center = current_box[0][0] + (current_box[0][1] - current_box[0][0])/2.0
        tar_lat_center = target_box[0][0] + (target_box[0][1] - target_box[0][0])/2.0

        # Calculate offset from central value
        lat_offset = tar_lat_center-cur_lat_center

        new_configs['ref_lat'] = [nlong(ref_lat + lat_offset)]
    if scale:
      if lon:
        cur_len = current_box[1][1] - current_box[1][0]
        targ_len = target_box[1][1] - target_box[1][0]
        e_we_change = (targ_len - cur_len) * (100.0) / (dx/1000.0)
        new_configs['e_we'] = geogrid_configs['e_we'].copy()
        new_configs['e_we'][0] = str(int(e_we_change) + e_we)
      if lat:
        e_sn_change = (current_box[0][0] - target_box[0][0]) * (111.0) / (dy/1000.0)
        e_sn_change += (target_box[0][1] - current_box[0][1]) * (111.0) / (dy/1000.0)
        new_configs['e_sn'] = geogrid_configs['e_sn'].copy()
        new_configs['e_sn'][0] = str(int(e_sn_change) + e_sn)
  else:
    new_configs = {}

  # Turn current and target box to positive longitude values
  for i, v in enumerate(target_box[1]):
    target_box[1][i] = nlong(v)
  for i, v in enumerate(current_box[1]):
    current_box[1][i] = nlong(v)

  return new_configs


def run_geogrid(np:int=None):
  cmd = ['ibrun', './geogrid.exe']
  if np!=None:
    cmd = ['ibrun', '-np', str(np), './geogrid.exe']
  proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  out, err = proc.communicate()
  err = err.decode('utf-8')
  out = out.decode('utf-8')
  if err!='':
    msg = f"Fatal error running geogrid:\n{err}"
    logger.critical(msg)
    raise Exception(msg)
  return out, err


def setup_main_domain(target_box:list, start_date:str, end_date:str, np:int=None):
  logger.info(f'Setting up main domain: {target_box}, START:{start_date}, END:{end_date}')
  base_configs = process_namelist('./namelist.wps')
  logger.info(f'Base WPS Configs:\n{pprint.pformat(base_configs)}\n')

  x_tolerance = 1.5*(float(base_configs['geogrid']['dx'][0])/1000.0)/100.0
  y_tolerance = 1.5*(float(base_configs['geogrid']['dy'][0])/1000.0)/100.0

  # Cacluate first guess at bounding box values
  geogrid_updates = guess_bounding_box(target_box, base_configs['geogrid'])

  # Configuratiosn that won't change through iterations of setting up parent domain
  share_confs = {'max_dom':f"1",
                 'start_date':f"'{start_date}'",
                 'end_date':f"'{end_date}'"}
  geogrid_confs = {'parent_id':"1",
                    'parent_grid_ratio':"1",
                    'i_parent_start':"1",
                    'j_parent_start':"1",
                    'geog_data_res':"'default'"}

  it = 0
  true_it = 0
  skip_geogrid = False
  while it<20:
    if not skip_geogrid:
      cur_configs = process_namelist('./namelist.wps', update_path=f'./d01.{it}.namelist.wps',
          update_configs={'geogrid':geogrid_updates.copy(), 'share':share_confs.copy()})
      cur_geogrid = {k: cur_configs['geogrid'][k] for k in ['e_sn', 'e_we', 'ref_lat', 'ref_lon']}
      logger.info("\n--------------------------------------------------")
      logger.info(f"Iteration {it} geogrid configs:\n{pprint.pformat(cur_geogrid)}")
      copy(f'./d01.{it}.namelist.wps', './namelist.wps')

      logger.info('Running geogrid')
      with timing('geogrid') as geogrid:
        run_geogrid(np=np)
      logger.info('Total [%s]: %.6f s' % geogrid())
      next_iter = it + 1

      current_box = get_corners('./geo_em.d01.nc')
      logger.info(f'New Bounding Box: {current_box}')
      logger.info(f'Target Bounding Box: {target_box}')

      tol = all([abs(current_box[1][0]-target_box[1][0])<x_tolerance,
                 abs(current_box[1][1]-target_box[1][1])<x_tolerance,
                 abs(current_box[0][0]-target_box[0][0])<y_tolerance,
                 abs(current_box[0][1]-target_box[0][1])<y_tolerance])
      if tol:
        logger.info(f'Grid tolerance ({x_tolerance}, {y_tolerance}) achieved at iteration {it}')
        break
    else:
      next_iter = it       # Only increase iteration counter if we actually run geogrid
      skip_geogrid=False


    if true_it%4==0:
      # Center latitude box
      logger.info(f'Centering latitude box')
      geogrid_updates = update_bounding_box(current_box, target_box, cur_configs['geogrid'],
          domain=0, center=True, scale=False, lat=True, lon=False)
    if true_it%4==1:
      # Center longitude box
      logger.info(f'Centering longitude box')
      geogrid_updates = update_bounding_box(current_box, target_box, cur_configs['geogrid'],
          domain=0, center=True, scale=False, lat=False, lon=True)
    if true_it%4==2:
      # Scale latitude box
      logger.info(f'Scaling latitude box')
      geogrid_updates = update_bounding_box(current_box, target_box, cur_configs['geogrid'],
          domain=0, center=False, scale=True, lat=True, lon=False)
    if true_it%4==3:
      # Scale longitude box
      logger.info(f'Scaling longitude box')
      geogrid_updates = update_bounding_box(current_box, target_box, cur_configs['geogrid'],
          domain=0, center=False, scale=True, lat=False, lon=True)

    update_config = list(geogrid_updates.keys())[0]
    cur_val = float(cur_configs['geogrid'][update_config][0])
    new_val = float(geogrid_updates[update_config][0])
    if cur_val==new_val:
      skip_geogrid=True    # Set to skip next iteration since no changes necessary
      logger.info(f'No update: {update_config} value {cur_val} same as {new_val}')
    else:
      logger.info(f"Will update: {update_config} from value {cur_val} to {new_val}")

    geogrid_updates.update(geogrid_confs)
    it = next_iter
    true_it = true_it + 1


def setup_nested_domain(target_box:list, start_date:str, end_date:str,
  parent_domain:int, ratio:int=3):
  logger.info(f'Setting up nested domain: {target_box}, START:{start_date}, END:{end_date}')
  base_configs = process_namelist('./namelist.wps')
  logger.info(f'Base WPS Configs:\n{pprint.pformat(base_configs)}')

  share_confs = {'max_dom':f"{base_configs['share']['max_dom']}",
                 'start_date':f"{base_configs['share']['start_date']}",
                 'end_date':f"{base_configs['share']['end_date']}"}
  share_confs['start_date'].append(f"'{start_date}'")
  share_confs['end_date'].append(f"'{end_date}'")
  share_confs['max_dom'] += 1
  geogrid_updates = guess_nested_box(target_box, base_configs['geogrid'],
    parent_domain=parent_domain, ratio=ratio)
  domain_id = share_confs['max_dom']

  it = 0
  skip_geogrid = False
  while it<20:
    logger.info(f'Iteration {it} geogrid configs:\n{pprint.pformat(geogrid_updates)}')
    cur_configs = process_namelist('./namelist.wps',
        update_path=f'./d{domain_id:02d}.{it}.namelist.wps',
        update_configs={'geogrid':geogrid_updates.copy(), 'share':share_confs.copy()})
    copy(f'./d{domain_id:02d}.{it}.namelist.wps', './namelist.wps')

    if not skip_geogrid:
      logger.info('Running geogrid')
      with timing('geogrid') as geogrid:
        run_geogrid()

    current_box = get_corners('./geo_em.d01.nc')
    logger.info(f'Current Bounding Box: {current_box}')
    logger.info(f'Target Bounding Box: {target_box}')

    if it%4==0:
      # Center latitude box
      logger.info(f'Centering latitude box')
      geogrid_updates = update_bounding_box(current_box, target_box, cur_configs['geogrid'],
          domain=0, center=True, scale=False, lat=True, lon=False)
    if it%4==1:
      # Center longitude box
      logger.info(f'Centering longitude box')
      geogrid_updates = update_bounding_box(current_box, target_box, cur_configs['geogrid'],
          domain=0, center=True, scale=False, lat=False, lon=True)
    if it%4==2:
      # Scale latitude box
      logger.info(f'Scaling latitude box')
      geogrid_updates = update_bounding_box(current_box, target_box, cur_configs['geogrid'],
          domain=0, center=False, scale=True, lat=True, lon=False)
    if it%4==3:
      # Scale longitude box
      logger.info(f'Scaling longitude box')
      geogrid_updates = update_bounding_box(current_box, target_box, cur_configs['geogrid'],
          domain=0, center=False, scale=True, lat=False, lon=True)

    update_config = list(geogrid_updates.keys())[0]
    if cur_configs['geogrid'][update_config]==geogrid_updates[update_config]:
      skip_geogrid=False
    else:
      skip_geogrid=True

    it += 1


def get_nested_structure(domains:dict):

  for d in domains.keys():
    domains[d]['children'] = []
    domains[d]['parents'] = []

  # Get list of all possible box pairs indices
  all_ds = list(domains.keys())
  pairs = combinations(range(len(all_ds)), 2)
  for pair in pairs:
    box1 = domains[all_ds[pair[0]]]['range']
    box2 = domains[all_ds[pair[1]]]['range']

    # Turn box1,box2 longitude to positive values
    for i, v in enumerate(box1[1]):
      box1[1][i] = plong(v)
    for i, v in enumerate(box2[1]):
      box2[1][i] = plong(v)

    def check_overlap(b1, b2, t):
      if b2[0] < b1[0]:
        # box2 start on left of box 1 start
        if b2[1] > b1[1]:
          # box1 latitude range child of box2
          return "child"
          logger.debug(f"Box1 {t} range {b1} is child of b2 {t} range {b2}.")
        elif b2[1] <= b1[1] and b2[1] >= b1[0]:
          msg = f"Overlapping latitude ranges {b1} and {b2}"
          logger.error(msg)
          raise Exception(msg)
        else:
          logger.debug(f"No Overlap between latitude ranges {b1} and {b2}")
      elif b2[0] < b1[1] and b2[0] != b1[0]:
        # box2 start lat on left of box 1 start lat
        if b2[1] < b1[1]:
          # box2 latitude range child of box1
          is_lat_parent = True
          return "parent"
        else:
          msg = f"Overlapping latitude ranges {box1[0]} and {box2[0]}"
          logger.error(msg)
          raise Exception(msg)
      return "no-overlap"

    lat_res = check_overlap(box1[0], box2[0], "latitude")
    lon_res = check_overlap(box1[1], box2[1], "longitude")

    if lat_res!=lon_res:
      msg = f"Not properly nested boxes. Latitude - {lat_res}, Longitude - {lon_res}."
      msg += f"\n{box1}\t{box2}"
      logger.error(msg)
      raise Exception(msg)

    if lat_res=="child":
      domains[all_ds[pair[0]]]['parents'].append(all_ds[pair[1]])
      domains[all_ds[pair[1]]]['children'].append(all_ds[pair[0]])
    elif lat_res=="parent":
      domains[all_ds[pair[0]]]['children'].append(all_ds[pair[1]])
      domains[all_ds[pair[1]]]['parents'].append(all_ds[pair[0]])

  # Order domains
  # Find main parent domain first
  p_domain = None
  for d in domains.keys():
    if len(domains[d]['parents'])==0:
      if p_domain!=None:
        msg = "Error - More than one main domain. {p_domain} and {d} conare both main domains."
        msg += f"\n{domains}"
        logger.error(msg)
        raise Exception(msg)
      else:
        p_domain=d

  if p_domain==None:
    msg = "Error - no main parent domain found"
    msg += f"\n{domains}"
    logger.error(msg)

  def get_children(dom):
    if len(domains[dom]['children'])>0:
      children = domains[dom]['children']
      all_children = []
      for child in children:
        all_children = all_children + get_children(child)
      return all_children
    else:
      return [dom]

  children = get_children(p_domain)
  domain_order = [p_domain] + children

  return domains, domain_order


if __name__ == "__main__":
  # Parse command line options
  parser = argparse.ArgumentParser()
  parser.add_argument('job_dir', type=str, help='Full path to job directory.')
  parser.add_argument('-np', '--num_processes', type=int, default=None,
      help="Number of processes to use for geogrid calls")
  parser.add_argument('-lf', '--log_file', type=str, default=None, help="Path to log file.")
  parser.add_argument('-ll', '--log_level', type=str, default='INFO',
    choices=['DEBUG','INFO','WARNING','ERROR','CRITICAL'], help='Set the logging level')
  args = parser.parse_args()

  # Initialize logger
  if args.log_file!=None:
    logging.basicConfig(level=args.log_level, filename=args.log_file,
        format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
  else:
    logging.basicConfig(level=args.log_level,
        format='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

  # Setup domain (no nested domains supported yet)
  with open(os.path.join(args.job_dir, 'configs.json'), 'r') as fp:
    configs = json.load(fp)

  domains = configs['domains']
  domains, order  = get_nested_structure(domains)

  # Determine main domain

  setup_main_domain(domains[order[0]]['range'], domains[order[0]]['start_date'],
    domains[order[0]]['end_date'], np=args.num_processes)

  # sync namelist.input file with domain information
  synced_wrf = sync_wrf_namelist(os.path.join(args.job_dir, 'wps'))
  synced_arwpost = sync_arwpost_namelist(os.path.join(args.job_dir, 'wps'))
