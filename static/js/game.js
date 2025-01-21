document.addEventListener('DOMContentLoaded', function() {
    // 캐릭터 정보 로드
    loadCharacterStats();
    
    // 몬스터 생성
    spawnMonster();
    
    // 전투 버튼 이벤트 리스너
    document.querySelectorAll('.battle-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            const playerChoice = e.target.id;
            const computerChoice = getComputerChoice();
            handleBattle(playerChoice, computerChoice);
        });
    });
    
    // 미니게임 정보 로드
    loadAvailableMinigames();
});

async function loadCharacterStats() {
    try {
        const response = await fetch('/api/character');
        const stats = await response.json();
        
        // 스탯 업데이트
        document.getElementById('level').textContent = stats.level;
        document.getElementById('exp').textContent = stats.exp;
        document.getElementById('hp').textContent = stats.hp;
        document.getElementById('attack').textContent = stats.attack;
        document.getElementById('defense').textContent = stats.defense;
        document.getElementById('gold').textContent = stats.gold;
        document.getElementById('fatigue').textContent = stats.fatigue || 0;
    } catch (error) {
        console.error('캐릭터 정보를 불러오는데 실패했습니다:', error);
    }
}

function getComputerChoice() {
    const choices = ['rock', 'paper', 'scissors'];
    return choices[Math.floor(Math.random() * choices.length)];
}

function handleBattle(playerChoice, computerChoice) {
    const playerPower = calculatePlayerPower();
    const monsterPower = calculateMonsterPower();
    const winChance = getPlayerWinChance(playerPower, monsterPower);
    
    // 피로도 체크
    const currentFatigue = parseInt(document.getElementById('fatigue').textContent);
    if (currentFatigue >= 100) {
        alert('피로도가 최대치입니다! 미니게임으로 피로도를 회복하세요.');
        return;
    }
    
    let result;
    const random = Math.random();
    
    if (playerChoice === computerChoice) {
        result = '무승부!';
    } else {
        // 전투력 차이를 반영한 승패 결정
        const isPlayerWin = random < winChance;
        
        if (isPlayerWin) {
            result = '승리!';
            handleVictory(currentMonster.grade);
            // 피로도 증가
            increaseFatigue(10);
        } else {
            result = '패배...';
            calculateDamage(false);
            // 피로도 증가 (패배시 더 많이 증가)
            increaseFatigue(15);
        }
    }
    
    alert(result);
}

function calculatePlayerPower() {
    const attack = parseInt(document.getElementById('attack').textContent);
    const defense = parseInt(document.getElementById('defense').textContent);
    return attack * 2 + defense;
}

function calculateMonsterPower() {
    return currentMonster.attack * 2 + (currentMonster.defense || 0);
}

function increaseFatigue(amount) {
    const fatigueElement = document.getElementById('fatigue');
    let currentFatigue = parseInt(fatigueElement.textContent);
    currentFatigue = Math.min(100, currentFatigue + amount);
    fatigueElement.textContent = currentFatigue;
    
    // 피로도가 높을 때 경고
    if (currentFatigue >= 80) {
        showFatigueWarning();
    }
}

function showFatigueWarning() {
    const warning = document.createElement('div');
    warning.className = 'fatigue-warning';
    warning.textContent = '피로도가 높습니다! 미니게임으로 휴식을 취하세요.';
    document.body.appendChild(warning);
    
    setTimeout(() => warning.remove(), 3000);
}

function getPlayerWinChance(playerPower, monsterPower) {
    const powerDiff = playerPower - monsterPower;
    const baseChance = 0.33; // 기본 33% 승률
    const maxBonus = 0.4; // 최대 40% 추가 승률
    
    // 전투력 차이에 따른 승률 보너스 계산
    const bonus = Math.min(maxBonus, Math.max(0, powerDiff / 100) * 0.2);
    return Math.min(0.9, baseChance + bonus); // 최대 90% 승률
}

async function loadAvailableMinigames() {
    try {
        const response = await fetch('/api/minigames');
        const data = await response.json();
        updateMinigamesUI(data);
    } catch (error) {
        console.error('미니게임 정보를 불러오는데 실패했습니다:', error);
    }
}

function updateMinigamesUI(data) {
    const minigamesContainer = document.querySelector('.minigames-container');
    minigamesContainer.innerHTML = '';
    
    Object.entries(data.games).forEach(([type, game]) => {
        const gameElement = createMinigameElement(type, game);
        minigamesContainer.appendChild(gameElement);
    });
}

function createMinigameElement(type, game) {
    const element = document.createElement('div');
    element.className = 'minigame-item';
    element.innerHTML = `
        <h3>${game.name}</h3>
        <p>필요 레벨: ${game.required_level}</p>
        <p>비용: ${game.cost} 골드</p>
        <button onclick="playMinigame('${type}')" class="minigame-btn">플레이</button>
    `;
    return element;
}

async function playMinigame(type) {
    try {
        const response = await fetch('/api/play_minigame', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ game_type: type })
        });
        
        const result = await response.json();
        if (result.success) {
            showMinigameRewards(result.rewards);
            updatePlayerStats(result);
        } else {
            alert(result.error);
        }
    } catch (error) {
        console.error('미니게임 플레이 중 오류 발생:', error);
    }
}

function showMinigameRewards(rewards) {
    const rewardsElement = document.createElement('div');
    rewardsElement.className = 'minigame-rewards';
    rewardsElement.innerHTML = `
        <h3>미니게임 보상</h3>
        <p>골드: ${rewards.gold}</p>
        <p>피로도 회복: ${rewards.fatigue_recovery}</p>
    `;
    document.body.appendChild(rewardsElement);
    
    setTimeout(() => rewardsElement.remove(), 3000);
}

function updatePlayerStats(result) {
    const goldElement = document.getElementById('gold');
    const fatigueElement = document.getElementById('fatigue');
    
    goldElement.textContent = parseInt(goldElement.textContent) + result.rewards.gold;
    fatigueElement.textContent = Math.max(0, parseInt(fatigueElement.textContent) - result.rewards.fatigue_recovery);
}

// 몬스터 등급 설정
const MONSTER_GRADES = {
    NORMAL: 'grade-normal',
    RARE: 'grade-rare',
    EPIC: 'grade-epic',
    LEGENDARY: 'grade-legendary'
};

const MAX_LEVEL = 77;
const EXP_TABLE = {
    // 레벨별 필요 경험치 (어려운 레벨링)
    getRequiredExp: (level) => {
        if (level >= MAX_LEVEL) return Infinity;
        return Math.floor(100 * Math.pow(1.5, level - 1));
    },
    
    // 몬스터 처치시 획득 경험치
    getMonsterExp: (monsterGrade, playerLevel) => {
        const baseExp = 10;
        const gradeMultiplier = {
            NORMAL: 1,
            RARE: 2.5,
            EPIC: 6,
            LEGENDARY: 15
        };
        
        // 레벨 차이에 따른 경험치 보정
        const levelDiff = monsterGrade === 'LEGENDARY' ? 0 : Math.max(0, playerLevel - 5);
        const levelPenalty = Math.max(0.1, 1 - (levelDiff * 0.1));
        
        return Math.floor(baseExp * gradeMultiplier[monsterGrade] * levelPenalty);
    }
};

// 플레이어 레벨에 따른 몬스터 등급 결정
function determineMonsterGrade(playerLevel) {
    const random = Math.random();
    
    if (playerLevel < 15) {
        return MONSTER_GRADES.NORMAL;
    } else if (playerLevel < 30) {
        if (random < 0.95) return MONSTER_GRADES.NORMAL;
        return MONSTER_GRADES.RARE;
    } else if (playerLevel < 50) {
        if (random < 0.85) return MONSTER_GRADES.NORMAL;
        if (random < 0.98) return MONSTER_GRADES.RARE;
        return MONSTER_GRADES.EPIC;
    } else {
        if (random < 0.75) return MONSTER_GRADES.NORMAL;
        if (random < 0.95) return MONSTER_GRADES.RARE;
        if (random < 0.99) return MONSTER_GRADES.EPIC;
        return MONSTER_GRADES.LEGENDARY;
    }
}

// 몬스터 생성 함수
function spawnMonster() {
    const playerLevel = parseInt(document.getElementById('level').textContent);
    const monsterElement = document.querySelector('.monster');
    
    // 이전 등급 클래스 제거
    Object.values(MONSTER_GRADES).forEach(grade => {
        monsterElement.classList.remove(grade);
    });
    
    // 새 등급 설정
    const newGrade = determineMonsterGrade(playerLevel);
    monsterElement.classList.add(newGrade);
    
    // 몬스터 능력치 설정
    const baseStats = {
        NORMAL: { hp: 50, attack: 5 },
        RARE: { hp: 100, attack: 10 },
        EPIC: { hp: 200, attack: 20 },
        LEGENDARY: { hp: 500, attack: 50 }
    };
    
    // 현재 몬스터의 능력치 저장
    currentMonster = {
        grade: newGrade.replace('grade-', '').toUpperCase(),
        ...baseStats[newGrade.replace('grade-', '').toUpperCase()]
    };
}

// 현재 몬스터 정보 반환
function getCurrentMonster() {
    return currentMonster;
}

// 전투 승리 처리
function handleVictory(monsterGrade) {
    const playerLevel = parseInt(document.getElementById('level').textContent);
    const expGain = EXP_TABLE.getMonsterExp(monsterGrade, playerLevel);
    let currentExp = parseInt(document.getElementById('exp').textContent);
    
    // 경험치 획득 및 레벨업 처리
    currentExp += expGain;
    const requiredExp = EXP_TABLE.getRequiredExp(playerLevel);
    
    if (currentExp >= requiredExp && playerLevel < MAX_LEVEL) {
        // 레벨업
        document.getElementById('level').textContent = playerLevel + 1;
        currentExp -= requiredExp;
        
        // 레벨업 효과
        showLevelUpEffect();
        
        // 능력치 증가
        increaseStats(playerLevel + 1);
    }
    
    document.getElementById('exp').textContent = currentExp;
    
    // 아이템 드롭 처리
    if (Math.random() < getDropRate(monsterGrade)) {
        dropItem(monsterGrade, playerLevel);
    }
}

// 레벨업 효과
function showLevelUpEffect() {
    const levelText = document.createElement('div');
    levelText.className = 'level-up-effect';
    levelText.textContent = 'LEVEL UP!';
    document.querySelector('.player-character').appendChild(levelText);
    
    setTimeout(() => levelText.remove(), 2000);
}

// 아이템 드롭 확률
function getDropRate(monsterGrade) {
    const baseRate = {
        NORMAL: 0.05,
        RARE: 0.15,
        EPIC: 0.35,
        LEGENDARY: 1
    };
    return baseRate[monsterGrade];
}

// 아이템 드롭
function dropItem(monsterGrade, playerLevel) {
    // 아이템 드롭 로직 구현 필요
    alert('아이템을 드롭했습니다!');
}

// 능력치 증가
function increaseStats(playerLevel) {
    // 능력치 증가 로직 구현 필요
    alert('능력치를 증가시켰습니다!');
}

function calculateDamage(playerWon) {
    const attack = parseInt(document.getElementById('attack').textContent);
    const defense = parseInt(document.getElementById('defense').textContent);
    
    if (playerWon) {
        // 크리티컬 확률 (10%)
        const isCritical = Math.random() < 0.1;
        let damage = attack;
        
        if (isCritical) {
            damage *= 2;
            alert('크리티컬 히트!');
        }
        
        // 몬스터에게 데미지 적용
        const currentMonster = getCurrentMonster();
        currentMonster.hp -= damage;
        
        if (currentMonster.hp <= 0) {
            // 몬스터 처치
            alert('몬스터를 처치했습니다!');
            spawnMonster();
        }
    } else {
        // 플레이어가 데미지를 받음
        const playerHp = parseInt(document.getElementById('hp').textContent);
        const damage = Math.max(5, 10 - defense); // 최소 데미지 5
        
        document.getElementById('hp').textContent = Math.max(0, playerHp - damage);
    }
}

let currentMonster;
