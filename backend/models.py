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
