# services/census_service.py

import requests
import geopandas as gpd
from shapely.geometry import box
from config import config
from .us_counties import counties_gdf

CENSUS_BASE_URL = "https://api.census.gov/data/2020/acs/acs5"

def _get_county_population(state_fips, county_fips):
    """
    调用 Census Bureau API 获取某county人口 (B01003_001E)
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
            return {"countyName": county_name, "population": population}
        else:
            return {"countyName": None, "population": 0}
    except Exception as e:
        print("Census API error:", e)
        return {"countyName": None, "population": 0}

def get_demographic_for_bbox(minx, miny, maxx, maxy, method="weighted"):
    """
    在用户选的 bounding box 上:
    1) 与 counties_gdf 做叠加, 找到所有落在bbox内的县
    2) 分别查人口, 然后根据 area 占比加权合并(或返回列表)

    :param method: "weighted" => 返回一个总人口(加权),
                   "largest" => 只返回面积最大的那个county,
                   "list" => 返回一个列表列出每个county info
    """

    region_polygon = box(minx, miny, maxx, maxy)

    # 构建 region_gdf
    region_gdf = gpd.GeoDataFrame(
        {'id': [1]},
        geometry=[region_polygon],
        crs="EPSG:4326"
    )

    # 做 overlay intersection
    intersected = gpd.overlay(counties_gdf, region_gdf, how='intersection')
    if len(intersected) == 0:
        return {
            "info": "No county found for bounding box",
            "totalPopulation": 0
        }

    # 计算每个碎片面积
    # shapely 2.0 area => degrees^2 并不是真实m^2, 
    #  若要准确面积, 先 to_crs一个投影坐标(如 EPSG:5070 for US).
    # 这里演示就用 degrees^2, 不那么准确
    intersected["area"] = intersected.geometry.area

    # "list" 模式 => 直接逐个 county_tract
    # "weighted" => 先按 county 分组, 计算总 area
    #  code below:
    group_cols = ["STATEFP", "COUNTYFP"]
    grouped = intersected.groupby(group_cols)["area"].sum().reset_index()
    total_area = grouped["area"].sum()

    # fetch census population for each county, do weighted
    results = []
    for idx, row in grouped.iterrows():
        st = row["STATEFP"]
        ct = row["COUNTYFP"]
        area_part = row["area"]
        popinfo = _get_county_population(st, ct)  # { countyName, population }
        portion = (area_part / total_area) if total_area > 0 else 0
        results.append({
            "state_fips": st,
            "county_fips": ct,
            "countyName": popinfo["countyName"],
            "population": popinfo["population"],
            "areaPart": area_part,
            "areaRatio": portion
        })

    if method == "weighted":
        # 做加权人口
        weighted_population = 0
        # countyNameList = []
        for item in results:
            weighted_population += item["population"] * item["areaRatio"]
            # countyNameList.append(item["countyName"])
        return {
            "method": "weighted",
            "estimatedPopulation": int(weighted_population),
            "details": results
        }
    elif method == "largest":
        # 找出 areaRatio 最大的一条
        largest_row = max(results, key=lambda x: x["areaRatio"])
        return {
            "method": "largest",
            "dominantCountyName": largest_row["countyName"],
            "population": largest_row["population"],
            "details": results
        }
    else:  # "list"
        return {
            "method": "list",
            "counties": results
        }
