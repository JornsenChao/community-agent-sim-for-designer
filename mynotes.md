# create backend/requirements.txt:

'''
pip-chill | Out-File -Encoding utf8 requirements.txt
or
pip freeze | Out-File -Encoding UTF8 requirements.txt
'''

# docker-postgis-flask

start docker
'''
cd backend
docker-compose build #
docker-compose up -d
'''

stop docker
'''
docker-compose stop
docker-compose rm
'''

# postgresql db:

## 1. PostGIS 核心元数据

### 1.1 geometry_columns 与 geography_columns

geometry_columns：PostGIS 会在此表中记录哪些普通表里有 geometry 类型的字段(如 geometry(Point,4326)等)，以便地理软件或库能快速知道“哪些表是空间表”。
geography_columns：类似，但记录的是 geography 类型的字段(一种更高层次的地理数据类型，自动做大圆测量)。
它们通常由 PostGIS 自动维护；并不是你直接存放数据的地方，只是元数据索引。

### 1.2 spatial_ref_sys

这个表存放了**坐标参考系统(SRID)**的定义，例如 EPSG:4326 对应 WGS84 坐标系。
里面每条记录包含 srid, auth_name, auth_srid, proj4text, srtext 等字段；
当你在数据库里存 geometry(… ,4326) 之类，PostGIS 就知道去 spatial_ref_sys 查相关坐标信息。
不是你自己要手动编辑的，PostGIS 默认会加载非常多的坐标系定义进去。

## 2. Tiger\* 相关 schema、表

你可以看到 tiger schema 下有很多表：addr, faces, edges, place, tract, zcta5 等，以及函数 geocode_settings, loader_platform 等。这是**“PostGIS Tiger Geocoder”**扩展（或 postgis_tiger_geocoder）带来的：

### 2.1 Tiger Geocoder 是什么

一个可以在 PostgreSQL + PostGIS 内安装的扩展，包含美国的地理信息(州、县、邮编、道路等 TIGER/Line 数据)和函数，用于地址解析(geocoding)或逆向地理编码(反查地址)。
这些表承载了从 US Census TIGER/Line 导入的底层数据(如 edges=道路, faces=面, place=城镇/城市, zcta5=ZIP code 区划, tract=人口普查区块等)。
有了它，你可在数据库里直接做“给定一个地址字符串 → 自动查找坐标”，或“坐标 → 逆查对应地址/街道/邮编”等操作。

### 2.2 tiger schema 下各表的典型作用

state, county, tract, bg, zcta5, place……存放全美各州、县、普查区、邮编区、城市区域等的多边形边界；
edges、faces 里可能存道路的线要素、土地分块等；
loader*\* / geocode_settings*\* 表主要是内部配置和元数据，让 geocoder 知道如何从 CSV/Shape 文件加载新的 TIGER 数据。
你看到的 “pg_database”, “postgres” schema, “public” schema, “tiger” schema, 以及 “topology” schema，也都是 PostGIS 默认或 Tiger 扩展必备的命名空间，里头有各种函数/表/视图。

### 简单来说：

这些 tiger._ 表是美国国家级地理数据(行政区域、道路地址等) + 地理编码功能；
如果你只需要在数据库中存自己的建筑/道路数据，可以在 public schema 下建表(或者你自定义 schema)，不必碰 tiger._。
如果你想用地址解析(给出字符串“1600 Pennsylvania Ave, Washington DC”→ 数据库里找出坐标), tiger geocoder 就派上用场。
