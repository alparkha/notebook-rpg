from flask import Flask, render_template, request, jsonify, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from dotenv import load_dotenv
from supabase import create_client, Client
import os
import json
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Supabase 설정
supabase: Client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
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
    user_data = supabase.table('users').select('*').eq('id', user_id).execute()
    if not user_data.data:
        return None
    return User(user_data.data[0])

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
        auth_response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        
        # 캐릭터 생성
        character = supabase.table('characters').insert({
            'user_id': auth_response.user.id,
            'level': 1,
            'exp': 0,
            'hp': 100,
            'attack': 10,
            'defense': 5,
            'gold': 0,
            'fatigue': 0
        }).execute()
        
        # 사용자 정보 업데이트
        supabase.table('users').update({
            'character_id': character.data[0]['id']
        }).eq('id', auth_response.user.id).execute()
        
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    try:
        auth_response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        user_data = supabase.table('users').select('*').eq('id', auth_response.user.id).execute()
        if user_data.data:
            user = User(user_data.data[0])
            login_user(user)
            return jsonify({'success': True}), 200
        return jsonify({'error': 'User not found'}), 404
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
        character = supabase.table('characters').select('*').eq('user_id', current_user.id).execute()
        if character.data:
            return jsonify(character.data[0]), 200
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
        character = supabase.table('characters').select('*').eq('user_id', current_user.id).single().execute()
        
        if not character.data:
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
