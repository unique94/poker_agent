from flask import render_template, request, jsonify
from app import db
from app.services.poker_service import PokerService

poker_service = PokerService()

def init_app(app):
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/calculate-bmi', methods=['POST'])
    def calculate_bmi():
        try:
            data = request.get_json()
            weight = float(data['weight'])
            height = float(data['height'])
            
            calculator = CalculatorService()
            result = calculator.calculate_bmi(weight, height)
            
            return jsonify({
                'success': True,
                'data': result
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400
    
    @app.route('/setup-table', methods=['POST'])
    def setup_table():
        try:
            # 获取前端发送的数据
            data = request.get_json()
            players = data.get('players', [])

            # 打印接收到的数据，用于调试
            print("Received players data:", players)
            
            # 示例：处理第一个玩家（你自己）的数据
            if players and len(players) > 0:
                player1 = players[0]
                print("Player 1 info:")
                print(f"Name: {player1['name']}")
                print(f"Chips: {player1['chips']}")
                print(f"Position: {player1['position']}")
                print(f"Is Dealer: {player1['isDealer']}")
                print(f"Bets: {player1['bets']}")
                print(f"Hole Cards: {player1['holeCards']}")

            # 这里可以添加你的业务逻辑
            # poker_service = PokerService()
            # result = poker_service.setup_game(players)

            # 返回成功响应
            return jsonify({
                'success': True,
                'data': {
                    'players': players,
                    # 可以在这里添加更多返回数据
                }
            })

        except Exception as e:
            # 返回错误响应
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400
    
    @app.route('/get-advice', methods=['POST'])
    def get_advice():
        try:
            data = request.get_json()
            players = data.get('players', [])
            cards = data.get('cards', {})
            
            # 创建 PokerService 实例并获取建议
            poker_service = PokerService()
            advice = poker_service.get_advice(players, cards)
            
            return jsonify({
                'success': True,
                'data': advice
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400
    
    @app.route('/reset-game', methods=['POST'])
    def reset_game():
        """重置游戏状态的路由"""
        try:
            poker_service.reset_game()
            return jsonify({
                'success': True,
                'message': '游戏已重置'
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400 