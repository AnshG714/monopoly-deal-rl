from mcts.consts import DEFAULT_ITERS
from mcts.node import ISMCTSNode
from mcts.determinize import determinize
from models.game.game import Game, GameCommand
from rollout import rollout


class ISMCTSSolver:
    def __init__(self, iterations: int = DEFAULT_ITERS):
        self.iterations = iterations

    def search(self, game: Game) -> GameCommand:
        root_player_idx = game.acting_player_idx
        root_node = ISMCTSNode()

        for _ in range(self.iterations):
            # 1. Determinize the game for the root player.
            determinized_game = determinize(game)
            node = root_node

            unexpanded_moves = []

            # 2. Select a node to expand via UCT.
            while not determinized_game.is_over():

                unexpanded_moves = node.get_unexpanded_moves(
                    determinized_game.legal_moves()
                )

                if unexpanded_moves:
                    break

                node = node.choose_child_uct(determinized_game.legal_moves())
                determinized_game.apply(node.move)

            # 3. Expand the node.
            if not determinized_game.is_over() and len(unexpanded_moves) > 0:
                # Select an action at random.
                move = determinized_game._rng.choice(unexpanded_moves)
                determinized_game.apply(move)
                new_node = ISMCTSNode(move, node)
                node.children.append(new_node)

                node = new_node

            # 4. Simulate from the expanded node.
            simulation_result = rollout(determinized_game)
            reward = 1 if simulation_result["winner"] == root_player_idx else 0

            # 5. Backpropagate the result.
            node.backpropagate(reward)

        return root_node.best_child().move
