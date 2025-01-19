# models.py
# 用 geoalchemy2.Geometry 存储地理数据(srid=4326 代表经纬度 WGS84坐标)

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
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
    geom = db.Column(Geometry('POLYGON', srid=4326), nullable=False)

class OSMRoad(db.Model):
    __tablename__ = 'osm_roads'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bounding_box = db.Column(db.String(200), nullable=False)
    osm_id = db.Column(db.String(200), nullable=True)  # e.g. "way/765432"
    name = db.Column(db.String(200), nullable=True)
    road_type = db.Column(db.String(100), nullable=True)  # from highway=...
    oneway = db.Column(db.Boolean, nullable=True)
    lanes = db.Column(db.Float, nullable=True)  # if numeric
    geom = db.Column(Geometry('LINESTRING', srid=4326), nullable=False)