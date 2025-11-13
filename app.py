from flask import Flask, render_template, request, redirect, jsonify
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from routes.search import search_bp
from datetime import datetime, date, timedelta
from models import db, User, Plant, FavoritePlant, WateringSchedule, FertilizationSchedule

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your-secret-key'

db.init_app(app)
from flask_migrate import Migrate
migrate = Migrate(app, db)

#для авторизации
login_manager = LoginManager()
login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

#главная страница
@app.route('/')
def index():
    return render_template('index.html')

#апи регистрация
@app.route('/api/register', methods=['POST'])
def api_register():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({
            'success' : False,
            'message' : 'Эта почта уже зарегистрирована!'
        }), 400
    try:
        user = User(name=name, email=email, password=password)
        db.session.add(user)
        db.session.commit()

        login_user(user)

        return jsonify({
            'success': True, 
            'message': 'Регистрация успешна!'
        })
    except Exception as e:
        db.session.rollback()
        print(f'Ошибка БД: {e}')
        return jsonify({
            'success' : False,
            'message' : 'Ошибка БД!'
        }), 400

#апи логина
@app.route('/api/login', methods = ['POST'])
def api_login():
    email = request.form.get('email')
    password = request.form.get('password')

    user = User.query.filter_by(email=email).first()

    if user:
        if password == user.password:
            login_user(user)
            return jsonify({'success': True, 'message': 'Вход выполнен!'})
        else:
            return jsonify({'success': False, 'message': 'Неверный пароль!'}), 400
    else:
        return jsonify({'success': False, 'message': 'Пользователь не найден'}), 400

#для выхода с аккаунта
@app.route('/api/logout')
def api_logout():
    logout_user()
    return redirect('/')

#апи проверка на админа
@app.route('/api/is_admin')
@login_required
def api_is_admin():
    if current_user.is_admin:
        return jsonify({'is_admin': True})
    else :
        return jsonify({'is_admin': False})

#профиль
@app.route('/profile')
@login_required
def profile():
    def russian_date(datestamp):
        months = {
            1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
            5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа', 
            9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'
        }
        return f'{months[datestamp.month]} {datestamp.year}'
    favorite_count = len(current_user.favorites)
    favorite_plants = current_user.favorites
    plants = [fp.plant for fp in favorite_plants]
    return render_template('profile.html', user=current_user, favorite_count=favorite_count, russian_date=russian_date, favorite_plants=plants)

#мои растения
@app.route('/my-plants')
@login_required
def my_plants():
    favorite_plants = current_user.favorites
    plants = [fp.plant for fp in favorite_plants]
    return render_template('my_plants.html', user_plants=plants)

#посмотреть пользователей(для разработки)
@app.route('/api/debug/users')
def api_debug_users():
    users = User.query.all()
    result = []
    for user in users:
        result.append({
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'password': user.password,
            'date': str(user.date)
        })
    return jsonify(result)

#все растения на сайте
@app.route('/plants')
@login_required
def plants():
    plants = Plant.query.all()

    favorite_plant_ids = [fp.plant_id for fp in current_user.favorites]

    return render_template('plants.html', plants=plants, favorite_plant_ids=favorite_plant_ids)

#апи для добавления в избранное
@app.route('/api/add-to-favorites/<int:plant_id>', methods=['POST'])
@login_required
def api_add_to_favorites(plant_id):
    plant = Plant.query.get(plant_id)
    favorite = FavoritePlant.query.filter_by(
        user_id = current_user.id,
        plant_id = plant_id
    ).first()

    if favorite:
        return jsonify({'success':False, 'message':'Растение уже в избранном'})
    try:
        favorite = FavoritePlant(user_id=current_user.id, plant_id=plant_id)
        db.session.add(favorite)
        db.session.commit()
        
        return jsonify({'success':True, 'message':f'Растение {plant.name} добавлено в избранное'})
    except Exception as e:
        return jsonify({'success':False, 'message':f'Ошибка БД: {str(e)}'}), 500

#апи для удаления из избранного
@app.route('/api/remove-from-favorites/<int:plant_id>', methods=['POST'])
@login_required
def api_remove_from_favorites(plant_id):
    plant = Plant.query.get(plant_id)
    favorite = FavoritePlant.query.filter_by(
        user_id = current_user.id,
        plant_id = plant_id
    ).first()

    if not favorite: return jsonify({'success':False, 'message':'Растение не найдено в избранном'}), 404
    try:
        WateringSchedule.query.filter_by(
            user_id=current_user.id,
            plant_id=plant_id
        ).delete()
        FertilizationSchedule.query.filter_by(
            user_id=current_user.id,
            plant_id=plant_id
        ).delete()
        db.session.delete(favorite)
        db.session.commit()

        return jsonify({'success':True, 'message':f'Растение {plant.name} удалено из избоанного'})
    except Exception as e:
        return jsonify({'success':False, 'message':f'Ошибка БД: {str(e)}'}), 500

#для идентификации через plantnet api
#пока на blueprint перенес только это
# !!! РАБОТАЕТ ТОЛЬКО ЧЕРЕЗ НЕ ПРОКСИ ИЛИ ВПН, НЕ ДОСТУПНО В РОССИИ !!!
# Пример работы dev/search_test.mp4
app.register_blueprint(search_bp)
@app.route('/search')
@login_required
def search():
    return render_template('search.html')

#страница для добавления растений(только для админа)
@app.route('/add-plant')
@login_required
def add_plant():
    if (current_user.is_admin):
        return render_template('add_plant.html')
    else:
        return render_template('index.html')

#апи для загрузки нового растения в бд(только для админа)
@app.route('/api/add-plant', methods=['POST'])
@login_required
def api_add_plant():
    if (current_user.is_admin):
        form_data = request.form.to_dict()
        try:
            plant = Plant(
                name=form_data['name'], latin_name=form_data['latin_name'],
                description=form_data['description'], image_url=form_data['image_url'],
                plant_type=form_data['plant_type'], lifespan=form_data['lifespan'],
                light=form_data['light'], difficulty=form_data['difficulty'],
                care_instructions=form_data.get('care_instructions'), 
                water_frequency=form_data['water_frequency'], temperature=f"{form_data['temperature']}°C"
            )
    
            db.session.add(plant)   
            db.session.commit()
            return jsonify({
                'success' : True, 'message' : 'Растение добавлено!'
            })
        except Exception as e:
            jsonify({'success':False, 'message':f'Ошибка БД: {str(e)}'}), 500

#график
@app.route('/calendar')
@login_required
def calendar():
    return render_template('calendar.html')

#апи для получения json списка избранных растений пользователя
@app.route('/api/favorite-plants')
@login_required
def api_favorite_plants():
    favorite_plants = current_user.favorites
    plants = [fp.plant for fp in favorite_plants]
    try:
        return jsonify([
            {
                'id': plant.id,
                'name': plant.name
            }
            for plant in plants
        ])
    except Exception as e:
        return jsonify({'success':False, 'message':f'Ошибка БД: {str(e)}'}),500

#апи для отображения дат полива в графике
@app.route('/api/watering-schedule')
@login_required
def api_watering_schedule():
    try:
        year = int(request.args.get('year', datetime.now().year))
        month = int(request.args.get('month', datetime.now().month))
        
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)

        schedules = WateringSchedule.query.filter(
            WateringSchedule.user_id == current_user.id,
            WateringSchedule.date >= start_date,
            WateringSchedule.date < end_date
        ).all()

        events = []
        for schedule in schedules:
            plant = Plant.query.get(schedule.plant_id)
            if plant:
                events.append({
                    'date': schedule.date.isoformat(),
                    'plant_id': schedule.plant_id,
                    'plant_name': plant.name
                })

        return jsonify(events)

    except Exception as e:
        return jsonify({'success': False, 'message': 'Ошибка при загрузки графика'}), 500

#апи для сохранения графика полива с промежутками
@app.route('/api/save-watering', methods=['POST'])
@login_required
def save_watering():
    try:
        data = request.get_json()
        start_date_str = data.get('date')
        plant_id = data.get('plant_id')
        repeat_days = data.get('repeat_days', 7)

        is_favorite = FavoritePlant.query.filter_by(
            user_id=current_user.id,
            plant_id=plant_id
        ).first()

        if not is_favorite:
            return jsonify({
                'success': False, 'message': 'Растение не найдено в избранных'}), 403

        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()

        WateringSchedule.query.filter_by(
            user_id=current_user.id,
            plant_id=plant_id
        ).delete()

        dates_to_add = []
        current_date = start_date
        end_date = start_date + timedelta(days=180)

        while current_date <= end_date:
            dates_to_add.append(current_date)
            current_date += timedelta(days=repeat_days)

        for date in dates_to_add:
            watering = WateringSchedule(
                user_id=current_user.id,
                plant_id=plant_id,
                date=date,
                repeat_interval=repeat_days
            )
            db.session.add(watering)

        db.session.commit()
        return jsonify({
            'success': True, 
            'message': f'График полива для "{Plant.query.get(plant_id).name}" установлен'
        })

    except Exception as e:
        return jsonify({'success': False, 'message': 'Ошибка при сохранении графика'}), 500
    
#апи для получения дат удобрения
@app.route('/api/fertilization-schedule')
@login_required
def api_fertilization_schedule():
    try:
        year = int(request.args.get('year', datetime.now().year))
        month = int(request.args.get('month', datetime.now().month))

        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)

        schedules = FertilizationSchedule.query.filter(
            FertilizationSchedule.user_id == current_user.id,
            FertilizationSchedule.date >= start_date,
            FertilizationSchedule.date < end_date
        ).all()

        events = []
        for schedule in schedules:
            plant = Plant.query.get(schedule.plant_id)
            if plant:
                events.append({
                    'date': schedule.date.isoformat(),
                    'plant_id': schedule.plant_id,
                    'plant_name': plant.name,
                    'repeat_interval': schedule.repeat_interval,
                    'type': 'fertilization'
                })

        return jsonify(events)

    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка при загрузки графика'}), 500

#апи для сохранения графика удобрений
@app.route('/api/save-fertilization', methods=['POST'])
@login_required
def save_fertilization():
    try:
        data = request.get_json()
        start_date_str = data.get('date')
        plant_id = data.get('plant_id')
        repeat_days = data.get('repeat_days', 14)

        if not start_date_str or not plant_id:
            return jsonify({'success': False, 'message': 'Требуется дата и растение'}), 400

        if not FavoritePlant.query.filter_by(user_id=current_user.id, plant_id=plant_id).first():
            return jsonify({'success': False, 'message': 'Растение не найдено'}), 403

        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()

        FertilizationSchedule.query.filter_by(
            user_id=current_user.id,
            plant_id=plant_id
        ).delete()

        current_date = start_date
        end_date = start_date + timedelta(days=180)
        events = []

        while current_date <= end_date:
            events.append(current_date)
            current_date += timedelta(days=repeat_days)

        for date in events:
            fert = FertilizationSchedule(
                user_id=current_user.id,
                plant_id=plant_id,
                date=date,
                repeat_interval=repeat_days
            )
            db.session.add(fert)

        db.session.commit()
        plant_name = Plant.query.get(plant_id).name

        return jsonify({
            'success': True,
            'message': f'Удобрение для "{plant_name}" установлено (каждые {repeat_days} дней)'
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка при сохранении графика'}), 500
if __name__ == '__main__':

    app.run()



