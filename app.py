from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime
import os
from dotenv import load_dotenv
import pymysql
import random

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')

# PlanetScale 데이터베이스 설정
DATABASE_URL = os.getenv('DATABASE_URL', 'mysql+pymysql://root:root@localhost/notebook_rpg')
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    oauth_provider = db.Column(db.String(20), nullable=False)
    character = db.relationship('Character', backref='user', lazy=True, uselist=False)

class Character(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    level = db.Column(db.Integer, default=1)
    exp = db.Column(db.Integer, default=0)
    hp = db.Column(db.Integer, default=100)
    attack = db.Column(db.Integer, default=10)
    defense = db.Column(db.Integer, default=5)
    gold = db.Column(db.Integer, default=0)
    fatigue = db.Column(db.Integer, default=0)  # 피로도 (0-100)
    last_fatigue_reset = db.Column(db.DateTime, default=datetime.utcnow)  # 피로도 마지막 초기화 시간
    mini_games_played = db.Column(db.JSON, default=dict)  # 미니게임 플레이 기록

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('intro.html')

@app.route('/game')
@login_required
def game():
    return render_template('game.html')

@app.route('/api/character')
@login_required
def get_character():
    character = current_user.character
    if not character:
        character = Character(user_id=current_user.id)
        db.session.add(character)
        db.session.commit()
    
    return jsonify({
        'level': character.level,
        'exp': character.exp,
        'hp': character.hp,
        'attack': character.attack,
        'defense': character.defense,
        'gold': character.gold
    })

@app.route('/api/minigames')
@login_required
def get_available_minigames():
    character = current_user.character
    available_games = {
        'capsule': {'required_level': 5, 'name': '캡슐 뽑기', 'cost': 100},
        'arcade': {'required_level': 10, 'name': '쪼그려 앉아 하는 오락실', 'cost': 200},
        'pets': {'required_level': 15, 'name': '병아리/메추리 키우기', 'cost': 300},
        'phone': {'required_level': 20, 'name': '선생님 몰래 핸드폰하기', 'cost': 150},
        'gambling': {'required_level': 25, 'name': '문방구 도박게임', 'cost': 500}
    }
    
    return jsonify({
        'games': available_games,
        'fatigue': character.fatigue,
        'gold': character.gold
    })

@app.route('/api/play_minigame', methods=['POST'])
@login_required
def play_minigame():
    game_type = request.json.get('game_type')
    character = current_user.character
    
    # 게임별 비용과 레벨 요구사항 확인
    game_requirements = {
        'capsule': {'level': 5, 'cost': 100, 'fatigue_recovery': 10},
        'arcade': {'level': 10, 'cost': 200, 'fatigue_recovery': 15},
        'pets': {'level': 15, 'cost': 300, 'fatigue_recovery': 20},
        'phone': {'level': 20, 'cost': 150, 'fatigue_recovery': 25},
        'gambling': {'level': 25, 'cost': 500, 'fatigue_recovery': 30}
    }
    
    req = game_requirements.get(game_type)
    if not req:
        return jsonify({'error': '잘못된 게임 타입입니다.'}), 400
    
    if character.level < req['level']:
        return jsonify({'error': '레벨이 부족합니다.'}), 400
    
    if character.gold < req['cost']:
        return jsonify({'error': '골드가 부족합니다.'}), 400
    
    # 골드 차감
    character.gold -= req['cost']
    
    # 피로도 회복
    character.fatigue = max(0, character.fatigue - req['fatigue_recovery'])
    
    # 보상 지급
    rewards = generate_minigame_rewards(game_type, character.level)
    
    # 플레이 기록 저장
    if not character.mini_games_played:
        character.mini_games_played = {}
    character.mini_games_played[game_type] = character.mini_games_played.get(game_type, 0) + 1
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'rewards': rewards,
        'new_fatigue': character.fatigue,
        'new_gold': character.gold
    })

def generate_minigame_rewards(game_type, player_level):
    rewards = {
        'items': [],
        'gold': 0,
        'exp': 0
    }
    
    if game_type == 'capsule':
        # 캡슐 뽑기: 랜덤 장비 or 강화권
        if random.random() < 0.3:
            rewards['items'].append({'type': 'equipment', 'level': max(1, player_level - 5)})
        else:
            rewards['items'].append({'type': 'enhance_ticket', 'level': max(1, player_level - 5)})
    
    elif game_type == 'arcade':
        # 오락실: 골드 위주 보상
        rewards['gold'] = random.randint(300, 800)
    
    elif game_type == 'pets':
        # 동물 키우기: 경험치 위주 보상
        rewards['exp'] = random.randint(50, 150)
    
    elif game_type == 'phone':
        # 핸드폰: 랜덤 보상
        reward_type = random.choice(['gold', 'exp', 'item'])
        if reward_type == 'gold':
            rewards['gold'] = random.randint(200, 500)
        elif reward_type == 'exp':
            rewards['exp'] = random.randint(30, 100)
        else:
            rewards['items'].append({'type': 'equipment', 'level': max(1, player_level - 3)})
    
    elif game_type == 'gambling':
        # 도박게임: 높은 위험, 높은 보상
        if random.random() < 0.4:  # 40% 확률로 대성공
            rewards['gold'] = random.randint(1000, 2000)
            rewards['items'].append({'type': 'enhance_ticket', 'level': player_level})
        else:  # 60% 확률로 소액 보상
            rewards['gold'] = random.randint(100, 300)
    
    return rewards

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
