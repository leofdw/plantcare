# Модели для БД
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(30), nullable=False)
    password = db.Column(db.String(60), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    date = db.Column(db.DateTime, default=datetime.now)

class Plant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    latin_name = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.Text, nullable=False)
    plant_type = db.Column(db.Text, nullable=False)
    lifespan = db.Column(db.Text, nullable=False)
    light = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.Text, nullable=False)
    care_instructions = db.Column(db.Text, default='')
    water_frequency = db.Column(db.Text, nullable=False)
    temperature = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, default=datetime.now)
    full_care_instructions = db.Column(db.Text, default='')#НЕ ИМЕЕТ ФУНКЦИОНАЛА(пока что)

class FavoritePlant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    plant_id = db.Column(db.Integer, db.ForeignKey('plant.id'), nullable = False)
    date_added = db.Column(db.DateTime, default=datetime.now)
    user = db.relationship('User', backref=db.backref('favorites', lazy=True))
    plant = db.relationship('Plant', backref=db.backref('favorited_by', lazy=True))

    __table_args__ = (db.UniqueConstraint('user_id', 'plant_id', name='unique_user_plant'),)

class WateringSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    plant_id = db.Column(db.Integer, db.ForeignKey('plant.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    repeat_interval = db.Column(db.Integer)  # дней между поливами
    
    def __repr__(self):
        return f'<Watering {self.date} for plant {self.plant_id}>'

class FertilizationSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    plant_id = db.Column(db.Integer, db.ForeignKey('plant.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    repeat_interval = db.Column(db.Integer)
    
    def __repr__(self):
        return f'<Fertilization {self.date} for plant {self.plant_id}>'
