from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
from dotenv import load_dotenv
import os
import json
from datetime import datetime, timedelta
import httpx
import base64
import hashlib
import secrets

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

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

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    if 'user_id' not in session:
        return None
    response = client.get(f"/rest/v1/users", params={"id": f"eq.{session['user_id']}", "select": "*"})
    if response.status_code == 200 and response.json():
        return response.json()[0]
    return None

def hash_password(password):
    """해시 함수로 비밀번호를 안전하게 저장"""
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000
    )
    return base64.b64encode(salt + key).decode('utf-8')

def verify_password(stored_password, provided_password):
    """저장된 해시와 제공된 비밀번호를 비교"""
    try:
        decoded = base64.b64decode(stored_password.encode('utf-8'))
        salt = decoded[:32]
        stored_key = decoded[32:]
        new_key = hashlib.pbkdf2_hmac(
            'sha256',
            provided_password.encode('utf-8'),
            salt,
            100000
        )
        return stored_key == new_key
    except:
        return False

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    try:
        # 이메일 중복 체크
        existing_user = client.get(
            f"/rest/v1/users",
            params={"email": f"eq.{email}", "select": "id"}
        ).json()
        
        if existing_user:
            return jsonify({'error': 'Email already exists'}), 400
        
        # 비밀번호 해시
        hashed_password = hash_password(password)
        
        # 사용자 생성
        user_response = client.post(
            "/rest/v1/users",
            json={
                "email": email,
                "password_hash": hashed_password
            }
        )
        
        if user_response.status_code != 201:
            return jsonify({'error': 'Registration failed'}), 400
            
        user_data = user_response.json()[0]
        user_id = user_data['id']
        
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
        
        # 세션 생성
        session['user_id'] = user_id
        session.permanent = True
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    try:
        # 사용자 정보 가져오기
        user_response = client.get(
            f"/rest/v1/users",
            params={"email": f"eq.{email}", "select": "*"}
        )
        
        if user_response.status_code != 200:
            return jsonify({'error': 'Failed to get user data'}), 400
            
        user_data = user_response.json()
        if not user_data:
            return jsonify({'error': 'User not found'}), 404
            
        user = user_data[0]
        
        # 비밀번호 검증
        if not verify_password(user['password_hash'], password):
            return jsonify({'error': 'Invalid credentials'}), 401
            
        # 세션 생성
        session['user_id'] = user['id']
        session.permanent = True
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/logout')
@login_required
def logout():
    session.clear()
    return jsonify({'success': True}), 200

@app.route('/character')
@login_required
def get_character():
    try:
        response = client.get(
            f"/rest/v1/characters",
            params={"user_id": f"eq.{session['user_id']}", "select": "*"}
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
            params={"user_id": f"eq.{session['user_id']}", "select": "*"}
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
