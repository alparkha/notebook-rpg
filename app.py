from flask import Flask, render_template, request, jsonify, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from dotenv import load_dotenv
import os
import json
from datetime import datetime
import httpx

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Supabase 설정
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# HTTP 클라이언트 설정
client = httpx.Client(
    base_url=SUPABASE_URL,
    headers={
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
)

# Login manager 설정
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
    response = client.get(f"/rest/v1/users", params={"id": f"eq.{user_id}", "select": "*"})
    if response.status_code == 200 and response.json():
        return User(response.json()[0])
    return None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    try:
        # 사용자 등록
        auth_response = client.post(
            "/auth/v1/signup",
            json={"email": email, "password": password}
        )
        auth_data = auth_response.json()
        
        if auth_response.status_code != 200:
            return jsonify({'error': auth_data.get('msg', 'Registration failed')}), 400
        
        user_id = auth_data['user']['id']
        
        # 캐릭터 생성
        character_response = client.post(
            "/rest/v1/characters",
            json={
                'user_id': user_id,
                'level': 1,
                'exp': 0,
                'hp': 100,
                'attack': 10,
                'defense': 5,
                'gold': 0,
                'fatigue': 0
            }
        )
        
        if character_response.status_code != 201:
            return jsonify({'error': 'Failed to create character'}), 400
            
        character_data = character_response.json()[0]
        
        # 사용자 정보 업데이트
        update_response = client.patch(
            f"/rest/v1/users",
            params={"id": f"eq.{user_id}"},
            json={'character_id': character_data['id']}
        )
        
        if update_response.status_code != 200:
            return jsonify({'error': 'Failed to update user'}), 400
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    try:
        # 로그인
        auth_response = client.post(
            "/auth/v1/token",
            params={"grant_type": "password"},
            json={"email": email, "password": password}
        )
        
        if auth_response.status_code != 200:
            return jsonify({'error': 'Invalid credentials'}), 401
            
        auth_data = auth_response.json()
        user_id = auth_data['user']['id']
        
        # 사용자 정보 가져오기
        user_response = client.get(
            f"/rest/v1/users",
            params={"id": f"eq.{user_id}", "select": "*"}
        )
        
        if user_response.status_code != 200:
            return jsonify({'error': 'Failed to get user data'}), 400
            
        user_data = user_response.json()[0]
        user = User(user_data)
        login_user(user)
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({'success': True}), 200

@app.route('/character')
@login_required
def get_character():
    try:
        response = client.get(
            f"/rest/v1/characters",
            params={"user_id": f"eq.{current_user.id}", "select": "*"}
        )
        
        if response.status_code != 200:
            return jsonify({'error': 'Failed to get character data'}), 400
            
        character_data = response.json()
        if character_data:
            return jsonify(character_data[0]), 200
        return jsonify({'error': 'Character not found'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/battle', methods=['POST'])
@login_required
def battle():
    data = request.get_json()
    monster_grade = data.get('monster_grade')
    player_choice = data.get('choice')
    
    try:
        response = client.get(
            f"/rest/v1/characters",
            params={"user_id": f"eq.{current_user.id}", "select": "*"}
        )
        
        if response.status_code != 200:
            return jsonify({'error': 'Failed to get character data'}), 400
            
        character_data = response.json()
        if not character_data:
            return jsonify({'error': 'Character not found'}), 404
            
        # 전투 로직 구현
        # TODO: Implement battle logic
        
        return jsonify({
            'success': True,
            'result': 'win',
            'rewards': {
                'exp': 100,
                'gold': 50
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)
