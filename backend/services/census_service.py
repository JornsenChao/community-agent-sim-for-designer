# services/census_service.py

import requests
import geopandas as gpd
from shapely.geometry import box
from config import config
from .us_counties import counties_gdf

CENSUS_BASE_URL = "https://api.census.gov/data/2020/acs/acs5"
CENSUS_GEOCODER_URL = "https://geocoding.geo.census.gov/geocoder/geographies/coordinates"

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

def get_tract_for_point(lat, lng):
    # url = "https://geocoding.geo.census.gov/geocoder/geographies/coordinates"
    params = {
        "x": lng,   # x=经度
        "y": lat,   # y=纬度
        "benchmark": "Public_AR_Current",
        "vintage": "Current_Current",
        "layers": "all",     # 只要Tract
        "format": "json"
    }
    try:
        r = requests.get(CENSUS_GEOCODER_URL, params=params, timeout=10)
        data = r.json()

        # 打印原始响应, 以便调试
        print("DEBUG get_tract_for_point:", data)

        if "result" not in data:
            return None

        geographies = data["result"].get("geographies", {})

        # 1) 尝试 "Census Tracts"
        if "Census Tracts" in geographies and len(geographies["Census Tracts"]) > 0:
            tract_info = geographies["Census Tracts"][0]
            tract = tract_info.get("TRACT")
            county = tract_info.get("COUNTY")
            state = tract_info.get("STATE")
            if tract and county and state:
                return f"{state}-{county}-{tract}"

        # 2) 如果 Tracts 没找到, 看看 "2020 Census Blocks" 里是否也有 'TRACT'
        if "2020 Census Blocks" in geographies and len(geographies["2020 Census Blocks"]) > 0:
            block_info = geographies["2020 Census Blocks"][0]
            tract = block_info.get("TRACT")
            county = block_info.get("COUNTY")
            state = block_info.get("STATE")
            if tract and county and state:
                return f"{state}-{county}-{tract}"

        # 3) 其他 fallback ...
        return None

    except Exception as e:
        print("Error in get_tract_for_point:", e)
        return None
    
def get_tract_demographics(state_fips, county_fips, tract_fips):
    """
    获取跟“公园需求”比较相关的ACS信息, 包括:
      - 人口年龄结构(儿童/老年)
      - 中位年龄
      - 收入
      - 通勤方式(走路/自行车/公共交通/开车)
      - 教育水平(HS or lower, Bachelor's or higher)
    
    使用 2021 ACS 5年数据 (acs5).
    你可按需修改变量, 或扩充更多信息(如残障 B18135, 种族 B02001, 等).
    """

    # 1) 先合并常见的人口&年龄
    # B01001_001E => total pop
    # B01002_001E => median age
    # 儿童(0-14) 需要把 B01001里 male/female 0-4, 5-9, 10-14 全加起来
    # 老年(65+) 需要 male/female 65-69,70-74,75-79,80-84,85+
    pop_variables = [
        "B01001_001E",  # total pop
        "B01002_001E",  # median age

        # male 0-4,5-9,10-14
        "B01001_003E","B01001_004E","B01001_005E",
        # female 0-4,5-9,10-14
        "B01001_027E","B01001_028E","B01001_029E",

        # male 65-69,70-74,75-79,80-84,85+
        "B01001_020E","B01001_021E","B01001_022E","B01001_023E","B01001_024E","B01001_025E",
        # female 65-69,70-74,75-79,80-84,85+
        "B01001_044E","B01001_045E","B01001_046E","B01001_047E","B01001_048E","B01001_049E",
    ]

    # 2) 收入
    # B19013_001E => Median Household Income (in the past 12 months)
    income_variables = ["B19013_001E"]

    # 3) 通勤方式 (B08101 table)
    # B08101_001E => total workers 16+ w/ commute data
    # B08101_009E => walked
    # B08101_010E => bicycle
    # B08101_017E => public transport (sum of subcategories?), or can see separate
    # B08101_019E => drive alone
    # (实际上 B08101 细分非常多, 这里只示例)
    commute_variables = [
        "B08101_001E",  # total
        "B08101_009E",  # walk
        "B08101_010E",  # bike
        "B08101_017E",  # public transport
        "B08101_019E",  # drive alone
    ]

    # 4) 教育水平 (B15003)
    # B15003_001E => total age 25+ for education
    # B15003_017E => HS diploma (or eqv) 
    # B15003_022E => Bachelor's
    # B15003_023E => Master's
    # B15003_024E => Professional school deg
    # B15003_025E => Doctorate
    # 这里只做简单区分 "HS or lower" vs "Bachelor or higher"
    edu_variables = [
        "B15003_001E",  # total
        "B15003_017E",  # HS diploma
        "B15003_022E",  # Bachelor's
        "B15003_023E",  # Master's
        "B15003_024E",  # Professional
        "B15003_025E",  # Doctorate
    ]

    all_vars = pop_variables + income_variables + commute_variables + edu_variables
    var_str = ",".join(all_vars)

    base_url = "https://api.census.gov/data/2021/acs/acs5"
    params = {
        "get": f"NAME,{var_str}",
        "for": f"tract:{tract_fips}",
        "in": f"state:{state_fips} county:{county_fips}",
        "key": config.CENSUS_API_KEY
    }

    try:
        r = requests.get(base_url, params=params, timeout=15)
        data = r.json()

        if len(data) < 2:
            return {"error": "No data returned from Census API."}

        headers = data[0]
        values = data[1]
        result_map = dict(zip(headers, values))

        # === 1) 基础人口 ===
        total_pop = int(result_map.get("B01001_001E", 0))
        median_age = float(result_map.get("B01002_001E", 0.0))

        # sum children 0-14 (male 0-4,5-9,10-14 + female 0-4,5-9,10-14)
        male_0_4   = int(result_map.get("B01001_003E",0))
        male_5_9   = int(result_map.get("B01001_004E",0))
        male_10_14 = int(result_map.get("B01001_005E",0))
        female_0_4   = int(result_map.get("B01001_027E",0))
        female_5_9   = int(result_map.get("B01001_028E",0))
        female_10_14 = int(result_map.get("B01001_029E",0))

        child_sum = (male_0_4 + male_5_9 + male_10_14
                    + female_0_4 + female_5_9 + female_10_14)

        # sum seniors 65+ (male 65-69,... + female 65-69,...)
        male_65plus = sum(int(result_map.get(v,0)) for v in [
            "B01001_020E","B01001_021E","B01001_022E","B01001_023E","B01001_024E","B01001_025E"
        ])
        female_65plus = sum(int(result_map.get(v,0)) for v in [
            "B01001_044E","B01001_045E","B01001_046E","B01001_047E","B01001_048E","B01001_049E"
        ])
        senior_sum = male_65plus + female_65plus

        pct_children = round(child_sum*100.0 / total_pop, 2) if total_pop>0 else 0
        pct_seniors  = round(senior_sum*100.0 / total_pop, 2) if total_pop>0 else 0

        # === 2) 收入 ===
        median_income = int(result_map.get("B19013_001E", 0))

        # === 3) 通勤 ===
        total_commuters = int(result_map.get("B08101_001E", 0))  # total workers 16+
        walk = int(result_map.get("B08101_009E", 0))
        bike = int(result_map.get("B08101_010E", 0))
        pubtrans = int(result_map.get("B08101_017E", 0))
        drive_alone = int(result_map.get("B08101_019E", 0))

        def ratio(part):
            return round(part*100.0 / total_commuters, 1) if total_commuters>0 else 0

        pct_walk_bike       = ratio(walk + bike)
        pct_public_transit  = ratio(pubtrans)
        pct_drive_alone     = ratio(drive_alone)

        # === 4) 教育 ===
        # B15003_001E => total 25+
        # B15003_017E => HS diploma
        # B15003_022E => Bachelor's
        # B15003_023E => Master's
        # B15003_024E => Professional
        # B15003_025E => Doctorate
        edu_total_25plus = int(result_map.get("B15003_001E",0))
        hs_diploma = int(result_map.get("B15003_017E",0))
        bachelors  = int(result_map.get("B15003_022E",0))
        masters    = int(result_map.get("B15003_023E",0))
        prof       = int(result_map.get("B15003_024E",0))
        doctorate  = int(result_map.get("B15003_025E",0))

        # 粗分: 
        # "HS or lower" => (HS diploma or below) / total 
        # "Bachelor or higher" => (bachelor + masters + prof + doc) / total
        # 其实还要加HS以下(多个变量)才能算真实HS or lower, 这里仅做示例
        hs_or_lower = hs_diploma  # 这里简化, 没加 <HS
        bach_or_higher = (bachelors + masters + prof + doctorate)

        pct_hs_or_lower = round(hs_or_lower*100.0 / edu_total_25plus, 1) if edu_total_25plus>0 else 0
        pct_bach_or_higher = round(bach_or_higher*100.0 / edu_total_25plus, 1) if edu_total_25plus>0 else 0

        return {
            "tract_name": result_map.get("NAME","unknown"),
            "total_pop": total_pop,
            "median_age": median_age,
            "pct_children": pct_children,
            "pct_seniors": pct_seniors,
            "median_income": median_income,
            "commute": {
                "pct_walk_bike": pct_walk_bike,
                "pct_public_transit": pct_public_transit,
                "pct_drive_alone": pct_drive_alone
            },
            "education_levels": {
                "pct_hs_or_lower": pct_hs_or_lower,
                "pct_bach_or_higher": pct_bach_or_higher
            }
        }

    except Exception as e:
        return {"error": str(e)}