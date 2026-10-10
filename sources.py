"""Where the bake keeps downloads (CACHE) and writes results (OUT). HKB_DATA moves both (default: ./data next to this file)."""
import os
DATA = os.environ.get('HKB_DATA', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data'))
CACHE, OUT = os.path.join(DATA, 'cache'), os.path.join(DATA, 'out')
BUILDINGS = 'https://portal.csdi.gov.hk/server/rest/services/common/landsd_rcd_1637211194312_35158/MapServer/0/query'
