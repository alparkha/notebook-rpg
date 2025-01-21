from flask import Flask, jsonify, request, render_template, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from datetime import datetime
import os
from dotenv import load_dotenv
import random
from supabase import create_client, Client
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')

# Supabase 설정
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data['id']
        self.email = user_data['email']
        self.character_id = user_data.get('character_id')

@login_manager.user_loader
def load_user(user_id):
    try:
        response = supabase.table('users').select('*').eq('id', user_id).execute()
        if response.data:
            return User(response.data[0])
    except Exception as e:
        print(f"Error loading user: {e}")
    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            response = supabase.table('users').select('*').eq('email', email).execute()
            if response.data and check_password_hash(response.data[0]['password'], password):
                user = User(response.data[0])
                login_user(user)
                return redirect(url_for('game'))
        except Exception as e:
            print(f"Login error: {e}")
        
        return 'Invalid credentials', 401
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        hashed_password = generate_password_hash(password)
        
        try:
            # 사용자 생성
            user_data = {
                'email': email,
                'password': hashed_password
            }
            response = supabase.table('users').insert(user_data).execute()
            
            if response.data:
                # 캐릭터 생성
                character_data = {
                    'user_id': response.data[0]['id'],
                    'level': 1,
                    'exp': 0,
                    'hp': 100,
                    'attack': 10,
                    'defense': 5,
                    'gold': 0,
                    'fatigue': 0
                }
                char_response = supabase.table('characters').insert(character_data).execute()
                
                # 사용자 정보 업데이트
                supabase.table('users').update({
                    'character_id': char_response.data[0]['id']
                }).eq('id', response.data[0]['id']).execute()
                
                user = User(response.data[0])
                login_user(user)
                return redirect(url_for('game'))
        except Exception as e:
            print(f"Registration error: {e}")
            return str(e), 400
        
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/game')
@login_required
def game():
    return render_template('game.html')

@app.route('/api/character')
@login_required
def get_character():
    try:
        response = supabase.table('characters').select('*').eq('user_id', current_user.id).execute()
        if response.data:
            return jsonify(response.data[0])
        return 'Character not found', 404
    except Exception as e:
        print(f"Error getting character: {e}")
        return str(e), 500

@app.route('/api/minigames')
@login_required
def get_available_minigames():
    try:
        response = supabase.table('characters').select('*').eq('user_id', current_user.id).execute()
        if response.data:
            character = response.data[0]
            available_games = {
                'capsule': {'required_level': 5, 'name': '캡슐 뽑기', 'cost': 100},
                'arcade': {'required_level': 10, 'name': '쪼그려 앉아 하는 오락실', 'cost': 200},
                'pets': {'required_level': 15, 'name': '병아리/메추리 키우기', 'cost': 300},
                'phone': {'required_level': 20, 'name': '선생님 몰래 핸드폰하기', 'cost': 150},
                'gambling': {'required_level': 25, 'name': '문방구 도박게임', 'cost': 500}
            }
            
            return jsonify({
                'games': available_games,
                'fatigue': character['fatigue'],
                'gold': character['gold']
            })
        return 'Character not found', 404
    except Exception as e:
        print(f"Error getting available minigames: {e}")
        return str(e), 500

@app.route('/api/play_minigame', methods=['POST'])
@login_required
def play_minigame():
    game_type = request.json.get('game_type')
    
    try:
        response = supabase.table('characters').select('*').eq('user_id', current_user.id).execute()
        if response.data:
            character = response.data[0]
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
            
            if character['level'] < req['level']:
                return jsonify({'error': '레벨이 부족합니다.'}), 400
            
            if character['gold'] < req['cost']:
                return jsonify({'error': '골드가 부족합니다.'}), 400
            
            # 골드 차감
            supabase.table('characters').update({
                'gold': character['gold'] - req['cost']
            }).eq('user_id', current_user.id).execute()
            
            # 피로도 회복
            supabase.table('characters').update({
                'fatigue': max(0, character['fatigue'] - req['fatigue_recovery'])
            }).eq('user_id', current_user.id).execute()
            
            # 보상 지급
            rewards = generate_minigame_rewards(game_type, character['level'])
            
            # 플레이 기록 저장
            supabase.table('characters').update({
                'mini_games_played': {game_type: character.get('mini_games_played', {}).get(game_type, 0) + 1}
            }).eq('user_id', current_user.id).execute()
            
            return jsonify({
                'success': True,
                'rewards': rewards,
                'new_fatigue': max(0, character['fatigue'] - req['fatigue_recovery']),
                'new_gold': character['gold'] - req['cost']
            })
        return 'Character not found', 404
    except Exception as e:
        print(f"Error playing minigame: {e}")
        return str(e), 500

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
    app.run(debug=True)
