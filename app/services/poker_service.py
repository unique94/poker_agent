class PokerService:
    def __init__(self):
        self.current_game = None
        self.positions = ['BB', 'SB', 'BTN', 'CO', 'HJ', 'UTG']

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
                'in_hand': player['status'] == 'active'
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
            # 获取主玩家（第一个玩家）信息
            main_player = players[0]
            hole_cards = main_player['holeCards']
            
            # 确定玩家位置
            position = self._get_position(players)
            
            # 分析当前阶段
            stage = self._get_current_stage(cards)
            
            # 生成建议
            position_advice = self._get_position_advice(position, len(players))
            action_advice = self._get_action_advice(position, hole_cards, cards, stage)
            bet_advice = self._get_bet_advice(position, main_player['chips'], players)
            
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
        dealer_index = next((i for i, p in enumerate(players) if p['isDealer']), -1)
        player_count = len(players)
        
        if dealer_index == -1:
            return "未知位置"
        
        # 获取该玩家数量下的位置列表
        positions = self._get_position_names(player_count)
        
        # 计算主玩家（索引0）相对于庄家的位置
        # 需要反向计算，因为位置是逆时针方向
        relative_pos = (0 - dealer_index) % player_count
        
        # 庄家位置是BTN，从那里开始数
        position_index = relative_pos
        if position_index < len(positions):
            return positions[position_index]
        return "未知位置"

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
        if player_count < 2 or player_count > 9:
            return []
        
        if player_count == 2:
            return ['BTN/SB', 'BB']
        
        # 基础位置
        positions = ['BTN', 'SB', 'BB']
        
        # 根据玩家数量添加其他位置
        if player_count > 3:
            positions.extend(['UTG'])
        if player_count > 4:
            positions.extend(['CO'])
        if player_count > 5:
            positions.extend(['HJ'])
        if player_count > 6:
            positions.extend(['MP'])
        if player_count > 7:
            positions.extend(['UTG+1'])
        if player_count > 8:
            positions.extend(['UTG+2'])
        
        # 确保返回的位置数量与玩家数量相匹配
        return positions[:player_count]
    
    def _get_current_stage(self, cards):
        """确定当前游戏阶段"""
        if not any(cards['flop']):
            return 'preflop'
        elif not cards['turn']:
            return 'flop'
        elif not cards['river']:
            return 'turn'
        return 'river'
    
    def _get_position_advice(self, position, player_count):
        """根据位置生成建议"""
        position_advice = {
            'BTN': '你在庄家位置，这是最有利的位置。你可以打更宽的范围，因为你在除大小盲以外的所有玩家之后行动。',
            'CO': '你在枪口位置，这是第二好的位置。你可以打比较宽的范围。',
            'HJ': '你在劫机位，需要比枪口位置更谨慎一些。',
            'MP': '你在中间位置，建议打比较紧的范围。',
            'UTG': '你在最早位置，需要打最紧的范围。',
            'UTG+1': '你在早位，需要打比较紧的范围。',
            'SB': '你在小盲位置，需要特别注意位置不利。',
            'BB': '你在大盲位置，已经投入了盲注，可以用更宽的范围防守。'
        }
        
        return position_advice.get(position, '未知位置')
    
    def _get_action_advice(self, position, hole_cards, cards, stage):
        """根据位置、手牌和当前阶段生成行动建议"""
        if stage == 'preflop':
            return self._get_preflop_advice(position, hole_cards)
        else:
            return self._get_postflop_advice(stage, hole_cards, cards)
    
    def _get_preflop_advice(self, position, hole_cards):
        """生成翻前建议"""
        if not hole_cards or not hole_cards['card1'] or not hole_cards['card2']:
            return "请先选择底牌"
            
        # 这里可以添加更复杂的翻前范围分析
        card1, card2 = hole_cards['card1'], hole_cards['card2']
        
        # 简单的示例逻辑
        if card1[1] == card2[1]:  # 对子
            return f"你有一对{card1[1]}，在{position}位置可以考虑加注。"
        elif card1[1] in 'AK' and card2[1] in 'AK':  # AK
            return f"你有{card1[1]}{card2[1]}，这是一手很强的牌，可以考虑加注。"
        else:
            return f"在{position}位置，这手牌需要谨慎行动。"
    
    def _get_postflop_advice(self, stage, hole_cards, cards):
        """生成翻后建议"""
        stage_names = {
            'flop': '翻牌',
            'turn': '转牌',
            'river': '河牌'
        }
        
        return f"在{stage_names[stage]}圈，需要根据公共牌和对手行动来决定策略。"
    
    def _get_bet_advice(self, position, chips, players):
        """生成下注建议"""
        # 计算底池大小
        pot = sum(sum(p['bets'].values()) for p in players)
        
        if pot == 0:
            return "标准加注尺度是2.5-3个大盲。"
        else:
            return f"当前底池{pot}，标准续注尺度是底池的1/2到2/3。"

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
            position = self._get_position(players)
            
            # 构建场景描述
            prompt = f"""在一个{player_count}人的德州扑克现金局中：

1. 基本信息：
- 你的位置：{position}
- 你的筹码：{main_player['chips']}
- 你的底牌：{main_player['holeCards']['card1']} {main_player['holeCards']['card2']}

2. 其他玩家信息："""

            # 添加其他玩家信息
            for i, player in enumerate(players[1:], 1):
                prompt += f"""
- 玩家{i}：{player['name']}
  筹码：{player['chips']}
  位置：{self._get_position([player])}
  {'是庄家' if player['isDealer'] else ''}"""

            # 添加公共牌信息
            prompt += "\n\n3. 牌面信息："
            if stage == 'preflop':
                prompt += "\n当前在翻前"
            else:
                if cards['flop']:
                    flop_cards = ' '.join(cards['flop'])
                    prompt += f"\n翻牌：{flop_cards}"
                if cards['turn']:
                    prompt += f"\n转牌：{cards['turn']}"
                if cards['river']:
                    prompt += f"\n河牌：{cards['river']}"

            # 添加行动信息
            prompt += "\n\n4. 行动信息："
            for i, player in enumerate(players):
                bets = player['bets']
                actions = []
                if bets['preflop'] > 0:
                    actions.append(f"翻前投注{bets['preflop']}")
                if bets['flop'] > 0:
                    actions.append(f"翻牌圈投注{bets['flop']}")
                if bets['turn'] > 0:
                    actions.append(f"转牌圈投注{bets['turn']}")
                if bets['river'] > 0:
                    actions.append(f"河牌圈投注{bets['river']}")
                
                player_name = "你" if i == 0 else player['name']
                if actions:
                    prompt += f"\n- {player_name}：" + "，".join(actions)

            # 添加底池信息
            total_pot = sum(sum(p['bets'].values()) for p in players)
            prompt += f"\n\n5. 当前底池：{total_pot}"

            # 添加提问
            prompt += """

请根据以上信息，给出详细的策略建议，包括：
1. 这手牌在当前位置的打法建议
2. 考虑其他玩家的筹码深度，建议的加注尺度
3. 需要注意的关键点
4. 如果遇到加注或反加注，应该如何应对"""

            return prompt

        except Exception as e:
            raise Exception(f"生成 prompt 时出错: {str(e)}") 