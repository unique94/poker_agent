// 这里可以添加您的 JavaScript 代码
console.log('Website loaded successfully!'); 

async function calculateBMI() {
    const weight = document.getElementById('weight').value;
    const height = document.getElementById('height').value;

    if (!weight || !height) {
        alert('请输入体重和身高');
        return;
    }

    try {
        const response = await fetch('/calculate-bmi', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ weight, height })
        });

        const result = await response.json();
        
        if (result.success) {
            document.getElementById('result').style.display = 'block';
            document.getElementById('bmi-value').textContent = result.data.bmi;
            document.getElementById('bmi-category').textContent = result.data.category;
        } else {
            alert('计算失败：' + result.error);
        }
    } catch (error) {
        alert('发生错误：' + error.message);
    }
} 

function updatePlayerInputs() {
    const playerCount = parseInt(document.getElementById('playerCount').value);
    const playerInputs = document.getElementById('playerInputs');
    playerInputs.innerHTML = '';

    for (let i = 0; i < playerCount; i++) {
        const playerCard = document.createElement('div');
        playerCard.className = 'player-input-card';
        
        // 为玩家1添加底牌选择
        const holeCardsHtml = i === 0 ? `
            <div class="hole-cards-group">
                <label>底牌</label>
                <div class="hole-cards-inputs">
                    <input type="text" class="card-input hole-card" id="player${i}card1" maxlength="2" readonly>
                    <input type="text" class="card-input hole-card" id="player${i}card2" maxlength="2" readonly>
                </div>
            </div>
        ` : '';

        playerCard.innerHTML = `
            <div class="player-input-row">
                <div class="player-number">${i + 1}</div>
                <div class="form-group-small">
                    <input type="text" id="player${i}name" placeholder="玩家" required>
                </div>
                <div class="form-group-small">
                    <input type="number" id="player${i}chips" placeholder="筹码" min="1" required>
                </div>
                <div class="dealer-checkbox">
                    <input type="checkbox" id="player${i}dealer" class="is-dealer" name="dealer" onchange="handleDealerChange(${i})">
                    <label for="player${i}dealer">庄</label>
                </div>
                <div class="bet-input-group">
                    <label>翻前</label>
                    <input type="text" id="player${i}preflop" placeholder="动作">
                </div>
                <div class="bet-input-group">
                    <label>翻牌</label>
                    <input type="text" id="player${i}flop" placeholder="动作">
                </div>
                <div class="bet-input-group">
                    <label>转牌</label>
                    <input type="text" id="player${i}turn" placeholder="动作">
                </div>
                <div class="bet-input-group">
                    <label>河牌</label>
                    <input type="text" id="player${i}river" placeholder="动作">
                </div>
                ${holeCardsHtml}
            </div>
        `;
        playerInputs.appendChild(playerCard);
    }
    
    // 在更新完玩家输入后重新初始化卡牌输入框
    setTimeout(initializeCardInputs, 0);
}

// 添加处理庄家选择的函数
function handleDealerChange(selectedIndex) {
    const checkboxes = document.querySelectorAll('.is-dealer');
    checkboxes.forEach((checkbox, index) => {
        if (index !== selectedIndex) {
            checkbox.checked = false;
        }
    });
}

async function setupTable() {
    const playerCount = parseInt(document.getElementById('playerCount').value);
    const players = [];

    // 收集玩家信息
    for (let i = 0; i < playerCount; i++) {
        const name = document.getElementById(`player${i}name`).value;
        const chips = parseInt(document.getElementById(`player${i}chips`).value);
        const isDealer = document.getElementById(`player${i}dealer`).checked;
        const bets = {
            preflop: document.getElementById(`player${i}preflop`).value || '',
            flop: document.getElementById(`player${i}flop`).value || '',
            turn: document.getElementById(`player${i}turn`).value || '',
            river: document.getElementById(`player${i}river`).value || ''
        };
        
        const holeCards = i === 0 ? {
            card1: document.getElementById(`player${i}card1`).value,
            card2: document.getElementById(`player${i}card2`).value
        } : null;
        
        players.push({
            name: name,
            chips: chips,
            position: i + 1,
            isDealer: isDealer,
            bets: bets,
            holeCards: holeCards
        });
    }

    // 存储当前牌桌信息
    currentTableInfo = {
        players: players
    };

    try {
        const response = await fetch('/setup-table', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ players })
        });

        const result = await response.json();
        
        if (result.success) {
            // 不再调用 displayTable，而是简单地显示成功消息
            alert('牌桌设置成功！');
            
            // 禁用所有输入框，表示游戏已开始
            players.forEach((_, index) => {
                document.getElementById(`player${index}name`).readOnly = true;
                document.getElementById(`player${index}chips`).readOnly = true;
                document.getElementById(`player${index}dealer`).disabled = true;
                document.getElementById(`player${index}preflop`).readOnly = true;
                document.getElementById(`player${index}flop`).readOnly = true;
                document.getElementById(`player${index}turn`).readOnly = true;
                document.getElementById(`player${index}river`).readOnly = true;
                
                if (index === 0 && document.getElementById(`player${index}card1`)) {
                    document.getElementById(`player${index}card1`).readOnly = true;
                    document.getElementById(`player${index}card2`).readOnly = true;
                }
            });
            
            // 禁用玩家数量选择和开始游戏按钮
            document.getElementById('playerCount').disabled = true;
            document.querySelector('.start-button').disabled = true;
            
            // 显示右侧面板
            document.querySelector('.right-panel').style.display = 'block';
        } else {
            alert('设置失败：' + result.error);
        }
    } catch (error) {
        alert('发生错误：' + error.message);
    }
}

function displayTable(tableInfo) {
    // 更新为使用正确的选择器
    const pokerSimulator = document.querySelector('.poker-simulator');
    const playerInputs = document.getElementById('playerInputs');
    
    // 保持玩家控制面板可见
    document.querySelector('.player-controls').style.display = 'block';
    
    // 更新玩家显示，保持原有布局
    playerInputs.innerHTML = tableInfo.players.map((player, index) => `
        <div class="player-input">
            <div class="player-info">
                <div class="player-name">${player.name}</div>
                <div class="player-chips">${player.chips} 筹码</div>
                ${player.isDealer ? '<div class="dealer-badge">庄家</div>' : ''}
            </div>
            ${index === 0 ? `
            <div class="player-cards">
                <input type="text" class="card-input" value="${player.holeCards?.card1 || ''}" readonly>
                <input type="text" class="card-input" value="${player.holeCards?.card2 || ''}" readonly>
            </div>
            ` : ''}
        </div>
    `).join('');
    
    // 确保中心面板和右侧面板保持可见
    document.querySelector('.center-panel').style.display = 'block';
    document.querySelector('.right-panel').style.display = 'block';
}

// 页面加载时初始化
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('playerCount').value = 6;
    updatePlayerInputs();
    initializeCardInputs();
    initializeCardPicker();
});

function getCardValues() {
    const cards = {
        flop: [],
        turn: '',
        river: ''
    };
    
    // 收集 Flop 牌
    const flopInputs = document.querySelectorAll('.card-group:nth-child(1) .card-input');
    flopInputs.forEach(input => {
        cards.flop.push(input.value);
    });
    
    // 收集 Turn 牌
    cards.turn = document.querySelector('.card-group:nth-child(2) .card-input').value;
    
    // 收集 River 牌
    cards.river = document.querySelector('.card-group:nth-child(3) .card-input').value;
    
    return cards;
}

// 修改请求建议的函数
async function requestAdvice() {
    const playerCount = parseInt(document.getElementById('playerCount').value);
    const players = [];

    // 收集玩家信息
    for (let i = 0; i < playerCount; i++) {
        const name = document.getElementById(`player${i}name`).value;
        const chips = parseInt(document.getElementById(`player${i}chips`).value);
        const isDealer = document.getElementById(`player${i}dealer`).checked;
        const bets = {
            preflop: document.getElementById(`player${i}preflop`).value || '',
            flop: document.getElementById(`player${i}flop`).value || '',
            turn: document.getElementById(`player${i}turn`).value || '',
            river: document.getElementById(`player${i}river`).value || ''
        };
        
        const holeCards = i === 0 ? {
            card1: document.getElementById(`player${i}card1`).value,
            card2: document.getElementById(`player${i}card2`).value
        } : null;
        
        players.push({
            name: name,
            chips: chips,
            position: i + 1,
            isDealer: isDealer,
            bets: bets,
            holeCards: holeCards
        });
    }

    // 获取公共牌信息
    const cards = getCardValues();
    
    // 验证必要信息
    if (!validateGameInfo(players, cards)) {
        return;
    }

    const requestData = {
        players: players,
        cards: cards
    };
    
    // 添加这行来查看发送的数据
    console.log('Sending data to backend:', requestData);

    try {
        const response = await fetch('/get-advice', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });

        const result = await response.json();
        
        if (result.success) {
            console.log('Received advice data:', result.data);
            displayAdvice(result.data);
        } else {
            alert('获取建议失败：' + result.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('发生错误：' + error.message);
    }
}

// 添加验证函数
function validateGameInfo(players, cards) {
    // 验证第一个玩家（主玩家）信息
    const mainPlayer = players[0];
    if (!mainPlayer.name) {
        alert('请输入主玩家名称');
        return false;
    }
    if (!mainPlayer.chips) {
        alert('请输入主玩家筹码');
        return false;
    }
    if (!mainPlayer.holeCards.card1 || !mainPlayer.holeCards.card2) {
        alert('请选择主玩家底牌');
        return false;
    }

    // 验证庄家是否选择
    const hasDealer = players.some(p => p.isDealer);
    if (!hasDealer) {
        alert('请选择一个庄家');
        return false;
    }

    // 验证其他玩家基本信息
    for (let i = 1; i < players.length; i++) {
        if (!players[i].name || !players[i].chips) {
            alert(`请完善玩家 ${i + 1} 的基本信息`);
            return false;
        }
    }

    return true;
}

function displayAdvice(adviceData) {
    const adviceContent = document.getElementById('adviceContent');
    const placeholder = adviceContent.querySelector('.advice-placeholder');
    const resultDiv = adviceContent.querySelector('.advice-result');
    
    console.log('Displaying advice:', adviceData);
    
    if (!adviceData || !adviceData.prompt) {
        // 显示错误信息
        placeholder.style.display = 'block';
        resultDiv.style.display = 'none';
        placeholder.innerHTML = '<p class="error-message">无法获取建议</p>';
        return;
    }
    
    // 隐藏占位符，显示结果
    placeholder.style.display = 'none';
    resultDiv.style.display = 'block';
    
    // 直接显示完整的建议内容
    resultDiv.querySelector('.scene-analysis').textContent = adviceData.prompt;
    
    // 滚动到建议区域
    adviceContent.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// 存储当前牌桌信息的变量
let currentTableInfo = null; 

// 添加卡牌输入验证
document.querySelectorAll('.card-input').forEach(input => {
    input.addEventListener('input', function(e) {
        // 转换为大写
        this.value = this.value.toUpperCase();
        
        // 验证输入格式
        if (this.value.length === 2) {
            const suit = this.value[0];
            const rank = this.value[1];
            
            // 验证花色和点数
            const validSuits = ['♠', '♥', '♣', '♦', 'S', 'H', 'C', 'D'];
            const validRanks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A'];
            
            if (!validSuits.includes(suit) || !validRanks.includes(rank)) {
                this.value = '';
                alert('请输入有效的扑克牌（如：♠A, ♥K, ♣Q）');
            }
        }
    });
}); 

// 更新卡牌选择器相关代码
let currentInput = null;
let selectedSuit = null;
const modal = document.getElementById('cardPickerModal');

// 初始化卡牌选择器
function initializeCardPicker() {
    // 花色按钮点击事件
    document.querySelectorAll('.suit-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            document.querySelectorAll('.suit-btn.selected')
                .forEach(b => b.classList.remove('selected'));
            this.classList.add('selected');
            selectedSuit = this.dataset.suit;
        });
    });

    // 点数按钮点击事件
    document.querySelectorAll('.rank-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            if (!selectedSuit) {
                alert('请先选择花色');
                return;
            }
            
            if (currentInput) {
                currentInput.value = selectedSuit + this.dataset.rank;
                modal.style.display = 'none';
                currentInput = null;
                selectedSuit = null;
            }
        });
    });

    // 点击其他地方关闭弹出框
    document.addEventListener('click', function(e) {
        if (!modal.contains(e.target) && !e.target.classList.contains('card-input')) {
            modal.style.display = 'none';
            currentInput = null;
            selectedSuit = null;
        }
    });
}

// 初始化卡牌输入框
function initializeCardInputs() {
    document.querySelectorAll('.card-input').forEach(input => {
        // 移除可能存在的旧事件监听器
        input.replaceWith(input.cloneNode(true));
    });
    
    // 重新添加事件监听器
    document.querySelectorAll('.card-input').forEach(input => {
        input.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            currentInput = this;
            
            // 计算弹出框位置
            const rect = this.getBoundingClientRect();
            const modalRect = modal.getBoundingClientRect();
            
            // 确保模态框不会超出视窗
            let left = rect.left;
            let top = rect.bottom + 5;
            
            // 检查右边界
            if (left + modalRect.width > window.innerWidth) {
                left = window.innerWidth - modalRect.width - 10;
            }
            
            // 检查下边界
            if (top + modalRect.height > window.innerHeight) {
                top = rect.top - modalRect.height - 5;
            }
            
            modal.style.left = left + 'px';
            modal.style.top = top + 'px';
            modal.style.display = 'block';
            
            // 重置选中状态
            selectedSuit = null;
            document.querySelectorAll('.suit-btn.selected, .rank-btn.selected')
                .forEach(btn => btn.classList.remove('selected'));
        });
    });
}

async function resetGame() {
    try {
        const response = await fetch('/reset-game', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        const result = await response.json();
        
        if (result.success) {
            // 清空所有行动输入
            const playerCount = parseInt(document.getElementById('playerCount').value);
            for (let i = 0; i < playerCount; i++) {
                // 保持玩家基本信息（名字、筹码、庄家位置）
                document.getElementById(`player${i}preflop`).value = '';
                document.getElementById(`player${i}flop`).value = '';
                document.getElementById(`player${i}turn`).value = '';
                document.getElementById(`player${i}river`).value = '';
            }
            
            // 清空公共牌
            document.querySelectorAll('.community-cards .card-input').forEach(input => {
                input.value = '';
            });
            
            // 清空主玩家的底牌
            if (document.getElementById('player0card1')) {
                document.getElementById('player0card1').value = '';
                document.getElementById('player0card2').value = '';
            }
            
            // 清空建议内容
            const adviceContent = document.getElementById('adviceContent');
            if (adviceContent) {
                const placeholder = adviceContent.querySelector('.advice-placeholder');
                const resultDiv = adviceContent.querySelector('.advice-result');
                
                if (placeholder) {
                    placeholder.style.display = 'block';
                }
                if (resultDiv) {
                    resultDiv.style.display = 'none';
                }
            }
            
            alert('新的一手已开始！');
        } else {
            alert('重置失败：' + result.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('发生错误：' + error.message);
    }
} 