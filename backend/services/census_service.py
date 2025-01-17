import requests
from config import config
import shapely
from .us_counties import counties_gdf
# US Census ACS 5-year 2020 as an example
# doc: https://www.census.gov/data/developers/data-sets/acs-5year.html
CENSUS_BASE_URL = "https://api.census.gov/data/2020/acs/acs5"

def get_county_population(state_fips, county_fips):
    """
    根据州代码(state_fips) + 县代码(county_fips)，
    调用Census Bureau API获取该county的人口总数
    B01003_001E = total population 
    """
    params = {
        "get": "NAME,B01003_001E",
        "for": f"county:{county_fips}",
        "in": f"state:{state_fips}",
        "key": config.CENSUS_API_KEY
    }
    try:
        r = requests.get(CENSUS_BASE_URL, params=params, timeout=10)
        data = r.json()
        if len(data) > 1:
            row = data[1]
            county_name = row[0]
            population = int(row[1])
            return {
                "countyName": county_name,
                "population": population
            }
        else:
            return {"error": "No county data found from Census."}
    except Exception as e:
        return {"error": f"Census API failed: {str(e)}"}

def get_demographic_for_bbox(bbox):
    # TODO: 你可以写一个逻辑: 根据bbox中心点 -> Reverse geocode -> 得到County fips
    # 下面纯硬编码, 假设返回 state_fips=06 (加州), county_fips=001 (Alameda)
    # 真实生产中要做: 1) reverse geocode -> get (state_fips, county_fips) 2) get_county_population
    # state_fips = "06"
    # county_fips = "001"
    # result = get_county_population(state_fips, county_fips)
    # return result
    poly = shapely.geometry.box(*bbox)  # (minx,miny, maxx,maxy)
    center = poly.centroid

    # counties_gdf = 预先加载的 County shapefile (带STATEFP, COUNTYFP)
    matched = counties_gdf[counties_gdf.geometry.contains(center)]
    if len(matched) == 1:
        row = matched.iloc[0]
        state_fips = row['STATEFP']
        county_fips = row['COUNTYFP']
        return get_county_population(state_fips, county_fips)
    else:
        return {"error": "无法匹配到唯一county"}
