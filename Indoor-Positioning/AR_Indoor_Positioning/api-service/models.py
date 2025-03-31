""" models.py file"""
 
# SQLAlchemy Instance Is Imported
from database import db
from sqlalchemy import text
 
# Declaring Model
class Positions(db.Model):
    __tablename__ = "positions"
 
    id = db.Column(db.Integer, primary_key=True)
    x = db.Column(db.REAL, nullable=False, default=0)
    y = db.Column(db.REAL,  nullable=False, default=0)
    z = db.Column(db.REAL,  nullable=False, default=0)
    sqltime = db.Column(db.DateTime(timezone=True), server_default=db.func.current_timestamp())


def get_position(id):
    return Positions.query.filter_by(id=id).first()

def update_position(id, position):
    pos = Positions.query.filter_by(id=id).first()
    if pos is not None:
        pos.x = position['x']
        pos.y = position['y']
        pos.z = position['z']
        db.session.commit()
    else:     
        t = text('INSERT INTO positions (id, x, y, z) VALUES (:val1,:val2,:val3,:val4)')
        db.session.execute(t,{'val1': id,'val2': position['x'],'val3': position['y'],'val4': position['z']})
        db.session.commit()
    
      
