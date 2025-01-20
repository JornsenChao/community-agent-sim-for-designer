# models.py
# 用 geoalchemy2.Geometry 存储地理数据(srid=4326 代表经纬度 WGS84坐标)

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, ForeignKey
from geoalchemy2 import Geometry

db = SQLAlchemy()
Base = declarative_base()

class GeoFeature(db.Model):
    __tablename__ = 'geo_features'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=True)
    # geometry 列, 存储多边形/线/点, SRID=4326
    geom = db.Column(Geometry('GEOMETRY', srid=4326), nullable=False)

    def __repr__(self):
        return f"<GeoFeature id={self.id} name={self.name}>"

class OSMBuilding(db.Model):
    __tablename__ = 'osm_buildings'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bounding_box = db.Column(db.String(200), nullable=False)  # "minx,miny,maxx,maxy"
    osm_id = db.Column(db.String(200), nullable=True)      # e.g. "way/123456"
    name = db.Column(db.String(200), nullable=True)       # building name if any
    building_type = db.Column(db.String(100), nullable=True)
    geom = db.Column(Geometry('MULTIPOLYGON', srid=4326), nullable=False)

class OSMRoad(db.Model):
    __tablename__ = 'osm_roads'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bounding_box = db.Column(db.String(200), nullable=False)
    osm_id = db.Column(db.String(200), nullable=True)  # e.g. "way/765432"
    name = db.Column(db.String(200), nullable=True)
    road_type = db.Column(db.String(100), nullable=True)  # from highway=...
    oneway = db.Column(db.Boolean, nullable=True)
    lanes = db.Column(db.Float, nullable=True)  # if numeric
    geom = db.Column(Geometry('MULTILINESTRING', srid=4326), nullable=False)

class Project(db.Model):
    """
    新增Project模型，替代你之前用dict存储. 
    """
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(200), nullable=True)
    boundary_geom = db.Column(Geometry('MULTIPOLYGON', srid=4326), nullable=True)
    # 你也可以记录 bounding box 或 other details

class Agent(db.Model):
    """
    用于存储每个Agent的地理与属性信息
    """
    __tablename__ = 'agents'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    project_id = db.Column(db.Integer, ForeignKey('projects.id'), nullable=False)
    # 所属项目

    # 地理位置: 住址, 工作(或通勤)地址
    home_geom = db.Column(Geometry('POINT', srid=4326), nullable=True)
    work_geom = db.Column(Geometry('POINT', srid=4326), nullable=True)

    # Census tract id
    home_tract = db.Column(db.String(50), nullable=True)
    work_tract = db.Column(db.String(50), nullable=True)

    # AI生成的属性
    name = db.Column(db.String(100), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    occupation = db.Column(db.String(100), nullable=True)
    background_story = db.Column(db.Text, nullable=True)

    # 还可加更多字段: income, dailyRoutine, etc

    def __repr__(self):
        return f"<Agent id={self.id} project_id={self.project_id}>"