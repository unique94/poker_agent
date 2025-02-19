from datetime import datetime

class PokerService:
    def __init__(self):
        self.current_game = None
        self.isNewHand = True
        self.positions = []
        self.action_history = []  # 添加行动历史存储

    def setup_game(self, players):
        """
        设置新的游戏
        """
        try:
            # 验证玩家数据
            self._validate_players(players)
            
            # 处理玩家数据
            processed_players = self._process_players(players)
            
            # 创建新游戏
            self.current_game = {
                'players': processed_players,
                'pot': 0,
                'current_round': 'preflop',
                # 其他游戏状态...
            }
            
            return self.current_game
            
        except Exception as e:
            raise Exception(f"设置游戏失败: {str(e)}")

    def _validate_players(self, players):
        """
        验证玩家数据
        """
        if not players:
            raise ValueError("没有玩家数据")
        
        # 验证玩家数量
        if not (2 <= len(players) <= 9):
            raise ValueError("玩家数量必须在2-9之间")
        
        # 验证庄家
        dealer_count = sum(1 for p in players if p.get('isDealer'))
        if dealer_count != 1:
            raise ValueError("必须且只能有一个庄家")

    def _process_players(self, players):
        """
        处理玩家数据
        """
        processed = []
        for player in players:
            processed_player = {
                'name': player['name'],
                'chips': player['chips'],
                'position': player['position'],
                'is_dealer': player['isDealer'],
                'action': player['action'],
                'status': player['status'],
                'bets': player['bets'],
                'hole_cards': player['holeCards'] if player['position'] == 1 else None,
                'total_bet': sum(player['bets'].values()),
                'in_hand': player['status'] == 'active',
                'action_history': player.get('actionHistory', [])
            }
            processed.append(processed_player)
        
        return processed

    @staticmethod
    def validate_table_setup(players):
        """验证牌桌设置"""
        if not 2 <= len(players) <= 9:
            raise ValueError("牌桌人数必须在2-9人之间")
        
        for player in players:
            if player['chips'] <= 0:
                raise ValueError(f"玩家 {player['name']} 的筹码必须大于0")
            if not player['name'].strip():
                raise ValueError("玩家名称不能为空")
        
        return True

    @staticmethod
    def initialize_table(players):
        """初始化牌桌"""
        return {
            'players': players,
            'total_players': len(players),
            'total_chips': sum(player['chips'] for player in players)
        }

    def get_advice(self, players, cards):
        """
        根据玩家信息和牌面信息生成策略建议
        """
        try:
            # 分析当前阶段
            stage = self._get_current_stage(cards)
            
            # 生成完整的场景描述
            prompt = self._get_bet_prompt(players, cards, stage)
            
            # 打印详细信息用于调试
            print("\n" + "="*50)
            print("德州扑克策略分析")
            print("="*50)
            print("\n【生成的 Prompt】")
            print("-"*50)
            print(prompt)
            
            # 返回结果
            data = {
                'prompt': prompt
            }
            
            return data
            
        except Exception as e:
            print(f"\n错误: 生成建议时出错 - {str(e)}")
            raise Exception(f"生成建议时出错: {str(e)}")
    
    def _get_position(self, players):
        """
        确定主玩家的位置
        
        位置顺序从庄家按逆时针方向：BTN -> SB -> BB -> UTG -> UTG+1 -> MP -> HJ -> CO
        """
        player_count = len(players)
        # 获取该玩家数量下的位置列表
        positions = self._get_position_names(player_count)
        
        dealer_index = next((i for i, p in enumerate(players) if p['isDealer']), -1)
        
        # 根据庄家位置重新排列位置名称
        # 将位置列表旋转，使庄家位置（BTN）对应dealer_index
        rotated_positions = positions[len(players)-dealer_index:] + positions[:len(players)-dealer_index]
        
        # 返回每个玩家对应的位置
        return rotated_positions

    def _get_position_names(self, player_count):
        """
        根据玩家数量返回位置名称列表
        从庄家位置(BTN)开始逆时针排列
        
        2人桌：BTN/SB, BB
        3人桌：BTN, SB, BB
        4人桌：BTN, SB, BB, UTG
        5人桌：BTN, SB, BB, UTG, CO
        6人桌：BTN, SB, BB, UTG, HJ, CO
        7人桌：BTN, SB, BB, UTG, MP, HJ, CO
        8人桌：BTN, SB, BB, UTG, UTG+1, MP, HJ, CO
        9人桌：BTN, SB, BB, UTG, UTG+1, UTG+2, MP, HJ, CO
        """
        if player_count < 3 or player_count > 9:
            return []

        if player_count == 3:
            positions = ['BTN', 'SB', 'BB']
        elif player_count == 4:
            positions = ['BTN', 'SB', 'BB', 'UTG']
        elif player_count == 5:
            positions = ['BTN', 'SB', 'BB', 'UTG', 'CO']
        elif player_count == 6:
            positions = ['BTN', 'SB', 'BB', 'UTG', 'HJ', 'CO']
        elif player_count == 7:
            positions = ['BTN', 'SB', 'BB', 'UTG', 'MP', 'HJ', 'CO']
        elif player_count == 8:
            positions = ['BTN', 'SB', 'BB', 'UTG', 'UTG+1', 'MP', 'HJ', 'CO']
        elif player_count == 9:
            positions = ['BTN', 'SB', 'BB', 'UTG', 'UTG+1', 'UTG+2', 'MP', 'HJ', 'CO']
        
        # 确保返回的位置数量与玩家数量相匹配
        return positions
    
    def _get_current_stage(self, cards):
        """确定当前游戏阶段"""
        if not any(cards['flop']):
            return 'preflop'
        elif not cards['turn']:
            return 'flop'
        elif not cards['river']:
            return 'turn'
        return 'river'

    def _get_bet_prompt(self, players, cards, stage):
        """
        生成用于大模型的 prompt，描述当前游戏场景
        
        Args:
            players (list): 玩家信息列表
            cards (dict): 公共牌信息
            stage (str): 当前游戏阶段
        
        Returns:
            str: 格式化的场景描述
        """
        try:
            # 获取主要信息
            player_count = len(players)
            main_player = players[0]
            positions = self._get_position(players)
            
            # 构建场景描述
            if (self.isNewHand):
                prompt = f"""在一个{player_count}人的德州扑克现金局中：

1. 基本信息：
- 你的位置：{positions[0]}
- 你的筹码：{main_player['chips']}
- 你的底牌：{main_player['holeCards']['card1']} {main_player['holeCards']['card2']}

2. 其他玩家信息："""

            # 添加其他玩家信息
            for i, player in enumerate(players[1:], 1):
                prompt += f"""
- 玩家：{player['name']}
  筹码：{player['chips']}
  位置：{positions[i]}"""

            # 添加公共牌信息
            prompt += "\n\n3. 当前牌面信息："
            if stage == 'preflop':
                prompt += "\n现在是翻前下注"
            else:
                if cards['flop']:
                    flop_cards = ' '.join(cards['flop'])
                    prompt += f"\n翻牌：{flop_cards}"
                if cards['turn']:
                    prompt += f"\n转牌：{cards['turn']}"
                if cards['river']:
                    prompt += f"\n河牌：{cards['river']}"
            
            print(players)
            # 添加玩家行动信息
            prompt += "\n\n4. 玩家行动信息："
            for i, player in enumerate(players):
                prompt += f"\n- 玩家：{player['name']}"
                prompt += f"\n  行动：{player['bets']}"

            prompt += "\n\n5. 现在行动到我，我应该怎么做？"

            # 添加提问
            if (self.isNewHand):
                prompt += """

请根据以上信息，给出详细的策略建议，包括：
1. 这手牌在当前位置的打法建议
2. 考虑其他玩家的筹码深度，建议的加注尺度
3. 需要注意的关键点
4. 如果遇到加注或反加注，应该如何应对"""

            self.isNewHand = False
            return prompt

        except Exception as e:
            raise Exception(f"生成 prompt 时出错: {str(e)}") 

    def reset_game(self):
        """
        重置游戏状态
        """
        self.isNewHand = True
        self.current_game = None
        self.action_history = [] 